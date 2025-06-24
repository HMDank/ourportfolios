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

    @rx.event
    def set_query(self, text: str = ""):
        self.search_query = text

    @rx.event
    def set_display_suggestions(self, mode: bool):
        yield time.sleep(0.2)  # Delay the set action
        self.display_suggestion = mode

    @rx.var
    def get_suggest_ticker(self) -> List[Dict[str, Any]]:
        """Recommends tickers on user's keystroke, sort by pct price change"""
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
                        ORDER BY ticker ASC
                    """
        result: pd.DataFrame = pd.read_sql(query, conn, params=params)
        conn.close()
        return result


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
                on_mount=SearchBarState.set_display_suggestions(
                    False),  # Hide suggestion dropdown on page load
                on_focus=SearchBarState.set_display_suggestions(True),
                width="100%",
            ),
            rx.cond(SearchBarState.display_suggestion,
                    # Scrollable suggestion dropdown
                    rx.fragment(
                        rx.vstack(
                            rx.scroll_area(
                                rx.foreach(
                                    SearchBarState.get_suggest_ticker,
                                    lambda ticker_value: suggestion_card(
                                        value=ticker_value),
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
                    ),
                    rx.fragment(),
                    ),
            position="relative",
            width="20vw",
        )
    )


def suggestion_card(value: Dict[str, Any]) -> rx.Component:
    ticker = value['ticker']
    industry = value['industry']
    pct_price_change: float = value['pct_price_change'].to(float)

    return rx.box(
        rx.hstack(
            rx.vstack(
                # ticker tag
                rx.text(
                    ticker,
                    size="5",
                    weight="bold",
                ),
                # industry tag
                rx.badge(
                    industry,
                    size="1",
                    weight="medium",
                    variant='surface',
                    color_scheme="violet",
                    radius='medium',
                ),
                spacing="1",
            ),
            rx.spacer(),
            # pct badge
            pct_change_badge(diff=pct_price_change),
            align="center",
            spacing="1",
        ),
        on_click=[
            rx.redirect(f"/analyze/{ticker}"),
            SearchBarState.set_query("")
        ],
        width="100%",
        padding="10px",
        cursor="pointer",
        _hover={'background_color': rx.color('gray', 3)},
    )
