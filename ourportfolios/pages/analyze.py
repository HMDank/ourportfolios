import reflex as rx
import pandas as pd
import sqlite3
from typing import List, Dict, Any

from ..components.navbar import navbar
from ..components.drawer import CartState, drawer_button
from ..components.page_roller import card_roller, card_link


class StockComparisonState(rx.State):
    stocks: List[Dict[str, Any]] = []

    @rx.var
    def selected_metrics(self) -> List[str]:
        """Default metrics to display"""
        return [
            'market_cap', 'roe', 'pe', 'pb', 'dividend_yield',
            'revenue_growth_1y', 'eps_growth_1y', 'gross_margin',
            'net_margin', 'beta', 'rsi14'
        ]

    @rx.var
    def metric_labels(self) -> Dict[str, str]:
        """Get human-readable labels for metrics"""
        return {
            'market_cap': 'Market Cap',
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
            print("[DEBUG] Formatting stock:", stock)
            formatted_stock = {}
            for key, value in stock.items():
                if key in self.selected_metrics:
                    formatted_stock[key] = self._format_value(key, value)
                else:
                    formatted_stock[key] = value
            print("[DEBUG] Formatted stock:", formatted_stock)
            formatted.append(formatted_stock)
        print("[DEBUG] All formatted stocks:", formatted)
        return formatted

    @rx.var
    def best_performers(self) -> Dict[str, int]:
        """Get the index of best performing stock for each metric"""
        best = {}
        higher_better = [
            'market_cap', 'roe', 'dividend_yield', 'revenue_growth_1y',
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
            return f"${value/1e9:.1f}B"
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
        print("[DEBUG] Cart tickers:", tickers)
        stocks = []
        if not tickers:
            print("[DEBUG] No tickers in cart.")
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
            print(f"[DEBUG] Query result for {ticker}:", df.to_dict())
            if not df.empty:
                stocks.append(df.iloc[0].to_dict())
        conn.close()
        print("[DEBUG] Stocks fetched:", stocks)
        self.stocks = stocks


def stock_header_card(stock: Dict[str, Any]) -> rx.Component:
    """Create header card for each stock"""
    print("[DEBUG] stock_header_card input:", stock)
    mc = stock.get('market_cap', None)
    print(f"[DEBUG] market_cap raw value: {mc} type: {type(mc)}")
    if isinstance(mc, (int, float)) and mc > 0:
        market_cap = f"{mc/1e9:.1f}B VND"
    elif isinstance(mc, (int, float)):
        market_cap = f"{mc} (raw, not >0)"
    else:
        market_cap = "N/A"
    print("[DEBUG] market_cap in stock_header_card (final):", market_cap)
    return rx.card(
        rx.vstack(
            rx.heading(
                stock.get('ticker', ''),
                size="6",
                weight="bold",
            ),
            rx.badge(
                stock.get('industry', ''),
                size="2",
            ),
            rx.text(
                market_cap,
                size="2"
            ),
            spacing="1",
            align="center"
        ),
        padding="1.2em",
        width="12em",
        min_height="9em"
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
        padding="0",
        margin_bottom="0.15em",
        width="100%"
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
    return rx.vstack(
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
    )


def legend_section() -> rx.Component:
    """Legend explaining the color coding"""
    return rx.card(
        rx.hstack(
            rx.text("Legend:", size="3", weight="bold"),
            rx.text("Best performing values are highlighted in", size="2"),
            rx.text("green", size="2", weight="bold",
                    color=rx.color("green", 11)),
            rx.text("and bolded", size="2"),
            spacing="2",
            align="center"
        ),
        background_color=rx.color("blue", 2),
        padding="1em",
        margin_top="2em",
        width="100%"
    )


def page_selection():
    return rx.box(
        card_roller(
            card_link(
                rx.hstack(
                    rx.icon("chevron_left", size=32),
                    rx.vstack(
                        rx.heading("Select", weight="bold", size="5"),
                        rx.text("caijdo", size="1"),
                        align="center",
                        justify="center",
                        height="100%",
                        spacing="1"
                    ),
                    align="center",
                    justify="center",
                ),
                href="/select",
            ),
            card_link(
                rx.vstack(
                    rx.heading("Analyze", weight="bold", size="7"),
                    rx.text("caijdo", size="3"),
                    align="center",
                    justify="center",
                    height="100%",
                    spacing="1"
                ),
                href="/analyze",
            ),
            card_link(
                rx.hstack(
                    rx.vstack(
                        rx.heading("Simulate", weight="bold", size="5"),
                        rx.text("caijdo", size="1"),
                        align="center",
                        justify="center",
                        height="100%",
                        spacing="1"
                    ),
                    rx.icon("chevron_right", size=32),
                    align="center",
                    justify="center",
                ),
                href="/simulate",
            ),
        ),
        width="100%",
        display="flex",
        justify_content="center",
        align_items="center",
        margin="0",
        padding="0",
    )


@rx.page(route="/analyze")
def index() -> rx.Component:
    """Main page component"""
    return rx.vstack(
        navbar(),
        page_selection(),
        rx.box(
            rx.vstack(
                comparison_section(),
                legend_section(),
                spacing="4",
                width="100%",
                padding="2em"
            ),
            width="100%",
            style={
                "maxWidth": "90vw",
                "margin": "0 auto",
            },
        ),
        drawer_button(),
        spacing='0',
    )
