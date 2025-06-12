import reflex as rx
import pandas as pd
import time
import sqlite3
from typing import List, Dict, Any


class SearchBarState(rx.State):
    search_query: str = ""
    display_suggestion: bool = False
    recent_tickers: List[str] = []

    @rx.event
    def set_query(self, text: str=""):
        self.search_query = text
        
    @rx.event
    def set_display_suggestions(self, mode: bool):
        yield time.sleep(0.1) # Delay the set action
        self.display_suggestion = mode
    
    @rx.event
    def add_ticker_to_history(self, ticker: str):
        if not ticker in self.recent_tickers:
            self.recent_tickers.append(ticker)
    
    @rx.var
    def get_suggest_ticker(self) -> List[Dict[str, Any]]:
        """Recommends tickers on user's type"""
        if not self.display_suggestion:  return []
        
        conn = sqlite3.connect("ourportfolios/data/data_vni.db")
        query: str = f"""
                        SELECT ticker, organ_name, current_price, price_change, pct_price_change 
                        FROM data_vni 
                        WHERE ticker 
                        LIKE ? 
                        ORDER BY current_price DESC
                    """
        df: pd.DataFrame = pd.read_sql(query, conn, params=(f"{self.search_query}%",))
        conn.close()
        return df.to_dict('records')

    @rx.var 
    def get_recent_ticker(self) -> List[Dict[str, Any]]:
        """Yields recently visited tickers"""
        if not self.display_suggestion:  return []
        
        conn = sqlite3.connect("ourportfolios/data/data_vni.db")
        placeholders = ', '.join(['?'] * len(self.recent_tickers))
        query = f"""
                    SELECT ticker, organ_name, current_price, price_change, pct_price_change 
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
            width="20vw",
            border_radius="8px",
        ),
        rx.vstack(
            rx.foreach(
                rx.cond(SearchBarState.search_query, SearchBarState.get_suggest_ticker, SearchBarState.get_recent_ticker),
                lambda ticker_value: suggestion_card(value=ticker_value),
            ),
            border="1px solid #444",
            border_top="none",
            width="20vw",
            max_height="250px",
            overflow_y="auto",
            z_index="100",
            background_color="#282828",
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
    organ_name = value['organ_name']
    current_price: int = value['current_price'].to(int)
    price_change: float = value['price_change'] #.to(float)
    pct_price_change: float = value['pct_price_change'].to(float)
    
    color = rx.cond(pct_price_change > 0, "#28a745", rx.cond(pct_price_change < 0, "#CC0000", "#6B7280"))

    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text(ticker, size="3", weight="medium"),
                rx.text(organ_name, size="1", weight="medium", color="#6B7280"),
                align="start",
            ),
            rx.spacer(),
            rx.vstack(
                rx.text(f"{current_price}", size="3", weight="medium"),
                #Note:  Price change data will be available on feat/ticker-filter/ui branch
                rx.text(f"{price_change}|{pct_price_change}%", size="2", weight="medium", color=color),
                align="end",
            ),
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
    