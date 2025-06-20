import reflex as rx
import pandas as pd
import sqlite3
from typing import List, Dict, Any

from ..components.navbar import navbar
from ..components.drawer import CartState, drawer_button
from ..components.page_roller import card_link, card_wrapper


class StockComparisonState(rx.State):
    stocks: List[Dict[str, Any]] = []

    @rx.var
    def selected_metrics(self) -> List[str]:
        """Default metrics to display"""
        return [
            'roe', 'pe', 'pb', 'dividend_yield',
            'revenue_growth_1y', 'eps_growth_1y', 'gross_margin',
            'net_margin', 'beta', 'rsi14'
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
            'stock_rating': 'Stock Rating',
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
    async def fetch_stocks_from_cart(self):
        """Fetch stock data for tickers in the cart and store in self.stocks."""
        cart_state = await self.get_state(CartState)
        tickers = [item["name"] for item in cart_state.cart_items]
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


def stock_header_card(stock: Dict[str, Any]) -> rx.Component:
    """Create header card for each stock"""
    market_cap = stock.get('market_cap', "")

    card_content = rx.card(
        rx.vstack(
            rx.text(stock.get('ticker', ''), weight="bold", size="4"),
            rx.badge(
                stock.get('industry', ''),
                size="2",
            ),
            rx.text(
                market_cap,
                size="2"
            ),
            spacing="1",
            align="center",
            justify="center",  # Center vertically
            width="100%"        # Center horizontally
        ),
        padding="1.2em",
        width="12em",
        min_height="9em",
        display="flex",
        align_items="center",
        justify_content="center"
    )

    return card_link(
        card_content,
        href=f"/analyze/{stock.get('ticker', '')}"
    )


def metric_comparison_row(metric_key: str) -> rx.Component:
    """Create a row comparing a specific metric across all stocks"""
    return rx.card(
        rx.hstack(
            # Metric label column
            rx.box(
                rx.text(
                    StockComparisonState.metric_labels[metric_key],
                    size="3",
                    weight="medium",
                    color=rx.color("gray", 12)
                ),
                width="13em",
                padding="1em",
                background_color=rx.color("gray", 2)
            ),
            # Stock values
            rx.hstack(
                rx.foreach(
                    StockComparisonState.formatted_stocks,
                    lambda stock, index: rx.box(
                        rx.text(
                            stock[metric_key],
                            size="3",
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
                        padding="1em",
                        text_align="center"
                    )
                ),
                spacing="1"
            ),
            spacing="0",
            align="center",
            width="100%"
        ),
        padding="0.25em 0",  # Add vertical space between rows
        margin_bottom="0.5em",  # More space between rows
        width="100%",
        background_color=rx.color("gray", 1)
    )


def stock_headers() -> rx.Component:
    """Create the header row with all stock information"""
    return rx.hstack(
        # Empty space for metric labels column
        rx.box(width="13em"),
        # Stock header cards
        rx.hstack(
            rx.foreach(
                StockComparisonState.formatted_stocks,
                lambda stock, _: stock_header_card(stock)
            ),
            spacing="1"
        ),
        spacing="0",
        margin_bottom="1em",
        width="100%"
    )


def comparison_section() -> rx.Component:
    """Main comparison section with all metrics"""
    return rx.cond(
        CartState.cart_items,
        rx.box(
            rx.vstack(
                stock_headers(),
                rx.vstack(
                    rx.foreach(
                        StockComparisonState.selected_metrics,
                        metric_comparison_row
                    ),
                    spacing="0",
                    width="100%"
                ),
                spacing="1",
                width="100%"
            ),
            width="100%",
            style={
                "maxWidth": "90vw",
                "margin": "0 auto",
                "padding": "2em 1em"
            }
        ),
        rx.center(
            rx.vstack(
                rx.text(
                    "Your cart is empty. Please select some tickers to compare.",
                    size="3",
                    weight="medium",
                    align="center",
                ),
                rx.link(
                    rx.card(
                        rx.hstack(
                            rx.icon("chevron_left", size=32),
                            rx.heading("Select",
                                       weight="bold", size="6"),
                            align="center",
                            justify="center",
                            height="100%",
                            spacing="2"
                        ),
                        width="300px",
                        height="150px",
                        padding="4",
                        cursor="pointer",
                        _hover={"transform": "scale(1.02)"},
                        transition="transform 0.2s ease",
                    ),
                    href="/select",
                    underline='none',
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
                "maxWidth": "90vw",
                "margin": "0 auto",
            },
        ),
        drawer_button(),
        spacing='0',
    )
