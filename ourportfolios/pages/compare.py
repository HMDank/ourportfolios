import reflex as rx
import pandas as pd
import sqlite3
from typing import List, Dict, Any

from ..components.navbar import navbar
from ..components.drawer import CartState, drawer_button
from ..components.page_roller import card_link, card_wrapper


class StockComparisonState(rx.State):
    stocks: List[Dict[str, Any]] = []
    compare_list: List[str] = []  # New: list of tickers for comparison
    selected_metrics: List[str] = [
        'roe', 'pe', 'pb', 'dividend_yield',
        'revenue_growth_1y', 'eps_growth_1y', 'gross_margin',
        'net_margin', 'beta', 'rsi14'
    ]  # Changed from @rx.var to state variable

    @rx.var
    def available_metrics(self) -> List[str]:
        """All available metrics that can be selected"""
        return [
            'roe', 'pe', 'pb', 'dividend_yield',
            'revenue_growth_1y', 'eps_growth_1y', 'gross_margin',
            'net_margin', 'beta', 'rsi14',
            'industry', 'tcbs_recommend'
        ]

    @rx.var
    def metric_labels(self) -> Dict[str, str]:
        """Get human-readable labels for metrics"""
        return {
            'roe': 'ROE',
            'pe': 'P/E Ratio',
            'pb': 'P/B Ratio',
            'dividend_yield': 'Dividend Yield',
            'revenue_growth_1y': 'Revenue Growth (1Y)',
            'eps_growth_1y': 'EPS Growth (1Y)',
            'gross_margin': 'Gross Margin',
            'net_margin': 'Net Margin',
            'beta': 'Beta',
            'rsi14': 'RSI (14)',
            'industry': 'Industry',
            'tcbs_recommend': 'Recommendation'
        }

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
    def best_performers(self) -> Dict[str, int]:
        """Get the index of best performing stock for each metric"""
        best = {}
        higher_better = [
            'roe', 'dividend_yield', 'revenue_growth_1y',
            'eps_growth_1y', 'gross_margin', 'net_margin'
        ]

        for metric in self.selected_metrics:
            values = []
            for i, stock in enumerate(self.stocks):
                val = stock.get(metric)
                if val is not None and isinstance(val, (int, float)):
                    values.append((val, i))

            if values:
                if metric in higher_better:
                    best[metric] = max(values, key=lambda x: x[0])[1]
                elif metric in ['pe', 'pb']:  # Lower is better
                    best[metric] = min(values, key=lambda x: x[0])[1]
                else:
                    best[metric] = -1
            else:
                best[metric] = -1

        return best

    def _format_value(self, key: str, value: Any) -> str:
        """Format values for display - private method"""
        if value is None:
            return "N/A"

        if key == 'market_cap':
            return f"{value}B VND"
        elif key in [
            'roe', 'dividend_yield', 'revenue_growth_1y',
            'eps_growth_1y', 'gross_margin', 'net_margin'
        ]:
            return f"{value*100:.1f}%"
        elif key in ['pe', 'pb', 'beta']:
            return f"{value:.1f}"
        elif key == 'rsi14':
            return f"{value:.0f}"
        else:
            return str(value)

    @rx.event
    def toggle_metric(self, metric: str):
        """Toggle a metric in the selected_metrics list"""
        if metric in self.selected_metrics:
            self.selected_metrics = [
                m for m in self.selected_metrics if m != metric]
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
        """Remove a specific stock from the compare list and update stocks data"""
        # Remove from compare_list
        self.compare_list = [t for t in self.compare_list if t != ticker]
        # Remove from stocks data
        self.stocks = [s for s in self.stocks if s.get('ticker') != ticker]

    @rx.event
    async def import_cart_to_compare(self):
        """Import tickers from cart into compare_list."""
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
        conn = sqlite3.connect(
            "/home/dank/Documents/Codebases/ourportfolios/"
            "ourportfolios/data/data_vni.db"
        )
        for ticker in tickers:
            query = (
                "SELECT ticker, market_cap, roe, pe, pb, dividend_yield, "
                "revenue_growth_1y, eps_growth_1y, gross_margin, net_margin, "
                "beta, rsi14, industry, tcbs_recommend "
                "FROM data_vni WHERE ticker = ?"
            )
            df = pd.read_sql(query, conn, params=(ticker,))
            if not df.empty:
                stocks.append(df.iloc[0].to_dict())
        conn.close()
        self.stocks = stocks

    @rx.event
    async def import_and_fetch_compare(self):
        """
        Import tickers from cart into compare_list and fetch their stock data.
        """
        cart_state = await self.get_state(CartState)
        tickers = [item["name"] for item in cart_state.cart_items]
        self.compare_list = tickers
        await self.fetch_stocks_from_compare()


def metric_selector_popover() -> rx.Component:
    """Popover component for selecting metrics to compare"""
    return rx.popover.root(
        rx.popover.trigger(
            rx.button(
                rx.hstack(
                    rx.icon("settings", size=16),
                    spacing="2"
                ),
                variant="outline",
                size="2"
            )
        ),

        rx.popover.content(
            rx.vstack(
                rx.hstack(
                    rx.spacer(),
                    rx.popover.close(
                        rx.button(
                            rx.icon("x", size=16),
                            variant="ghost",
                            size="1"
                        )
                    ),
                    width="100%",
                    align="center"
                ),
                rx.heading('Select metrics'),
                rx.scroll_area(
                    rx.vstack(
                        rx.foreach(
                            StockComparisonState.available_metrics,
                            lambda metric: rx.hstack(
                                rx.checkbox(
                                    checked=StockComparisonState.selected_metrics.contains(
                                        metric),
                                    on_change=lambda: StockComparisonState.toggle_metric(
                                        metric),
                                    size="2"
                                ),
                                rx.text(
                                    StockComparisonState.metric_labels[
                                        metric
                                    ],
                                    size="2"
                                ),
                                spacing="2",
                                align="center",
                                width="100%"
                            )
                        ),
                        spacing="2",
                        align="start",
                        width="100%"
                    ),
                    height="300px",
                    width="100%"
                ),
                rx.spacer(),
                rx.hstack(
                    rx.spacer(),
                    rx.button(
                        "Select All",
                        on_click=StockComparisonState.select_all_metrics,
                        size="1",
                        variant="soft"
                    ),
                    rx.button(
                        "Clear All",
                        on_click=StockComparisonState.clear_all_metrics,
                        size="1",
                        variant="soft"
                    ),
                    spacing="2",
                    width="100%"
                ),
                spacing="3",
                width="300px",
                padding="0.7em"
            ),
            side="bottom",
            align="start"
        )
    )


def stock_header_card(stock: Dict[str, Any]) -> rx.Component:
    """Create header card for each stock with remove button"""
    market_cap = stock.get('market_cap', "")
    ticker = stock.get('ticker', '')

    return rx.card(
        rx.vstack(
            # Remove button positioned at top-right
            rx.button(
                rx.icon("x", size=12),
                on_click=lambda: StockComparisonState.remove_stock_from_compare(
                    ticker),
                variant="ghost",
                size="1",
                color_scheme="red",
                style={
                    "position": "absolute",
                    "top": "0.75em",
                    "right": "0.75em",
                    "padding": "0.25em",
                    "min_width": "auto",
                    "height": "auto",
                    "border_radius": "50%",
                    "opacity": "0.7"
                }
            ),
            # Stock content - clickable area
            rx.link(
                rx.vstack(
                    rx.text(
                        ticker,
                        weight="bold",
                        size="6",
                        color=rx.color("gray", 12),
                        letter_spacing="0.05em"
                    ),
                    rx.badge(
                        stock.get('industry', ''),
                        size="1",
                        variant="soft",
                        style={"font_size": "0.7em"}
                    ),
                    rx.text(
                        f"{market_cap} B. VND",
                        size="1",
                        color=rx.color("gray", 10),
                        weight="medium"
                    ),
                    spacing="2",
                    align="center",
                    justify="center",
                    width="100%",
                    padding_top="1.5em"
                ),
                href=f"/analyze/{ticker}",
                text_decoration="none",
                _hover={"text_decoration": "none"},
                width="100%"
            ),
            spacing="0",
            align="center",
            justify="center",
            width="100%",
            height="100%"
        ),
        padding="0.5em",  # Reduced padding
        width="12em",
        min_height="7em",  # Slightly reduced height
        display="flex",
        align_items="center",
        justify_content="center",
        position="relative",
        style={
            "border": f"1px solid {rx.color('gray', 6)}",
            "border_radius": "12px",
            "transition": "all 0.2s ease",
            "cursor": "pointer",
            "flex_shrink": "0"
        },
        _hover={
            "border_color": rx.color("gray", 8),
            "transform": "translateY(-2px)",
            "box_shadow": f"0 8px 25px -5px {rx.color('gray', 4)}"
        }
    )


def stock_headers() -> rx.Component:
    """
    Create the header row with all stock information.
    The metric label column is sticky.
    """
    return rx.hstack(
        # Sticky metric label placeholder
        rx.box(
            width="12em",
            min_width="12em",
            style={
                "flex_shrink": "0",
                "position": "sticky",
                "left": 0,
                "z_index": 2,
                "background": rx.color("gray", 1),
                "border_right": f"1px solid {rx.color('gray', 4)}"
            }
        ),
        # Horizontally scrollable stock header cards
        rx.hstack(
            rx.foreach(
                StockComparisonState.formatted_stocks,
                lambda stock, _:
                    stock_header_card(stock)
            ),
            spacing="2",
            style={"flex_wrap": "nowrap"},
            margin_top="0.5em"  # Add top margin to prevent cut-off
        ),
        spacing="0",
        margin_bottom="1.5em",
        width="fit-content",
        min_width="fit-content",
        style={"flex_wrap": "nowrap"}
    )


def metric_comparison_row(metric_key: str) -> rx.Component:
    """
    Create a row comparing a specific metric across all stocks.
    The metric label and the values are in two separate boxes.
    The metric label column is sticky.
    """
    return rx.hstack(
        # Sticky metric label card (its own card/box)
        rx.card(
            rx.box(
                rx.text(
                    StockComparisonState.metric_labels[
                        metric_key
                    ],
                    size="2",
                    weight="medium",
                    color=rx.color("gray", 12)
                ),
                width="12em",
                min_width="12em",
                padding="0.5em 0.3em 0.5em 0.5em",  # Reduced padding
                background_color=rx.color("gray", 2),
                display="flex",
                align_items="center",
                style={
                    "flex_shrink": "0",
                    "position": "sticky",
                    "left": 0,
                    "z_index": 2,
                    "background": rx.color("gray", 1),
                    "border_right": f"1px solid {rx.color('gray', 4)}"
                }
            ),
            width="12em",
            min_width="12em",
            background_color=rx.color("gray", 1),
            style={
                # border style split for line length
                "border": (
                    f"1px solid {rx.color('gray', 3)}"
                ),
                "border_radius": "8px 0 0 8px",
                "flex_shrink": "0",
                "overflow": "visible",
                "margin_right": "0px"
            }
        ),
        # Metric values card (its own card/box, horizontally scrollable)
        rx.card(
            rx.hstack(
                rx.foreach(
                    StockComparisonState.formatted_stocks,
                    lambda stock, index: rx.box(
                        rx.text(
                            stock[metric_key],
                            size="2",
                            weight=rx.cond(
                                StockComparisonState.best_performers[
                                    metric_key
                                ] == index,
                                "bold",
                                "medium"
                            ),
                            color=rx.cond(
                                StockComparisonState.best_performers[
                                    metric_key
                                ] == index,
                                rx.color("green", 11),
                                rx.color("gray", 11)
                            )
                        ),
                        width="12em",
                        min_width="12em",
                        padding="0.5em",  # Reduced padding
                        text_align="center",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        style={"flex_shrink": "0"}
                    )
                ),
                spacing="2",
                style={"flex_wrap": "nowrap"}
            ),
            width="fit-content",
            min_width="fit-content",
            background_color=rx.color("gray", 1),
            style={
                # border style split for line length
                "border": (
                    f"1px solid {rx.color('gray', 3)}"
                ),
                "border_radius": "0 8px 8px 0",
                "flex_shrink": "0",
                "overflow": "visible",
                "margin_left": "0px"
            }
        ),
        spacing="0",
        align="center",
        width="fit-content",
        style={"flex_wrap": "nowrap"}
    )


def metric_label_column() -> rx.Component:
    """
    Fixed vertical column of metric labels (sticky/fixed on the left),
    perfectly aligned with the number rows and with minimal spacing.
    """
    return rx.vstack(
        rx.foreach(
            StockComparisonState.selected_metrics,
            lambda metric_key: rx.card(
                rx.box(
                    rx.text(
                        StockComparisonState.metric_labels[metric_key],
                        size="2",
                        weight="medium",
                        color=rx.color("gray", 12)
                    ),
                    width="12em",
                    min_width="12em",
                    padding="0.5em 0.3em 0.5em 0.5em",
                    background_color=rx.color("gray", 2),
                    display="flex",
                    align_items="center",
                    style={
                        "flex_shrink": "0",
                        "position": "sticky",
                        "left": 0,
                        "z_index": 2,
                        "background": rx.color("gray", 1),
                        "border_right": f"1px solid {rx.color('gray', 4)}"
                    }
                ),
                width="12em",
                min_width="12em",
                background_color=rx.color("gray", 1),
                style={
                    "border": (
                        f"1px solid {rx.color('gray', 3)}"
                    ),
                    "border_radius": "8px 0 0 8px",
                    "flex_shrink": "0",
                    "overflow": "visible",
                    # Minimal spacing from value columns
                    "margin_right": "0.5em"
                }
            )
        ),
        spacing="1",
        align="start",
        width="fit-content",
        style={
            "flex_wrap": "nowrap",
            "margin_top": "8.5em"  # Push down to align with metric rows
        }
    )


def comparison_controls() -> rx.Component:
    """Controls section with metric selector and load button"""
    return rx.hstack(
        rx.button(
            rx.hstack(
                rx.icon("import", size=16),
                rx.text("Import from Cart"),
                spacing="2"
            ),
            on_click=StockComparisonState.import_and_fetch_compare,
            size="2",
        ),
        rx.spacer(),
        metric_selector_popover(),
        spacing="3",
        align="center",
        width="100%",
        margin_bottom="2em"
    )


def comparison_section() -> rx.Component:
    """
    Main comparison section with all metrics.
    Metric labels are fixed on the left,
    only the table content scrolls horizontally.
    """
    return rx.cond(
        StockComparisonState.compare_list,
        rx.box(
            rx.vstack(
                comparison_controls(),
                rx.hstack(
                    # Fixed metric label column
                    metric_label_column(),
                    # Scrollable area for stock headers and metric values
                    rx.box(
                        rx.scroll_area(
                            rx.vstack(
                                # Stock headers (no metric label placeholder)
                                rx.hstack(
                                    rx.foreach(
                                        StockComparisonState.formatted_stocks,
                                        lambda stock, _:
                                            stock_header_card(stock)
                                    ),
                                    spacing="2",
                                    style={"flex_wrap": "nowrap"},
                                    margin_top="0.5em"
                                ),
                                # Metric value rows (no metric label column)
                                rx.foreach(
                                    StockComparisonState.selected_metrics,
                                    lambda metric_key: rx.card(
                                        rx.hstack(
                                            rx.foreach(
                                                StockComparisonState.
                                                formatted_stocks,
                                                lambda stock, index: rx.box(
                                                    rx.text(
                                                        stock[metric_key],
                                                        size="2",
                                                        weight=rx.cond(
                                                            StockComparisonState.
                                                            best_performers[
                                                                metric_key
                                                            ] == index,
                                                            "bold",
                                                            "medium"
                                                        ),
                                                        color=rx.cond(
                                                            StockComparisonState.
                                                            best_performers[
                                                                metric_key
                                                            ] == index,
                                                            rx.color(
                                                                "green", 11),
                                                            rx.color(
                                                                "gray", 11)
                                                        )
                                                    ),
                                                    width="12em",
                                                    min_width="12em",
                                                    padding="0.5em",
                                                    text_align="center",
                                                    display="flex",
                                                    align_items="center",
                                                    justify_content="center",
                                                    style={"flex_shrink": "0"}
                                                )
                                            ),
                                            spacing="2",
                                            style={"flex_wrap": "nowrap"}
                                        ),
                                        width="fit-content",
                                        min_width="fit-content",
                                        background_color=rx.color("gray", 1),
                                        style={
                                            # Minimal border style
                                            "border": (
                                                f"1px solid {rx.color('gray', 3)}"
                                            ),
                                            "border_radius": "0 8px 8px 0",
                                            "flex_shrink": "0",
                                            "overflow": "visible",
                                            "margin_left": "0px"
                                        }
                                    )
                                ),
                                spacing="1",
                                align="start",
                                width="fit-content"
                            ),
                            direction="horizontal",
                            scrollbars="horizontal",
                            style={
                                "width": "100%",
                                "max_height": "none"
                            }
                        ),
                        width="100%",
                        style={
                            "overflow_x": "auto",
                            "overflow_y": "visible"
                        }
                    ),
                    spacing="0",
                    width="100%"
                ),
                spacing="0",
                width="100%"
            ),
            width="100%",
            style={
                "max_width": "100vw",
                "margin": "0 auto",
                "padding": "1.5em",
                "overflow": "hidden"
            }
        ),
        rx.center(
            rx.vstack(
                rx.text(
                    "Your compare list is empty. "
                    "Use the button below to import from cart.",
                    size="3",
                    weight="medium",
                    align="center",
                ),
                rx.button(
                    rx.hstack(
                        rx.icon("shopping_cart", size=16),
                        rx.text("Import from Cart"),
                        spacing="2"
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
        navbar(),
        rx.box(
            rx.link(
                rx.hstack(rx.icon("chevron_left", size=22),
                          rx.text("analyze", margin_top="-2px"), spacing="0"),
                href='/analyze',
                underline="none"
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
                "max_width": "90vw",  # Reduced max width
                "margin": "0 auto",
            },
        ),
        drawer_button(),
        spacing='0',
    )
