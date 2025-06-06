import reflex as rx
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional

from ..utils.compute_instrument import compute_ma, compute_rsi

# Price chart wrapper
class Chart(rx.Component):
    """Wraps the <Chart> component from react-lightweight-charts-simple."""
    library = "react-lightweight-charts-simple"
    tag = "Chart"

    # These props map to the Chart’s React props:
    width: rx.Var[int]
    height: rx.Var[int]
    autoWidth: rx.Var[bool]
    autoHeight: rx.Var[bool]
    layout: rx.Var[Dict[str, Any]]
    grid: rx.Var[Dict[str, Any]]
    rightPriceScale: rx.Var[Dict[str, Any]]
    overlayPriceScales: rx.Var[Dict[str, Any]]
    timeScale: rx.Var[Dict[str, Any]]
    watermark: rx.Var[Dict[str, Any]]
    margin: rx.Var[Dict[str, Any]]

class CandlestickSeries(rx.Component):
    """Wraps the <CandlestickSeries> component."""
    library = "react-lightweight-charts-simple"
    tag = "CandlestickSeries"

    data: rx.Var[List[Dict[str, Any]]]
    options: rx.Var[Dict[str, Any]]

class LineSeries(rx.Component):
    """Wraps the <LineSeries> component (for MA or RSI)."""
    library = "react-lightweight-charts-simple"
    tag = "LineSeries"

    data: rx.Var[List[Dict[str, Any]]]
    options: rx.Var[Dict[str, Any]]

def compute_ma(df: pd.DataFrame, ma_period: int) -> List[Dict[str, Any]]:
    """Calculates the Moving Average (MA)."""
    df = df.copy()
    df["value"] = df["close"].rolling(window=ma_period).mean().round(2)
    return (
        df[["time", "value"]]
        .dropna(how="any", axis=0)
        .to_dict("records")
    )

def compute_rsi(df: pd.DataFrame, rsi_period: int) -> List[Dict[str, Any]]:
    """Calculates the Relative Strength Index (RSI)."""
    df = df.copy()
    df["diff"] = df["close"].diff()
    df["gains"] = np.where(df["diff"] > 0, df["diff"], 0)
    df["losses"] = np.where(df["diff"] < 0, abs(df["diff"]), 0)
    df["avg_gain"] = df["gains"].rolling(window=rsi_period).mean()
    df["avg_loss"] = df["losses"].rolling(window=rsi_period).mean()
    rs = np.where(df["avg_loss"] == 0, np.inf, df["avg_gain"] / df["avg_loss"])
    df["value"] = (100 - (100 / (1 + rs))).round(2)
    return (
        df[["time", "value"]]
        .dropna(how="any", axis=0)
        .to_dict("records")
    )

# Price chart State
class PriceChartState(rx.State):
    # stock_historical_data
    df: pd.DataFrame = pd.DataFrame(columns=["time", "open", "high", "low", "close"])  

    # User‐selectable options's selection', 'ma_period', 'rsi_period')
    chart_selection: str = "Candlestick"
    ma_period: int = 0
    rsi_period: int = 0
    selections: list[str] = ['Candlestick', 'Price', 'Return']
    
    @rx.event
    def load_data(self, df: pd.DataFrame):
        """
        An event to refresh/recall historical data given new ticker
        """
        self.df = df
        
    @rx.event
    def set_selection(self, selection: str):
        self.chart_selection  = selection

    @rx.var
    def ohlc_data(self) -> List[Dict[str, Any]]:
        """Return a list of {time, open, high, low, close}."""
        if "time" not in self.df.columns: df2 = self.df.reset_index()
        else: df2 = self.df.copy()
            
        return df2[["time", "open", "high", "low", "close"]].to_dict("records")

    @rx.var
    def price_data(self) -> List[Dict[str, Any]]:
        """Return a list of {time, value} from 'close'."""
        if "time" not in self.df.columns: df2 = self.df.reset_index()
        else: df2 = self.df.copy()
        tmp = df2[["time", "close"]].rename(columns={"close": "value"})
        
        return tmp.dropna(how="any", axis=0).to_dict("records")

    @rx.var
    def returns_data(self) -> List[Dict[str, Any]]:
        """Return % returns as {time, value}."""
        if "time" not in self.df.columns: df2 = self.df.reset_index()
        else: df2 = self.df.copy()
        
        tmp = df2[["time", "close"]].rename(columns={"close": "value"})
        tmp["value"] = tmp["value"].pct_change()
        
        return tmp.dropna(how="any", axis=0).to_dict("records")

    @rx.var
    def ma_data(self) -> Optional[List[Dict[str, Any]]]:
        """If ma_period > 0, compute MA."""
        if self.ma_period > 0:
            df2 = self.df.copy()
            if "time" not in df2.columns:
                df2 = df2.reset_index()
            return compute_ma(df2, self.ma_period)
        
        return None

    @rx.var
    def rsi_data(self) -> Optional[List[Dict[str, Any]]]:
        """If rsi_period > 0, compute RSI."""
        if self.rsi_period > 0:
            df2 = self.df.copy()
            if "time" not in df2.columns:
                df2 = df2.reset_index()
            return compute_rsi(df2, self.rsi_period)
        return None

    # Chart configurations 
    @rx.var
    def chart_configs(self) -> Dict[str, Any]:
        """
        Return a dict containing all props needed for:
          - Chart (layout, grid, scales, etc.)
          - A list of series (each with type/data/options)
        """
        # Base layout shared by candlestick and line‐only charts
        common_layout = {
            "background": { "type": "solid", "color": "#131722" },
            "textColor": "#d1d4dc",
        }
        common_grid = {
            "vertLines": { "color": "rgba(42,46,57,0)" },
            "horzLines": { "color": "rgba(42,46,57,0.6)" },
        }

        if self.chart_selection == "Candlestick":
            # The “container” / Chart‐level props
            chart_props = {
                "height": 600,
                "layout": common_layout,
                "grid": common_grid,
                "rightPriceScale": {
                    "scaleMargins": { "top": 0.2, "bottom": 0.25 },
                    "borderVisible": False,
                },
                "overlayPriceScales": {
                    "scaleMargins": { "top": 0.7, "bottom": 0 },
                },
            }

            candle_series = {
                "type": "Candlestick",
                "data": self.ohlc_data,
                "options": {
                    "upColor": "#2ECC71",
                    "downColor": "#E74C3C",
                    "borderUpColor": "#2ECC71",
                    "borderDownColor": "#E74C3C",
                    "wickUpColor": "#2ECC71",
                    "wickDownColor": "#E74C3C",
                    "borderVisible": False,
                },
            }

            series_list = [candle_series]

            # If MA is requested, append a LineSeries config
            if self.ma_data:
                ma_series = {
                    "type": "Line",
                    "data": self.ma_data,
                    "options": {
                        "color": "#007bff",
                        "lineWidth": 1,
                        "lineStyle": 0,
                        "priceLineVisible": False,
                        "lastValueVisible": False,
                    },
                }
                series_list.append(ma_series)

            # If RSI is requested, render a SECONDARY chart below
            if self.rsi_data:
                rsi_chart_props = {
                    "height": 100,
                    "layout": common_layout,
                    "grid": {
                        "vertLines": { "color": "rgba(0,0,0,0)" },
                        "horzLines": { "color": "rgba(0,0,0,0.1)" },
                    },
                    "timeScale": { "visible": False },
                    "watermark": {
                        "visible": True,
                        "fontSize": 18,
                        "horzAlign": "left",
                        "vertAlign": "center",
                        "color": "rgba(171, 71, 188, 0.7)",
                        "text": "RSI",
                    },
                }
                rsi_series = {
                    "type": "Line",
                    "data": self.rsi_data,
                    "options": {
                        "color": "#B10DC9",
                        "lineWidth": 1,
                        "lineStyle": 0,
                        "priceLineVisible": False,
                        "lastValueVisible": False,
                    },
                }
                return {
                    "main": {"chart": chart_props, "series": series_list},
                    "rsi": {"chart": rsi_chart_props, "series": [rsi_series]},
                }

            return { "main": {"chart": chart_props, "series": series_list} }

        # ——— Price / Returns  ———
        else:
            chart_props = {
                "height": 600,
                "layout": { "background": { "type": "solid", "color": "#262730" }, "textColor": "#FFFFFF" },
                "grid": {
                    "vertLines": { "color": "rgba(255,255,255,0.1)" },
                    "horzLines": { "color": "rgba(255,255,255,0.1)" },
                },
                "rightPriceScale": { "borderColor": "rgba(255,255,255,0.3)" },
                "timeScale": { "borderColor": "rgba(255,255,255,0.3)" },
                "margin": { "top": 20, "bottom": 20, "left": 20, "right": 20 },
            }

            values = self.price_data if self.chart_selection == "Price" else self.returns_data
            series_list = [
                {
                    "type": "Line",
                    "data": values,
                    "options": {
                        "color": "#1f77b4",
                        "lineWidth": 1,
                        "lineStyle": 0,
                        "crossHairMarkerVisible": True,
                        "crossHairMarkerRadius": 3,
                        "crossHairMarkerBorderColor": "#FFFFFF",
                        "crossHairMarkerBackgroundColor": "#1f77b4",
                        "priceLineVisible": False,
                        "lastValueVisible": False,
                    },
                }
            ]
            return { "main": {"chart": chart_props, "series": series_list} }



class PriceChart(rx.Component):
    """Renders a single page with dropdowns/inputs to choose the mode, then shows one or two charts."""
    @rx.var
    def mode(self) -> str:
        return PriceChartState.chart_selection

    def render(self):
        # Controls: select mode, MA period, RSI period
        controls = rx.box(
            rx.hstack(
                rx.foreach(
                    PriceChartState.selections,
                    lambda selection: rx.button(
                        PriceChartState.selections,
                        variant=rx.cond(selection == PriceChartState.chart_selection, 'solide', 'outline')
                    )
                )  
            ),
            rx.input(
                type="number",
                min=0,
                value=PriceChartState.ma_period,
                placeholder="MA period",
                on_change=lambda value: PriceChartState.set_ma_period(rx.cond(value is not None, value.to(int), 0)),
                style={"width": "4rem", "marginRight": "1rem"},
            ),
            rx.input(
                type="number",
                min=0,
                value=PriceChartState.rsi_period,
                placeholder="RSI period",
                on_change=lambda value: PriceChartState.set_rsi_period(rx.cond(value is not None, value.to(int), 0)),
                style={"width": "4rem"},
            ),
            style={"display": "flex", "alignItems": "center", "marginBottom": "1rem"},
        )

        # Build charts based on selection mode
        main_chart = rx.cond(
            PriceChartState.chart_selection == "Candlestick",
            self._render_candlestick_chart(),
            self._render_line_chart()
        )

        rsi_chart = rx.cond(
            (PriceChartState.chart_selection == "Candlestick") & (PriceChartState.rsi_period > 0),
            self._render_rsi_chart(),
            rx.fragment()
        )

        return rx.box(
            controls,
            rx.box(
                main_chart,
                style={"display": "flex", "justifyContent": "center", "marginBottom": "1rem"},
            ),
            rx.box(
                rsi_chart,
                style={"display": "flex", "justifyContent": "center"},
            ),
        )

    def _render_candlestick_chart(self):
        """Render candlestick chart with optional MA overlay."""
        candlestick_series = CandlestickSeries.create(
            data=PriceChartState.ohlc_data,
            options={
                "upColor": "#2ECC71",
                "downColor": "#E74C3C",
                "borderUpColor": "#2ECC71",
                "borderDownColor": "#E74C3C",
                "wickUpColor": "#2ECC71",
                "wickDownColor": "#E74C3C",
                "borderVisible": False,
            },
        )

        ma_series = rx.cond(
            PriceChartState.ma_period > 0,
            LineSeries.create(
                data=PriceChartState.ma_data,
                options={
                    "color": "#007bff",
                    "lineWidth": 1,
                    "lineStyle": 0,
                    "priceLineVisible": False,
                    "lastValueVisible": False,
                },
            ),
            rx.fragment()
        )

        return Chart.create(
            candlestick_series,
            ma_series,
            height=600,
            layout={
                "background": { "type": "solid", "color": "#131722" },
                "textColor": "#d1d4dc",
            },
            grid={
                "vertLines": { "color": "rgba(42,46,57,0)" },
                "horzLines": { "color": "rgba(42,46,57,0.6)" },
            },
            rightPriceScale={
                "scaleMargins": { "top": 0.2, "bottom": 0.25 },
                "borderVisible": False,
            },
            overlayPriceScales={
                "scaleMargins": { "top": 0.7, "bottom": 0 },
            },
        )

    def _render_line_chart(self):
        """Render line chart for Price or Returns."""
        data = rx.cond(
            PriceChartState.chart_selection == "Price",
            PriceChartState.price_data,
            PriceChartState.returns_data
        )

        line_series = LineSeries.create(
            data=data,
            options={
                "color": "#1f77b4",
                "lineWidth": 1,
                "lineStyle": 0,
                "crossHairMarkerVisible": True,
                "crossHairMarkerRadius": 3,
                "crossHairMarkerBorderColor": "#FFFFFF",
                "crossHairMarkerBackgroundColor": "#1f77b4",
                "priceLineVisible": False,
                "lastValueVisible": False,
            },
        )

        return Chart.create(
            line_series,
            height=600,
            layout={
                "background": { "type": "solid", "color": "#262730" },
                "textColor": "#FFFFFF"
            },
            grid={
                "vertLines": { "color": "rgba(255,255,255,0.1)" },
                "horzLines": { "color": "rgba(255,255,255,0.1)" },
            },
            rightPriceScale={ "borderColor": "rgba(255,255,255,0.3)" },
            timeScale={ "borderColor": "rgba(255,255,255,0.3)" },
            margin={ "top": 20, "bottom": 20, "left": 20, "right": 20 },
        )

    def _render_rsi_chart(self):
        """Render RSI chart."""
        rsi_series = LineSeries.create(
            data=PriceChartState.rsi_data,
            options={
                "color": "#B10DC9",
                "lineWidth": 1,
                "lineStyle": 0,
                "priceLineVisible": False,
                "lastValueVisible": False,
            },
        )

        return Chart.create(
            rsi_series,
            height=100,
            layout={
                "background": { "type": "solid", "color": "#131722" },
                "textColor": "#d1d4dc",
            },
            grid={
                "vertLines": { "color": "rgba(0,0,0,0)" },
                "horzLines": { "color": "rgba(0,0,0,0.1)" },
            },
            timeScale={ "visible": False },
            watermark={
                "visible": True,
                "fontSize": 18,
                "horzAlign": "left",
                "vertAlign": "center",
                "color": "rgba(171, 71, 188, 0.7)",
                "text": "RSI",
            },
        )