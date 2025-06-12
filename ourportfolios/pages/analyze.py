import reflex as rx
from typing import List, Dict, Any

# Sample data structure - replace with your actual data
sample_stocks = [
    {
        'ticker': 'AAPL',
        'market_cap': 2800000000000,
        'roe': 0.26,
        'pe': 28.5,
        'pb': 8.2,
        'dividend_yield': 0.0185,
        'revenue_growth_1y': 0.08,
        'eps_growth_1y': 0.12,
        'gross_margin': 0.38,
        'net_margin': 0.23,
        'beta': 1.2,
        'rsi14': 55,
        'stock_rating': 'BUY',
        'industry': 'Technology',
        'tcbs_recommend': 'Strong Buy'
    },
    {
        'ticker': 'MSFT',
        'market_cap': 2500000000000,
        'roe': 0.35,
        'pe': 32.1,
        'pb': 12.8,
        'dividend_yield': 0.022,
        'revenue_growth_1y': 0.12,
        'eps_growth_1y': 0.18,
        'gross_margin': 0.42,
        'net_margin': 0.31,
        'beta': 0.9,
        'rsi14': 62,
        'stock_rating': 'BUY',
        'industry': 'Technology',
        'tcbs_recommend': 'Buy'
    },
    {
        'ticker': 'GOOGL',
        'market_cap': 1800000000000,
        'roe': 0.28,
        'pe': 25.3,
        'pb': 5.4,
        'dividend_yield': 0.0,
        'revenue_growth_1y': 0.06,
        'eps_growth_1y': 0.15,
        'gross_margin': 0.56,
        'net_margin': 0.21,
        'beta': 1.1,
        'rsi14': 48,
        'stock_rating': 'HOLD',
        'industry': 'Technology',
        'tcbs_recommend': 'Hold'
    }
]


class StockComparisonState(rx.State):
    stocks: List[Dict[str, Any]] = sample_stocks
    selected_metrics: List[str] = [
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
        higher_better = ['market_cap', 'roe', 'dividend_yield', 'revenue_growth_1y',
                         'eps_growth_1y', 'gross_margin', 'net_margin']

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
        elif key in ['roe', 'dividend_yield', 'revenue_growth_1y', 'eps_growth_1y', 'gross_margin', 'net_margin']:
            return f"{value*100:.1f}%"
        elif key in ['pe', 'pb', 'beta']:
            return f"{value:.2f}"
        elif key == 'rsi14':
            return f"{value:.0f}"
        else:
            return str(value)


def stock_header_card(stock: Dict[str, Any]) -> rx.Component:
    """Create header card for each stock"""
    return rx.card(
        rx.vstack(
            rx.text(
                stock['ticker'],
                size="6",
                weight="bold",
                color=rx.color("blue", 11)
            ),
            rx.text(
                stock['industry'],
                size="2",
                color=rx.color("gray", 11)
            ),
            rx.badge(
                stock['stock_rating'],
                color_scheme=rx.cond(
                    stock['stock_rating'] == 'BUY',
                    'green',
                    rx.cond(
                        stock['stock_rating'] == 'SELL',
                        'red',
                        'gray'
                    )
                ),
                size="2"
            ),
            rx.text(
                stock['tcbs_recommend'],
                size="1",
                color=rx.color("gray", 10)
            ),
            spacing="2",
            align="center"
        ),
        padding="1.2em",
        width="180px",
        min_height="140px"
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
                width="200px",
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
                                StockComparisonState.best_performers[metric_key] == index,
                                "bold",
                                "medium"
                            ),
                            color=rx.cond(
                                StockComparisonState.best_performers[metric_key] == index,
                                rx.color("green", 11),
                                rx.color("gray", 11)
                            )
                        ),
                        width="180px",
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
        margin_bottom="2px",
        width="100%"
    )


def stock_headers() -> rx.Component:
    """Create the header row with all stock information"""
    return rx.hstack(
        # Empty space for metric labels column
        rx.box(width="200px"),
        # Stock header cards
        rx.hstack(
            rx.foreach(
                StockComparisonState.stocks,
                stock_header_card
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


def header_section() -> rx.Component:
    """Page header with title and info"""
    return rx.vstack(
        rx.hstack(
            rx.text(
                "Stock Comparison Dashboard",
                size="8",
                weight="bold",
                color=rx.color("gray", 12)
            ),
            rx.spacer(),
            rx.badge(
                "Comparing stocks",
                color_scheme="blue",
                size="2"
            ),
            width="100%"
        ),
        rx.separator(),
        spacing="4",
        margin_bottom="2em",
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


@rx.page(route="/analyze")
def index() -> rx.Component:
    """Main page component"""
    return rx.container(
        rx.vstack(
            header_section(),
            comparison_section(),
            legend_section(),
            spacing="4",
            width="100%",
            padding="2em"
        ),
        size="4"
    )
