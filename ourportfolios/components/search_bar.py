import reflex as rx
import pandas as pd
import time
import sqlite3
import itertools
from typing import List, Dict, Any

from .graph import pct_change_badge


class SearchBarState(rx.State):
    search_query: str = ""
    display_suggestion: bool = False
    recent_tickers: List[str] = []

    @rx.event
    def set_query(self, text: str = ""):
        self.search_query = text

    @rx.event
    def set_display_suggestions(self, mode: bool):
        yield time.sleep(0.2)  # Delay the set action
        self.display_suggestion = mode
        
    @rx.event
    def add_ticker_to_history(self, ticker: str):
        if not ticker in self.recent_tickers:
            self.recent_tickers.append(ticker)

    @rx.var
    def get_suggest_ticker(self) -> List[Dict[str, Any]]:
        """Recommends tickers on user's type"""
        if not self.display_suggestion:
            return []

        # At first, try to fetch exact ticker
        match_conditions = "ticker LIKE ?"
        result: pd.DataFrame = self.fetch_ticker(
            match_conditions=match_conditions, params=(f"{self.search_query}%",))

        # In-case of mistype or no ticker returned, calculate all possible permutation of provided search_query with fixed length
        if result.empty:
            # All possible combination of ticker's letter
            combos = list(itertools.permutations(
                list(self.search_query), len(self.search_query)))
            all_combination = [f"{''.join(combo)}%" for combo in combos]

            match_conditions = " OR ".join(["ticker LIKE ?"] * len(combos))
            result: pd.DataFrame = self.fetch_ticker(
                match_conditions=match_conditions, params=all_combination)

        # Suggest base of the first letter if still no ticker matched
        if result.empty:
            result: pd.DataFrame = self.fetch_ticker(
                match_conditions="ticker LIKE ?", params=(f"{self.search_query[0]}%",))

        return result.to_dict('records')

    def fetch_ticker(self, match_conditions: str, params: Any) -> pd.DataFrame:
        conn = sqlite3.connect("ourportfolios/data/data_vni.db")
        query: str = f"""
                        SELECT ticker, pct_price_change, industry
                        FROM data_vni 
                        WHERE {match_conditions}
                        ORDER BY current_price DESC
                    """
        result: pd.DataFrame = pd.read_sql(query, conn, params=params)
        conn.close()
        return result

    @rx.var
    def get_recent_ticker(self) -> List[Dict[str, Any]]:
        """Yields recently visited tickers"""
        if not self.display_suggestion:
            return []

        conn = sqlite3.connect("ourportfolios/data/data_vni.db")
        placeholders = ', '.join(['?'] * len(self.recent_tickers))
        query = f"""
                    SELECT ticker, organ_name, pct_price_change, industry
                    FROM data_vni 
                    WHERE ticker 
                    IN ({placeholders})
                """
        df: pd.DataFrame = pd.read_sql(query, conn, params=self.recent_tickers)
        return df.to_dict('records')


def search_bar():
    return rx.box(
        rx.vstack(
            rx.input(
                rx.input.slot(rx.icon(tag="search", size=16)),
                placeholder="Search for a ticker here!",
                type="search",
                size="2",
                value=SearchBarState.search_query,
                on_change=SearchBarState.set_query,
                on_blur=SearchBarState.set_display_suggestions(False),
                on_mount=SearchBarState.set_display_suggestions(False), # Hide suggestion dropdown on page load
                on_focus=SearchBarState.set_display_suggestions(True),
                width="100%",
            ),
            rx.cond(SearchBarState.display_suggestion,
                # Scrollable suggestion dropdown 
                rx.vstack(
                    rx.scroll_area(
                        rx.foreach(
                            rx.cond(SearchBarState.search_query is not None, 
                                    SearchBarState.get_suggest_ticker,
                                    SearchBarState.get_recent_ticker),
                            lambda ticker_value: suggestion_card(value=ticker_value),
                        ),
                        scrollbars="vertical",
                        type="scroll",
                    ),
                    width="100%",
                    max_height=250,
                    overflow_y="auto",
                    z_index="100",
                    background_color=rx.color('gray', 2),
                    position="absolute",
                    top="calc(100% + 5px)",
                    border_radius=6
                ),
                rx.box(),
            ),
            position="relative",
            width="22vw",
        )
    )


def suggestion_card(value: Dict[str, Any]) -> rx.Component:
    ticker = value['ticker']
    industry = value['industry']
    pct_price_change: float = value['pct_price_change'].to(float)

    return rx.box(
        rx.hstack(
            # ticker tag
            rx.text(
                ticker,
                size="5",
                weight="bold",
            ),
            # industry tag
            rx.badge(
                industry,
                size="2",
                weight="medium",
                variant='surface',
                color_scheme="violet",
                radius='medium',
            ),
            rx.spacer(),
            # pct badge
            pct_change_badge(diff=pct_price_change),

            align="center",
            spacing="2",
        ),
        on_click=[
            rx.redirect(f"/analyze/{ticker}"),
            SearchBarState.add_ticker_to_history(ticker=ticker),
            SearchBarState.set_query("")
        ],
        width="100%",
        padding="10px",
        cursor="pointer",
        _hover={'background_color': rx.color('gray', 3)},
        max_width="100%",
    )


