"""State for stock comparison functionality."""

import reflex as rx
import pandas as pd
from sqlalchemy import text
from typing import List, Dict, Any
from collections import defaultdict
from ..utils.scheduler import db_settings


class StockComparisonState(rx.State):
    """State for comparing multiple stocks side by side."""

    stocks: List[Dict[str, Any]] = []
    compare_list: List[str] = []
    selected_metrics: List[str] = [
        "roe",
        "pe",
        "pb",
        "dividend_yield",
        "gross_margin",
        "net_margin",
        "rsi14",
    ]

    @rx.var
    def available_metrics(self) -> List[str]:
        """All available metrics that can be selected."""
        return [
            "roe",
            "roa",
            "pe",
            "pb",
            "ps",
            "ev_ebitda",
            "dividend_yield",
            "gross_margin",
            "net_margin",
            "doe",
            "alpha",
            "beta",
            "eps",
            "rsi14",
        ]

    @rx.var
    def metric_labels(self) -> Dict[str, str]:
        """Get human-readable labels for metrics."""
        return {
            "roe": "ROE",
            "roa": "ROA",
            "pe": "P/E Ratio",
            "pb": "P/B Ratio",
            "ps": "P/S Ratio",
            "ev_ebitda": "EV/EBITDA",
            "dividend_yield": "Dividend Yield",
            "gross_margin": "Gross Margin",
            "net_margin": "Net Margin",
            "doe": "DOE",
            "alpha": "Alpha",
            "beta": "Beta",
            "eps": "EPS",
            "rsi14": "RSI (14)",
        }

    @rx.var
    def grouped_stocks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group formatted stocks by industry."""
        groups = defaultdict(list)
        for stock in self.formatted_stocks:
            industry = stock.get("industry", "Unknown")
            groups[industry].append(stock)
        return dict(groups)

    @rx.var
    def formatted_stocks(self) -> List[Dict[str, Any]]:
        """Pre-format all stock values for display."""
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
        """Calculate best performer for each metric within each industry."""
        industry_best = {}
        higher_better = [
            "roe",
            "roa",
            "dividend_yield",
            "gross_margin",
            "net_margin",
            "alpha",
            "eps",
        ]
        lower_better = ["pe", "pb", "ps", "ev_ebitda", "beta", "doe"]

        for industry, stocks in self.grouped_stocks.items():
            industry_best[industry] = {}

            for metric in self.selected_metrics:
                values = []
                for stock in stocks:
                    original_stock = next(
                        (
                            s
                            for s in self.stocks
                            if s.get("symbol") == stock.get("symbol")
                        ),
                        None,
                    )
                    if original_stock:
                        val = original_stock.get(metric)
                        if val is not None and isinstance(val, (int, float)):
                            values.append((val, stock.get("symbol")))

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
        """Format values for display."""
        if value is None:
            return "N/A"

        if key == "market_cap":
            return f"{value}B VND"
        elif key in [
            "roe",
            "roa",
            "dividend_yield",
            "gross_margin",
            "net_margin",
            "doe",
        ]:
            return f"{value:.1f}%"
        elif key in ["pe", "pb", "ps", "ev_ebitda", "alpha", "beta", "eps"]:
            return f"{value:.2f}"
        elif key == "rsi14":
            return f"{value:.0f}"
        else:
            return str(value)

    @rx.event
    def toggle_metric(self, metric: str):
        """Toggle a metric in the selected_metrics list."""
        if metric in self.selected_metrics:
            self.selected_metrics = [m for m in self.selected_metrics if m != metric]
        else:
            self.selected_metrics = self.selected_metrics + [metric]

    @rx.event
    def select_all_metrics(self):
        """Select all available metrics."""
        self.selected_metrics = self.available_metrics.copy()

    @rx.event
    def clear_all_metrics(self):
        """Clear all selected metrics."""
        self.selected_metrics = []

    @rx.event
    def remove_stock_from_compare(self, ticker: str):
        """Remove a stock from comparison list."""
        self.compare_list = [t for t in self.compare_list if t != ticker]
        self.stocks = [s for s in self.stocks if s.get("symbol") != ticker]

    @rx.event
    async def import_cart_to_compare(self):
        """Import tickers from cart to comparison list."""
        # Import here to avoid circular dependency
        from ..state import CartState

        cart_state = await self.get_state(CartState)
        tickers = [item["name"] for item in cart_state.cart_items]
        self.compare_list = tickers

    @rx.event
    async def fetch_stocks_from_compare(self):
        """Fetch stock data for tickers in compare_list from database."""
        tickers = self.compare_list
        stocks = []
        if not tickers or not db_settings.conn:
            self.stocks = []
            return

        for ticker in tickers:
            try:
                overview_query = text(
                    "SELECT symbol, industry, market_cap "
                    "FROM tickers.overview_df WHERE symbol = :symbol"
                )
                overview_df = pd.read_sql(
                    overview_query, db_settings.conn, params={"symbol": ticker}
                )

                stats_query = text(
                    "SELECT symbol, roe, roa, ev_ebitda, dividend_yield, "
                    "gross_margin, net_margin, doe, alpha, beta, pe, pb, eps, ps, rsi14 "
                    "FROM tickers.stats_df WHERE symbol = :symbol"
                )
                stats_df = pd.read_sql(
                    stats_query, db_settings.conn, params={"symbol": ticker}
                )

                if not overview_df.empty and not stats_df.empty:
                    stock_data = {
                        "symbol": ticker,
                        "industry": overview_df.iloc[0]["industry"],
                        "market_cap": overview_df.iloc[0]["market_cap"],
                        "roe": stats_df.iloc[0]["roe"],
                        "roa": stats_df.iloc[0]["roa"],
                        "ev_ebitda": stats_df.iloc[0]["ev_ebitda"],
                        "dividend_yield": stats_df.iloc[0]["dividend_yield"],
                        "gross_margin": stats_df.iloc[0]["gross_margin"],
                        "net_margin": stats_df.iloc[0]["net_margin"],
                        "doe": stats_df.iloc[0]["doe"],
                        "alpha": stats_df.iloc[0]["alpha"],
                        "beta": stats_df.iloc[0]["beta"],
                        "pe": stats_df.iloc[0]["pe"],
                        "pb": stats_df.iloc[0]["pb"],
                        "eps": stats_df.iloc[0]["eps"],
                        "ps": stats_df.iloc[0]["ps"],
                        "rsi14": stats_df.iloc[0]["rsi14"],
                    }
                    stocks.append(stock_data)
            except Exception as e:
                print(f"Error fetching data for {ticker}: {e}")
                continue

        self.stocks = stocks

    @rx.event
    async def import_and_fetch_compare(self):
        """Import tickers from cart and fetch their stock data."""
        await self.import_cart_to_compare()
        await self.fetch_stocks_from_compare()
