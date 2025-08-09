import reflex as rx
import pandas as pd
from sqlalchemy import text
from typing import List, Dict, Any
from collections import defaultdict

from ..components.navbar import navbar
from ..components.drawer import CartState, drawer_button
from ..components.loading import loading_screen
from ..utils.scheduler import db_settings


class StockComparisonState(rx.State):
    stocks: List[Dict[str, Any]] = []
    compare_list: List[str] = []
    selected_metrics: List[str] = [
        "roe",
        "pe",
        "pb",
        "dividend_yield",
        "revenue_growth_1y",
        "eps_growth_1y",
        "gross_margin",
        "net_margin",
        "rsi14",
    ]

    @rx.var
    def available_metrics(self) -> List[str]:
        """All available metrics that can be selected"""
        return [
            "roe",
            "pe",
            "pb",
            "dividend_yield",
            "revenue_growth_1y",
            "eps_growth_1y",
            "gross_margin",
            "net_margin",
            "rsi14",
            "tcbs_recommend",
        ]

    @rx.var
    def metric_labels(self) -> Dict[str, str]:
        """Get human-readable labels for metrics"""
        return {
            "roe": "ROE",
            "pe": "P/E Ratio",
            "pb": "P/B Ratio",
            "dividend_yield": "Dividend Yield",
            "revenue_growth_1y": "Revenue Growth (1Y)",
            "eps_growth_1y": "EPS Growth (1Y)",
            "gross_margin": "Gross Margin",
            "net_margin": "Net Margin",
            "rsi14": "RSI (14)",
            "tcbs_recommend": "Recommendation",
        }

    @rx.var
    def grouped_stocks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group formatted stocks by industry"""
        groups = defaultdict(list)
        for stock in self.formatted_stocks:
            industry = stock.get("industry", "Unknown")
            groups[industry].append(stock)
        return dict(groups)

    @rx.var
    def formatted_stocks(self) -> List[Dict[str, Any]]:
        """Pre-format all stock values for display"""
        formatted = []
        for stock in self.stocks:
            formatted_stock = {}
            for key, value in stock.items():
                if key in self.selected_metrics:
                    formatted_stock[key] = self._format_value(key, value)
                else:
                    formatted_stock[key] = value
            formatted.append(formatted_stock)
        return formatted

    @rx.var
    def industry_best_performers(self) -> Dict[str, Dict[str, str]]:
        industry_best = {}
        higher_better = [
            "roe",
            "dividend_yield",
            "revenue_growth_1y",
            "eps_growth_1y",
            "gross_margin",
            "net_margin",
        ]
        lower_better = ["pe", "pb"]

        for industry, stocks in self.grouped_stocks.items():
            industry_best[industry] = {}

            for metric in self.selected_metrics:
                values = []
                for stock in stocks:
                    original_stock = next(
                        (
                            s
                            for s in self.stocks
                            if s.get("ticker") == stock.get("ticker")
                        ),
                        None,
                    )
                    if original_stock:
                        val = original_stock.get(metric)
                        if val is not None and isinstance(val, (int, float)):
                            values.append((val, stock.get("ticker")))

                if values:
                    if metric in higher_better:
                        best_ticker = max(values, key=lambda x: x[0])[1]
                    elif metric in lower_better:
                        best_ticker = min(values, key=lambda x: x[0])[1]
                    else:
                        best_ticker = None

                    industry_best[industry][metric] = best_ticker
                else:
                    industry_best[industry][metric] = None

        return industry_best

    def _format_value(self, key: str, value: Any) -> str:
        """Format values for display - private method"""
        if value is None:
            return "N/A"

        if key == "market_cap":
            return f"{value}B VND"
        elif key in [
            "roe",
            "dividend_yield",
            "revenue_growth_1y",
            "eps_growth_1y",
            "gross_margin",
            "net_margin",
        ]:
            return f"{value * 100:.1f}%"
        elif key in ["pe", "pb"]:
            return f"{value:.1f}"
        elif key == "rsi14":
            return f"{value:.0f}"
        else:
            return str(value)

    @rx.event
    def toggle_metric(self, metric: str):
        """Toggle a metric in the selected_metrics list"""
        if metric in self.selected_metrics:
            self.selected_metrics = [m for m in self.selected_metrics if m != metric]
        else:
            self.selected_metrics = self.selected_metrics + [metric]

    @rx.event
    def select_all_metrics(self):
        """Select all available metrics"""
        self.selected_metrics = self.available_metrics.copy()

    @rx.event
    def clear_all_metrics(self):
        """Clear all selected metrics"""
        self.selected_metrics = []

    @rx.event
    def remove_stock_from_compare(self, ticker: str):
        self.compare_list = [t for t in self.compare_list if t != ticker]
        self.stocks = [s for s in self.stocks if s.get("ticker") != ticker]

    @rx.event
    async def import_cart_to_compare(self):
        cart_state = await self.get_state(CartState)
        tickers = [item["name"] for item in cart_state.cart_items]
        self.compare_list = tickers

    @rx.event
    async def fetch_stocks_from_compare(self):
        """
        Fetch stock data for tickers in compare_list and store in self.stocks.
        """
        tickers = self.compare_list
        stocks = []
        if not tickers:
            self.stocks = []
            return
        for ticker in tickers:
            query = text(
                "SELECT ticker, market_cap, roe, pe, pb, dividend_yield, "
                "revenue_growth_1y, eps_growth_1y, gross_margin, net_margin, "
                "rsi14, industry, tcbs_recommend "
                "FROM comparison.comparison_df WHERE ticker = :pattern"
            )
            df = pd.read_sql(query, db_settings.conn, params={"pattern": ticker})
            if not df.empty:
                stocks.append(df.iloc[0].to_dict())

        self.stocks = stocks

    @rx.event
    async def import_and_fetch_compare(self):
        """Import tickers from cart into compare_list and fetch their stock data."""
        cart_state = await self.get_state(CartState)
        tickers = [item["name"] for item in cart_state.cart_items]
        self.compare_list = tickers
        await self.fetch_stocks_from_compare()


def metric_selector_popover() -> rx.Component:
    """Popover component for selecting metrics to compare"""
    return rx.popover.root(
        rx.popover.trigger(
            rx.button(
                rx.hstack(rx.icon("settings", size=16), spacing="2"),
                variant="outline",
                size="2",
            )
        ),
        rx.popover.content(
            rx.vstack(
                rx.hstack(
                    rx.heading("Select metrics"),
                    rx.spacer(),
                    rx.popover.close(
                        rx.button(rx.icon("x", size=16), variant="ghost", size="1")
                    ),
                    width="100%",
                    align="center",
                ),
                rx.scroll_area(
                    rx.vstack(
                        rx.foreach(
                            StockComparisonState.available_metrics,
                            lambda metric: rx.hstack(
                                rx.checkbox(
                                    checked=StockComparisonState.selected_metrics.contains(
                                        metric
                                    ),
                                    on_change=lambda: StockComparisonState.toggle_metric(
                                        metric
                                    ),
                                    size="2",
                                ),
                                rx.text(
                                    StockComparisonState.metric_labels[metric], size="2"
                                ),
                                spacing="2",
                                align="center",
                                width="100%",
                            ),
                        ),
                        spacing="2",
                        align="start",
                        width="100%",
                    ),
                    height="300px",
                    width="100%",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.spacer(),
                    rx.button(
                        "Select All",
                        on_click=StockComparisonState.select_all_metrics,
                        size="1",
                        variant="soft",
                    ),
                    rx.button(
                        "Clear All",
                        on_click=StockComparisonState.clear_all_metrics,
                        size="1",
                        variant="soft",
                    ),
                    spacing="2",
                    width="100%",
                ),
                spacing="3",
                width="300px",
                padding="0.7em",
            ),
            side="bottom",
            align="start",
        ),
    )


def stock_column_card(stock: Dict[str, Any], industry: str) -> rx.Component:
    """Create a column with separate header card and metrics card for each stock"""
    market_cap = stock.get("market_cap", "")
    ticker = stock.get("ticker", "")

    return rx.vstack(
        # Header card - separate from metrics
        rx.card(
            rx.box(
                rx.button(
                    rx.icon("x", size=12),
                    on_click=lambda: StockComparisonState.remove_stock_from_compare(
                        ticker
                    ),
                    variant="ghost",
                    size="2",
                    style={
                        "position": "absolute",
                        "top": "0.5em",
                        "right": "0.5em",
                        "min_width": "auto",
                        "height": "auto",
                        "opacity": "0.7",
                    },
                ),
                rx.link(
                    rx.vstack(
                        rx.text(
                            ticker,
                            weight="medium",
                            size="8",
                            color=rx.color("gray", 12),
                            letter_spacing="0.05em",
                        ),
                        rx.badge(
                            stock.get("industry", ""),
                            size="1",
                            variant="soft",
                            style={"font_size": "0.7em"},
                        ),
                        rx.text(
                            f"{market_cap} B. VND",
                            size="1",
                            color=rx.color("gray", 10),
                            weight="medium",
                        ),
                        spacing="2",
                        justify="center",
                        width="100%",
                        padding_bottom="0.2em",
                    ),
                    href=f"/analyze/{ticker}",
                    text_decoration="none",
                    _hover={
                        "text_decoration": "none",
                    },
                    width="100%",
                ),
                position="relative",
                width="100%",
            ),
            width="12em",
            style={
                "flex_shrink": "0",
                "transition": "transform 0.2s ease",
            },
            _hover={
                "transform": "translateY(-0.4em)",
            },
        ),
        # Metrics card
        rx.card(
            rx.vstack(
                rx.foreach(
                    StockComparisonState.selected_metrics,
                    lambda metric_key: rx.box(
                        rx.text(
                            stock[metric_key],
                            size="2",
                            weight=rx.cond(
                                StockComparisonState.industry_best_performers[industry][
                                    metric_key
                                ]
                                == ticker,
                                "medium",
                                "regular",
                            ),
                            color=rx.cond(
                                StockComparisonState.industry_best_performers[industry][
                                    metric_key
                                ]
                                == ticker,
                                rx.color("green", 11),
                                rx.color("gray", 11),
                            ),
                        ),
                        width="100%",
                        min_height="2.5em",
                        text_align="center",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        border_bottom=f"1px solid {rx.color('gray', 4)}",
                    ),
                ),
                spacing="0",
                width="100%",
            ),
            width="11.5em",
            style={"flex_shrink": "0"},
        ),
        spacing="5",
        align="center",
        width="12em",
        min_width="12em",
        style={"flex_shrink": "0"},
    )


def metric_labels_column() -> rx.Component:
    """Fixed column showing metric labels"""
    return rx.vstack(
        rx.card(
            rx.box(
                width="12em",
                min_width="12em",
                min_height="7.5em",
            ),
            width="12em",
            min_width="12em",
            style={
                "flex_shrink": "0",
                "visibility": "hidden",
            },
        ),
        # Metrics labels card
        rx.card(
            rx.vstack(
                rx.foreach(
                    StockComparisonState.selected_metrics,
                    lambda metric_key: rx.box(
                        rx.text(
                            StockComparisonState.metric_labels[metric_key],
                            size="2",
                            weight="medium",
                            color=rx.color("gray", 12),
                        ),
                        width="100%",
                        min_height="2.5em",
                        display="flex",
                        align_items="center",
                        justify_content="start",
                        border_bottom=f"1px solid {rx.color('gray', 4)}",
                    ),
                ),
                spacing="0",
                width="100%",
            ),
            width="12em",
            min_width="12em",
            style={"flex_shrink": "0"},
        ),
        spacing="2",
        align="start",
        style={"flex_shrink": "0"},
    )


def comparison_controls() -> rx.Component:
    """Controls section with metric selector and load button"""
    return rx.hstack(
        rx.spacer(),
        rx.hstack(
            rx.button(
                rx.hstack(rx.icon("import", size=16), spacing="2"),
                on_click=StockComparisonState.import_and_fetch_compare,
                size="2",
            ),
            metric_selector_popover(),
            spacing="3",
            align="center",
        ),
        spacing="0",
        align="center",
        width="100%",
        margin_bottom="2em",
    )


def industry_group_section(industry: str, stocks: List[Dict[str, Any]]) -> rx.Component:
    """Create a section for each industry group"""
    return rx.hstack(
        rx.foreach(
            stocks,
            lambda stock: stock_column_card(stock, industry),
        ),
        spacing="3",
        align="start",
        style={"flex_wrap": "nowrap"},
    )


def comparison_section() -> rx.Component:
    """Main comparison section with industry-grouped layout"""
    return rx.cond(
        StockComparisonState.compare_list,
        rx.box(
            rx.vstack(
                comparison_controls(),
                # Main comparison table
                rx.hstack(
                    # Fixed metric labels column
                    metric_labels_column(),
                    # Scrollable grouped stock columns area
                    rx.box(
                        rx.scroll_area(
                            rx.box(
                                rx.hstack(
                                    # Industry groups
                                    rx.foreach(
                                        StockComparisonState.grouped_stocks.items(),
                                        lambda item: industry_group_section(
                                            item[0], item[1]
                                        ),
                                    ),
                                    spacing="7",  # Space between industry groups
                                    align="start",
                                    style={"flex_wrap": "nowrap"},
                                ),
                                padding_top="0.5em",
                                padding_bottom="0.5em",
                            ),
                            direction="horizontal",
                            scrollbars="horizontal",
                            style={
                                "width": "100%",
                                "maxWidth": "90vw",
                                "overflowX": "auto",
                                "overflowY": "hidden",
                            },
                        ),
                        width="100%",
                        margin_left="1.8em",
                        style={
                            "maxWidth": "90vw",
                            "overflowX": "auto",
                            "overflowY": "hidden",
                            "position": "relative",
                        },
                    ),
                    spacing="0",
                    align="start",
                    width="100%",
                    style={"flex_wrap": "nowrap"},
                ),
                spacing="0",
                width="100%",
            ),
            width="100%",
            style={
                "max_width": "100vw",
                "margin": "0 auto",
                "padding": "1.5em",
                "overflowX": "hidden",
            },
        ),
        rx.center(
            rx.vstack(
                rx.text(
                    "Your compare list is empty. ",
                    size="3",
                    weight="medium",
                    align="center",
                ),
                rx.button(
                    rx.hstack(
                        rx.icon("shopping_cart", size=16),
                        rx.text("Import from Cart"),
                        spacing="2",
                    ),
                    on_click=StockComparisonState.import_and_fetch_compare,
                    size="3",
                ),
                spacing="3",
                align="center",
            ),
            min_height="40vh",
            width="100%",
        ),
    )


@rx.page(route="/analyze/compare")
def index() -> rx.Component:
    """Main page component"""
    return rx.fragment(
        loading_screen(),
        navbar(),
        rx.box(
            rx.link(
                rx.hstack(
                    rx.icon("chevron_left", size=22),
                    rx.text("analyze", margin_top="-2px"),
                    spacing="0",
                ),
                href="/analyze",
                underline="none",
            ),
            position="fixed",
            justify="center",
            style={"paddingTop": "1em", "paddingLeft": "0.5em"},
            z_index="1",
        ),
        rx.box(
            comparison_section(),
            width="100%",
            style={
                "max_width": "90vw",
                "margin": "0 auto",
            },
        ),
        drawer_button(),
        spacing="0",
    )
