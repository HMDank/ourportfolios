import reflex as rx
import pandas as pd
import time
import sqlite3
from typing import List, Dict, Any
import itertools

class SearchBarState(rx.State):
    search_query: str = ""
    display_suggestion: bool = False
    recent_tickers: List[str] = []

    @rx.event
    def set_query(self, text: str=""):
        self.search_query = text
        
    @rx.event
    def set_display_suggestions(self, mode: bool):
        yield time.sleep(0.15) # Delay the set action
        self.display_suggestion = mode
    
    @rx.event
    def add_ticker_to_history(self, ticker: str):
        if not ticker in self.recent_tickers:
            self.recent_tickers.append(ticker)
    
    @rx.var
    def get_suggest_ticker(self) -> List[Dict[str, Any]]:
        """Recommends tickers on user's type"""
        if not self.display_suggestion:  return []
        
        # At first, try to fetch exact ticker
        match_conditions = "ticker LIKE ?"
        result: pd.DataFrame = self.fetch_ticker(match_conditions=match_conditions, params=(f"{self.search_query}%",))
        
        # In-case of mistype or no ticker returned, calculate all possible permutation of provided search_query with fixed length
        if result.empty:
            # All possible combination of ticker's letter
            combos = list(itertools.permutations(list(self.search_query), len(self.search_query)))
            all_combination = [f"{''.join(combo)}%" for combo in combos]
            
            match_conditions = " OR ".join(["ticker LIKE ?"] * len(combos))
            result: pd.DataFrame = self.fetch_ticker(match_conditions=match_conditions, params=all_combination)
        
        # Suggest base of the first letter if still no ticker matched
        if result.empty:
            result: pd.DataFrame = self.fetch_ticker(match_conditions="ticker LIKE ?", params=(f"{self.search_query[0]}%",))
            
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
        if not self.display_suggestion:  return []
        
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
        rx.input(
            rx.input.slot(rx.icon(tag="search", size=16)),
            placeholder="Search for a ticker here!",
            type="search",
            size="2",
            value=SearchBarState.search_query,
            on_change=SearchBarState.set_query,
            on_blur=SearchBarState.set_display_suggestions(False),
            on_focus=SearchBarState.set_display_suggestions(True),
            width="24vw",
            border_radius="8px",
        ),
        rx.vstack(
            rx.foreach(
                rx.cond(SearchBarState.search_query, SearchBarState.get_suggest_ticker, SearchBarState.get_recent_ticker),
                lambda ticker_value: suggestion_card(value=ticker_value),
            ),
            width="24vw",
            max_height="250px",
            overflow_y="auto",
            z_index="100",
            background_color=rx.color('gray', 2),
            color="white", 
            position="absolute",
            top="calc(100% + 5px)",
            left="0",
        ),
        position="relative",
        background_color="#000000",
        border_radius="8px",
    )
    
def suggestion_card(value: Dict[str, Any]) -> rx.Component:
    ticker = value['ticker']
    industry = value['industry']
    pct_price_change: float = value['pct_price_change'].to(float)
    
    color = rx.cond(pct_price_change > 0, rx.color('jade', 11), rx.cond(pct_price_change < 0, rx.color('red', 9), rx.color('gray', 7)))
    scheme = rx.cond(pct_price_change > 0, "green", rx.cond(pct_price_change < 0, "red", "gray"))
    
    return rx.box(
        rx.hstack(
            rx.badge(
                ticker,
                size="3",
                weight="bold",
                variant='solid',
                color_scheme="violet",
                radius='small',
            ),
            
            rx.badge(
                industry,
                size="2",
                weight="medium",
                variant='surface',
                color_scheme="gray",
                radius='medium',
            ),
            
            rx.spacer(),
            
            rx.badge(
                f"{pct_price_change}%", 
                size="1", 
                weight="medium", 
                color=color, 
                variant="surface",
                color_scheme=scheme,
                radius='full',
            ),
            
            align="center",
            spacing="2",
        ),
        on_click=[
            rx.redirect(f"/analyze/{ticker}"), 
            SearchBarState.add_ticker_to_history(ticker=ticker),
            SearchBarState.set_query("")
        ],
        width="100%",
        padding="8px",
        border_radius="8px",
        cursor="pointer",
        _hover={'background_color':"#000000"}
    )
    