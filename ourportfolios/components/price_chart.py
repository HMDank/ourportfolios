import reflex as rx
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Any, Optional

from ..utils.compute_instrument import compute_ma, compute_rsi
from ..utils.load_data import load_historical_data


class Echarts(rx.Component):
    library = "echarts-for-react@3.0.2"
    lib_dependencies = ['fast-deep-equal', 'size-sensor']
    tag = "Reactecharts"
    is_default = True

    option: rx.Var[Dict[str, Any]]


# Price chart State
class PriceChartState(rx.State):
    df: list[dict[str, Any]] = []
    chart_selection: str = "Candlestick"
    ma_period: int = 200
    rsi_period: int = 14
    selections: list[str] = ['Candlestick', 'Price', 'Return']

    @rx.event
    def load_data(self):
        """An event to refresh/recall historical data given new ticker"""
        ticker: str = self.router.page.params.get("ticker","")
        chart_data: pd.DataFrame = load_historical_data(symbol=ticker,
                                       start=(date.today() - relativedelta(years=6)).strftime("%Y-%m-%d"),
                                       end=(date.today()+ relativedelta(days=1)).strftime("%Y-%m-%d"),
                                       interval="1D")
        if not chart_data.empty: self.set_df(chart_data.to_dict("records"))

    @rx.event
    def set_ma_period(self, value: int):
        if not value:
            value = 0
        self.ma_period = value
        self.chart_configs


    @rx.event
    def set_rsi_period(self, value: int):
        if not value:
            value = 0
        self.rsi_period = value
        self.chart_configs


    @rx.event
    def set_selection(self, selection: str):
        self.chart_selection = selection
        self.chart_configs

    @rx.var
    def ohlc_data(self) -> pd.DataFrame:
        """Return a dataframe of {time, open, high, low, close}"""
        if not self.df:
            return pd.DataFrame(columns=["time", "open", "high", "low", "close"])

        df = pd.DataFrame(self.df)
        if "time" not in df.columns:
            df2 = df.reset_index()
        else:
            df2 = df.copy()
        return df2

    @rx.var
    def price_data(self) -> pd.DataFrame:
        """Return a list of {time, value } from 'close'"""
        if not self.df:
            return pd.DataFrame(columns=["time", "close"])
        df = pd.DataFrame(self.df)
        if not {"time", "close"}.issubset(df.columns):
            return []
        tmp = df[["time", "close"]].rename(columns={"close": "value"})
        return tmp.dropna(how="any", axis=0)

    @rx.var
    def returns_data(self) -> pd.DataFrame:
        """Return % returns as {time, value, }"""
        if not self.df:
            return pd.DataFrame(columns=["time", "close"])
        df = pd.DataFrame(self.df)
        if "time" not in df.columns:
            df2 = df.reset_index()
        else:
            df2 = df.copy()

        tmp = df2[["time", "close"]].rename(columns={"close": "value"})
        tmp["value"] = tmp["value"].pct_change()

        return tmp.dropna(how="any", axis=0)

    @rx.var
    def ma_data(self) -> Optional[List[Dict[str, Any]]]:
        """If ma_period > 0, compute MA"""
        if not self.df or not self.ma_period:
            return []
        df = pd.DataFrame(self.df)
        if self.ma_period > 0:
            df2 = df.copy()
            if "time" not in df2.columns:
                df2 = df2.reset_index()
            return compute_ma(df2, self.ma_period)
        return None

    @rx.var
    def rsi_data(self) -> Optional[List[Dict[str, Any]]]:
        """If rsi_period > 0, compute RSI"""
        if not self.df or not self.rsi_period:
            return []
        df = pd.DataFrame(self.df)
        if self.rsi_period > 0:
            df2 = df.copy()
            if "time" not in df2.columns:
                df2 = df2.reset_index()
            return compute_rsi(df2, self.rsi_period)
        return None

    @rx.var
    def chartOptions(self) -> dict[str, Any]:
        return self.chart_configs

    # Chart configurations
    @rx.var
    def chart_configs(self) -> dict[str, Any]:
        if not self.df:
            return {}

        if self.chart_selection == 'Candlestick':
            df = self.ohlc_data
            data = df[['open', 'high', 'low', 'close']].values.tolist()

        elif self.chart_selection == 'Price':
            df = self.price_data
            data = df[['time', 'value']].values.tolist()

        elif self.chart_selection == 'Return':
            df = self.returns_data
            data = df[['time', 'value']].values.tolist()

        dates = df["time"].tolist()

        options = {
            "backgroundColor": "#0e0d14",
            "textStyle": {"color": "#ffffff"},
            "toolbox": {
                "feature": {
                    "dataZoom": {"yAxisIndex": False},
                    "saveAsImage": {},
                },
                "iconStyle": {"borderColor": "#777"},
            },
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {
                    "type": "cross",
                    "snap": True,
                    "label": {
                        "show": True,
                        "backgroundColor": "#222",
                    },
                    "formatter": (
                        "Date: {b0}<br/>"
                        "Open: {c0[0]} Close: {c0[1]}<br/>"
                        "Low: {c0[2]} High: {c0[3]}<br/>"
                        "MA10: {c1}<br/>"
                        "MA50: {c2}<br/>"
                        "Vol: {c3}"
                    ),
                },
                "backgroundColor": "#222",
                "borderColor": "#777",
                "borderWidth": 1,
                "textStyle": {"color": "#fff"},

            },
            "grid": [
                {"left": "6%", "right": "4%", "top": "4%",  "height": "70%"},  # price
                {"left": "6%", "right": "4%", "top": "85%", "height": "15%"}  # rsi
            ],
            "xAxis": [
                {
                    "type": "category",
                    "gridIndex": 0,
                    "data": dates,
                    "scale": True,
                    "boundaryGap": False,
                    "axisLine": {"lineStyle": {"color": "#888"}},
                    "axisLabel": {"color": "#ccc"},
                    "splitLine": {"show": False},
                    "axisPointer": {"z": 100},
                },
                # RSI
                {
                    "type": "category",
                    "gridIndex": 1,
                    "data": dates,
                    "axisLine": {"lineStyle": {"color": "#888"}},
                    "axisLabel": {"color": "#ccc"},
                    "axisTick": {"alignWithLabel": True},
                    "splitLine": {"show": False},
                },
            ],
            "yAxis": [
                {
                    "gridIndex": 0,
                    "scale": True,
                    "splitNumber": 5,
                    "axisLine": {"lineStyle": {"color": "#888"}},
                    "axisLabel": {"color": "#ccc"},
                    "splitLine": {"lineStyle": {"color": "#333"}},
                    "axisPointer": {
                        "label": {"show": True, "formatter": "{value}"}
                    }
                },
                # RSI
                {
                    "gridIndex": 1,
                    "scale": True,
                    "splitNumber": 3,
                    "axisLine": {"lineStyle": {"color": "#888"}},
                    "axisLabel": {"color": "#ccc"},
                    "splitLine": {"lineStyle": {"color": "#333"}},
                },
            ],
            "dataZoom": [
                {
                    "type": "inside",
                    "xAxisIndex": [0, 1],
                    "start": 60,
                    "end": 100,
                },
                {
                    "show": False,
                    "type": "slider",
                    "xAxisIndex": [0, 1],
                    "top": "92%",
                    "start": 60,
                    "end": 100,
                    "handleIcon": "M8.2,13.5H3.8V6.5h4.4V13.5z",
                    "handleSize": "100%",
                    "handleStyle": {"color": "#aaa"},
                    "borderColor": "#777",
                },
            ],
            "series": [
                {
                    "name": "Main-chart",
                    "type": "candlestick" if self.chart_selection == "Candlestick" else 'line',
                    "data": data,
                    "itemStyle": {
                        "color": "#26a69a",
                        "color0": "#ef5350",
                        "borderColor": "#26a69a",
                        "borderColor0": "#ef5350",
                    },
                    "barMaxWidth": "60%",
                    "markLine": {
                    "symbol": ["none", "none"],
                },
            }
        ],
    }
        
        # MA period
        ma_data = self.ma_data
        options['series'].append(
            {
                "name": f"MA{self.ma_period}",
                "type": "line",
                "data": ma_data,
                "smooth": True,
                "lineStyle": {"width": 1.5, "color": "#73bdf4"},
                "showSymbol": False,
                "connectNulls": False,
            },
        )

        rsi_data = self.rsi_data
        options["series"].append(
            {
                "name": f"RSI{self.rsi_period}", "type": "line",
                "xAxisIndex": 1, "yAxisIndex": 1,
                "data": rsi_data, "smooth": True,
                "lineStyle": {"width": 1.5, "color": "#f4d35e"},
                "showSymbol": False,
                "connectNulls": False,
                "markLine": {
                    "data": [
                        {"yAxis": 70, "lineStyle": {
                            "type": "dashed", "color": "#888"}},
                        {"yAxis": 30, "lineStyle": {
                            "type": "dashed", "color": "#888"}},
                    ]
                }
            },
        )

        return options


def render_price_chart():
    controls = rx.box(
        rx.vstack(
            rx.hstack(
                rx.foreach(
                    PriceChartState.selections,
                    lambda selection: rx.button(
                        selection,
                        on_click=PriceChartState.set_selection(selection),
                        variant=rx.cond(
                            selection == PriceChartState.chart_selection, 'solid', 'outline')
                    )
                )
            ),
            rx.hstack(
                rx.vstack(
                    rx.text("MA: ", fontSize="sm", fontWeight="medium"),
                    rx.input(
                        title="MA",
                        type="number",
                        min=0,
                        value=PriceChartState.ma_period.to(str),
                        placeholder="e.g 200",
                        on_change=lambda value: PriceChartState.set_ma_period(
                            rx.cond(value, value.to(int), None)),
                        style={"width": "5rem", "marginRight": "1rem"},
                    ),
                ),
                rx.vstack(
                    rx.text("RSI: ", fontSize="sm", fontWeight="medium"),
                    rx.input(
                        title="RSI",
                        type="number",
                        min=0,
                        value=PriceChartState.rsi_period.to(str),
                        placeholder="e.g 14",
                        on_change=lambda value: PriceChartState.set_rsi_period(
                            rx.cond(value, value.to(int), None)),
                        style={"width": "5rem"},
                    ),
                )
            )
        ),
        style={"display": "flex", "alignItems": "center", "marginBottom": "1rem"},
    )

    return rx.box(
        rx.box(
            Echarts.create(option=PriceChartState.chartOptions),
            style={
                "width": "65vw",
                "height": "50vh",
                "padding": "0",
                "margin": "0 auto",
            },
            on_mount=PriceChartState.load_data
        ),
    )
