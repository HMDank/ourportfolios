import reflex as rx
import pandas as pd
from typing import List, Dict, Any
from datetime import date
from dateutil.relativedelta import relativedelta
import json

from ..utils.compute_instrument import compute_ma, compute_rsi
from ..utils.load_data import load_historical_data


# Price chart State
class PriceChartState(rx.State):
    df: pd.DataFrame = pd.DataFrame()
    selected_chart: str = "Candlestick"
    selected_ma_period: Dict[str, bool] = {}
    rsi_line: bool = False

    ma_period: List[str] = ["5", "10", "20", "50", "100", "200"]
    rsi_period: int = 14

    @rx.event
    def load_chart_data(self):
        """An event to refresh/recall historical data given new ticker"""
        ticker: str = self.router.page.params.get("ticker", "")
        self.df: pd.DataFrame = load_historical_data(
            symbol=ticker,
            start=(date.today() - relativedelta(months=3)).strftime("%Y-%m-%d"),
            end=(date.today() + relativedelta(days=1)).strftime("%Y-%m-%d"),
            interval="1D",
        )
        yield rx.call_script(
            f"""render_price_chart({self.chart_layout}, {self.chart_options})"""
        )

    @rx.event
    def load_chart_options(self):
        # Loads MA options
        self.selected_ma_period = {item: False for item in self.ma_period}

    @rx.event
    def set_selection(self):
        if self.selected_chart == "Candlestick":
            self.selected_chart = "Price"
        else:
            self.selected_chart = "Candlestick"
        yield rx.call_script(
            f"""render_price_chart({self.chart_layout}, {self.chart_options})"""
        )

    @rx.event
    def add_ma_period(self, value: bool, period: str):
        self.selected_ma_period[period] = value
        yield rx.call_script(
            f"""render_price_chart({self.chart_layout}, {self.chart_options})"""
        )

    @rx.event
    def add_rsi_line(self):
        if not self.rsi_line:
            self.rsi_line = True
        else:
            self.rsi_line = False
        yield rx.call_script(
            f"""render_price_chart({self.chart_layout}, {self.chart_options})"""
        )

    @rx.var
    def ohlc_data(self) -> List[Dict[str, Any]]:
        """Return a list of {time, open, high, low, close}"""
        if self.df.empty:
            return []

        df2 = self.df.copy()
        if "time" not in self.df.columns:
            df2 = df2.reset_index()

        df2["time"] = df2["time"].apply(lambda x: x.strftime("%Y-%m-%d"))
        return df2.to_dict("records")

    @rx.var
    def price_data(self) -> List[Dict[str, Any]]:
        """Return a list of {time, value } from 'close'"""
        if (self.df.empty) or (not {"time", "close"}.issubset(self.df.columns)):
            return []

        df2 = self.df[["time", "close"]].rename(columns={"close": "value"})
        df2["time"] = df2["time"].apply(lambda x: x.strftime("%Y-%m-%d"))
        return df2.dropna(how="any", axis=0).to_dict("records")

    @rx.var
    def ma_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """If ma_period > 0, compute MA"""
        if self.df.empty:
            return {}

        df2 = self.df.copy()
        if "time" not in df2.columns:
            df2 = df2.reset_index()

        ma_data = {
            period: compute_ma(df2, ma_period=int(period))
            for period, state in self.selected_ma_period.items()
            if state
        }
        return ma_data

    @rx.var
    def rsi_data(self) -> List[Dict[str, Any]]:
        """If rsi_period > 0, compute RSI"""
        if self.df.empty or not self.rsi_line:
            return []

        df2 = self.df.copy()
        if "time" not in df2.columns:
            df2 = df2.reset_index()
        return compute_rsi(df2, self.rsi_period)

    @rx.var
    def chart_options(self) -> str:
        """Summarize chart settings"""
        # Price
        price_data = (
            self.ohlc_data if self.selected_chart == "Candlestick" else self.price_data
        )
        # MA line
        ma_line_data = self.ma_data
        # RSI line
        rsi_line_data = self.rsi_data

        options: Dict[str, Any] = {
            "type": self.selected_chart,
            "price_data": price_data,
            "ma_line_data": ma_line_data,
            "rsi_line_data": rsi_line_data,
        }

        return json.dumps(options)

    # Chart layout
    @rx.var
    def chart_layout(self) -> str:
        """Return chart configurations"""
        # Default
        options = {
            "layout": {
                "background": {"type": "solid", "color": "#131722"},
                "textColor": "#d1d4dc",
            },
            "grid": {
                "horzLines": {"color": "#2a2e36"},
                "vertLines": {"color": "#2a2e36"},
            },
            "priceScale": {
                "scaleMargins": {"top": 0.2, "bottom": 0.25},
                "borderVisible": False,
            },
            "overlayPriceScales": {
                "scaleMargins": {"top": 0.7, "bottom": 0},
            },
            "timeScale": {
                "borderColor": "#cccccc",
                "rightOffset": 10,
                "barSpacing": 12,
                "lockVisibleTimeRangeOnResize": True,
            },
        }
        return json.dumps(options)


def render_price_chart():
    return rx.card(
        rx.flex(
            rx.script(
                src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js",
            ),
            rx.script(src="/chart.js"),
            rx.box(id="price_chart", width="60vw", height="25vw"),
            rx.flex(
                rx.button(
                    rx.icon(
                        rx.cond(
                            PriceChartState.selected_chart == "Candlestick",
                            "chart-candlestick",
                            "chart-spline",
                        ),
                        size=15,
                    ),
                    variant="outline",
                    on_click=PriceChartState.set_selection,
                ),
                rx.menu.root(
                    rx.menu.trigger(rx.button("MA", variant="outline")),
                    rx.menu.content(
                        rx.vstack(
                            rx.foreach(
                                PriceChartState.selected_ma_period.items(),
                                lambda item: rx.checkbox(
                                    rx.badge(f"MA{item[0]}"),
                                    checked=item[1],
                                    on_change=lambda value: PriceChartState.add_ma_period(
                                        value, item[0]
                                    ),
                                ),
                            ),
                            spacing="3",
                        )
                    ),
                    modal=False,
                ),
                rx.button(
                    "RSI",
                    variant=rx.cond(PriceChartState.rsi_line, "solid", "outline"),
                    on_click=PriceChartState.add_rsi_line,
                ),
                direction="column",
                spacing="3",
            ),
            width="100%",
            height="100%",
            direction="row",
            spacing="3",
        ),
    )
