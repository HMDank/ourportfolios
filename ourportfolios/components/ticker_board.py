import reflex as rx
import pandas as pd

from typing import List, Dict, Any
from sqlalchemy import TextClause, text

from ..utils.scheduler import db_settings
from ..utils.generate_query import get_suggest_ticker
from ..components.drawer import CartState
from ..components.graph import pct_change_badge


class TickerBoardState(rx.State):
    search_query: str = ""

    # Filters
    selected_exchange: List[str] = []
    selected_industry: List[str] = []
    selected_technical_metric: Dict[str, List[float]] = {}
    selected_fundamental_metric: Dict[str, List[float]] = {}

    # Sorts
    selected_sort_order: str = "ASC"
    selected_sort_option: str = "ticker"

    @rx.event
    def apply_filters(self, filters: Dict[str, Any]):
        self.selected_exchange = filters.pop("exchange", [])
        self.selected_industry = filters.pop("industry", [])
        self.selected_technical_metric = filters.pop("technical", {})
        self.selected_fundamental_metric = filters.pop("fundamental", {})

    @rx.event
    def clear_filters(self):
        self.selected_exchange = []
        self.selected_industry = []
        self.selected_technical_metric = {}
        self.selected_fundamental_metric = {}

    @rx.event
    def set_sort_option(self, option: str):
        self.selected_sort_option = option

    @rx.event
    def set_sort_order(self, order: str):
        self.selected_sort_order = order

    @rx.var
    def get_all_tickers(self) -> List[Dict[str, Any]]:
        query: List[str] = [
            """SELECT ticker, organ_name, current_price, accumulated_volume, pct_price_change 
            FROM comparison.comparison_df 
            WHERE"""
        ]

        if self.search_query != "":
            match_query, params = get_suggest_ticker(
                search_query=self.search_query, return_type="query"
            )
            query.append(match_query)
        else:
            query.append("1=1")
            params = None

        # Filter by industry
        if self.selected_industry:
            query.append(
                f"AND industry IN ({', '.join(f"'{industry}'" for industry in self.selected_industry)})"
            )

        # Filter by exchange
        if self.selected_exchange:
            query.append(
                f"AND exchange IN ({', '.join(f"'{exchange}'" for exchange in self.selected_exchange)})"
            )

        # Filter by metrics
        if self.selected_fundamental_metric:  # Fundamental
            query.append(
                " ".join(
                    [
                        f"AND {metric} BETWEEN {value_range[0]} AND {value_range[1]}"
                        for metric, value_range in self.selected_fundamental_metric.items()
                    ]
                )
            )

        if self.selected_technical_metric:  # Technical
            query.append(
                " ".join(
                    [
                        f"AND {metric} BETWEEN {value_range[0]} AND {value_range[1]}"
                        for metric, value_range in self.selected_technical_metric.items()
                    ]
                )
            )

        # Order by condition
        if self.selected_sort_option:
            query.append(
                f"ORDER BY {self.selected_sort_option} {self.selected_sort_order}"
            )

        full_query: TextClause = text(" ".join(query))

        with db_settings.conn.connect() as connection:
            try:
                return pd.read_sql(full_query, connection, params=params).to_dict(
                    "records"
                )

            except Exception:
                return []


def ticker_board() -> rx.Component:
    card_layout = {
        "layout_spacing": {
            "paddingRight": "3em",
            "paddingLeft": "2em",
            "marginTop": "0.25em",
            "marginBottom": "0.5em",
        },
        "layout_segments": {
            "symbol": {"width": "52%", "align": "left"},
            "instrument": {"width": "12%", "align": "center"},
            "cart": {"width": "12%", "align": "center"},
        },
    }
    return (
        rx.card(
            # Header
            ticker_basic_info_header(**card_layout),
            # Ticker
            rx.scroll_area(
                rx.foreach(
                    TickerBoardState.get_all_tickers,
                    lambda value: ticker_card(
                        ticker=value.ticker,
                        organ_name=value.organ_name,
                        current_price=value.current_price,
                        accumulated_volume=value.accumulated_volume,
                        pct_price_change=value.pct_price_change,
                        **card_layout,
                    ),
                ),
                paddingRight="0.6em",
                type="hover",
                scrollbars="vertical",
                width="61em",
                height="30em",
            ),
            background_color=rx.color("gray", 1),
            border_radius=6,
            width="100%",
        ),
    )


def ticker_card(
    ticker: str,
    organ_name: str,
    current_price: float,
    accumulated_volume: int,
    pct_price_change: float,
    **kwargs,
):
    color = rx.cond(
        pct_price_change.to(int) > 0,
        rx.color("green", 11),
        rx.cond(pct_price_change.to(int) < 0, rx.color("red", 9), rx.color("gray", 7)),
    )
    instrument_text_props = {"weight": "regular", "size": "3", "color": color}
    return rx.card(
        rx.flex(
            # Ticker and organ_name
            rx.box(
                rx.link(
                    rx.text(ticker, weight="medium", size="7"),
                    href=f"/analyze/{ticker}",
                    style={"textDecoration": "none", "color": "inherit"},
                ),
                rx.text(organ_name, color=rx.color("gray", 7), size="2"),
                **kwargs["layout_segments"]["symbol"],
            ),
            # Price
            rx.text(
                current_price,
                **instrument_text_props,
                **kwargs["layout_segments"]["instrument"],
            ),
            # Volume
            rx.text(
                f"{accumulated_volume:,.3f}",
                **instrument_text_props,
                **kwargs["layout_segments"]["instrument"],
            ),
            # Change
            rx.text(
                pct_change_badge(diff=pct_price_change),
                **instrument_text_props,
                **kwargs["layout_segments"]["instrument"],
            ),
            # Cart button
            rx.spacer(),
            rx.button(
                rx.icon("shopping-cart", size=16),
                size="2",
                variant="soft",
                on_click=lambda: CartState.add_item(ticker),
            ),
            align="center",
            direction="row",
            width="100%",
        ),
        width="100%",
        **kwargs["layout_spacing"],
    )


def ticker_basic_info_header(**kwargs) -> rx.Component:
    heading_text_props = {
        "weight": "medium",
        "color": "white",
        "size": "3",
    }
    return rx.card(
        rx.flex(
            rx.heading(
                "Symbol",
                **heading_text_props,
                **kwargs["layout_segments"]["symbol"],
            ),
            # Price
            rx.heading(
                "Price",
                **heading_text_props,
                **kwargs["layout_segments"]["instrument"],
            ),
            # Volume
            rx.heading(
                "Volume",
                **heading_text_props,
                **kwargs["layout_segments"]["instrument"],
            ),
            # % Change
            rx.heading(
                "% Change",
                **heading_text_props,
                **kwargs["layout_segments"]["instrument"],
            ),
            direction="row",
            width="100%",
            **kwargs["layout_spacing"],
        ),
        variant="ghost",
    )
