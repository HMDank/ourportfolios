import reflex as rx
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import date, timedelta
import json

from ..utils.compute_instrument import compute_ma, compute_rsi
from ..utils.load_data import load_historical_data


# Price chart State
class PriceChartState(rx.State):
    df: List[Dict[str, Any]] = []
    chart_selection: str = "Candlestick"
    ma_period: int = 200
    rsi_period: int = 14
    selections: List[str] = ['Candlestick', 'Price', 'Return']
    show_chart: bool = True
    
    @rx.event
    def load_data(self):
        """An event to refresh/recall historical data given new ticker"""
        ticker: str = self.router.page.params.get("ticker","")
        chart_data: pd.DataFrame = load_historical_data(symbol=ticker, 
                                       start=(date.today() - timedelta(days=365)).strftime("%Y-%m-%d"), 
                                       end=(date.today()+ timedelta(days=1)).strftime("%Y-%m-%d"), 
                                       interval="1D")
        
        if not chart_data.empty: self.set_df(chart_data.to_dict("records"))
        
    @rx.event
    def set_selection(self, selection: str):
        self.chart_selection  = selection

    @rx.var
    def ohlc_data(self) -> pd.DataFrame:
        """Return a dataframe of {time, open, high, low, close}"""
        if not self.df:
            return pd.DataFrame(columns=["time","open","high","low","close"])
        
        df = pd.DataFrame(self.df)
        if "time" not in df.columns: df2 = df.reset_index()
        else: df2 = df.copy()
        return df2

    @rx.var
    def price_data(self) -> pd.DataFrame:
        """Return a list of {time, value } from 'close'"""
        if not self.df:
            return pd.DataFrame(columns=["time", "close"])
        
        df = pd.DataFrame(self.df)
        if not {"time","close"}.issubset(df.columns):
            return []
        tmp = df[["time","close"]].rename(columns={"close":"value"})
        return tmp.dropna(how="any", axis=0)
    
    @rx.var
    def returns_data(self) -> pd.DataFrame:
        """Return % returns as {time, value, }"""
        if not self.df:
            return pd.DataFrame(columns=["time", "close"])
        
        df = pd.DataFrame(self.df)
        if "time" not in df.columns: df2 = df.reset_index()
        else: df2 = df.copy()
        
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
    
    @rx.event
    def chartOptions(self) -> rx.Component:
        if self.show_chart:
            json_props: Dict[str, Any] = json.dumps(my_options)
            json_data = json.dumps(temp_data)
            json_script = f"""
                // Find the chart container
                const container = document.getElementById('chart');
                // Create the chart
                const chart = LightweightCharts.createChart(container,{json_props});

                // Add a line series and set sample data
                const seriesOptions = {{
                    "upColor": "#2ECC71",
                    "downColor": "#E74C3C",
                    "borderUpColor": "#2ECC71",
                    "borderDownColor": "#E74C3C",
                    "wickUpColor": "#2ECC71",
                    "wickDownColor": "#E74C3C",
                    "borderVisible": false,
                }}
                const candleSeries = chart.addSeries(LightweightCharts.CandlestickSeries, seriesOptions);
                candleSeries.setData({json_data});
                """      
                    
            return rx.call_script(json_script)
        return rx.call_script(f"""""")
    
    # Chart configurations 
    @rx.var
    def chart_configs(self) -> Dict[str, Any]:
        """Return configurations for candlestick chart """
        if self.chart_selection == 'Candlestick':
            options = {
                "height": 600,
                "layout": {
                    "background": { "type": "solid", "color": "#131722" },
                    "textColor": "#d1d4dc",
                },
                "grid": {
                    "horzLines":   { "color": '#2a2e36' },
                    "vertLines":   { "color": '#2a2e36' },
                },
                "rightPriceScale": {
                    "scaleMargins": { "top": 0.2, "bottom": 0.25 },
                    "borderVisible": False,
                },
                "overlayPriceScales": {
                    "scaleMargins": { "top": 0.7, "bottom": 0 },
                },
                
                "candlestickSeries":{
                    'data':[
                        { 'time': '2018-10-19', 'open': 180.34, 'high': 180.99, 'low': 178.57, 'close': 179.85 },
                        { 'time': '2018-10-22', 'open': 180.82, 'high': 181.40, 'low': 177.56, 'close': 178.75 },
                        { 'time': '2018-10-23', 'open': 175.77, 'high': 179.49, 'low': 175.44, 'close': 178.53 },
                        { 'time': '2018-10-24', 'open': 178.58, 'high': 182.37, 'low': 176.31, 'close': 176.97 },
                        { 'time': '2018-10-25', 'open': 177.52, 'high': 180.50, 'low': 176.83, 'close': 179.07 },
                        { 'time': '2018-10-26', 'open': 176.88, 'high': 177.34, 'low': 170.91, 'close': 172.23 },
                        { 'time': '2018-10-29', 'open': 173.74, 'high': 175.99, 'low': 170.95, 'close': 173.20 },
                        { 'time': '2018-10-30', 'open': 173.16, 'high': 176.43, 'low': 172.64, 'close': 176.24 },
                        { 'time': '2018-10-31', 'open': 177.98, 'high': 178.85, 'low': 175.59, 'close': 175.88 },
                        { 'time': '2018-11-01', 'open': 176.84, 'high': 180.86, 'low': 175.90, 'close': 180.46 },
                        { 'time': '2018-11-02', 'open': 182.47, 'high': 183.01, 'low': 177.39, 'close': 179.93 },
                        { 'time': '2018-11-05', 'open': 181.02, 'high': 182.41, 'low': 179.30, 'close': 182.19 }
                    ],
                    "upColor": "#2ECC71",
                    "downColor": "#E74C3C",
                    "borderUpColor": "#2ECC71",
                    "borderDownColor": "#E74C3C",
                    "wickUpColor": "#2ECC71",
                    "wickDownColor": "#E74C3C",
                    "borderVisible": False,
                }
            }
            return options




temp_data = [{ 'time': '2018-10-19', 'open': 180.34, 'high': 180.99, 'low': 178.57, 'close': 179.85 },
        { 'time': '2018-10-22', 'open': 180.82, 'high': 181.40, 'low': 177.56, 'close': 178.75 },
        { 'time': '2018-10-23', 'open': 175.77, 'high': 179.49, 'low': 175.44, 'close': 178.53 },
        { 'time': '2018-10-24', 'open': 178.58, 'high': 182.37, 'low': 176.31, 'close': 176.97 },
        { 'time': '2018-10-25', 'open': 177.52, 'high': 180.50, 'low': 176.83, 'close': 179.07 },
        { 'time': '2018-10-26', 'open': 176.88, 'high': 177.34, 'low': 170.91, 'close': 172.23 },
        { 'time': '2018-10-29', 'open': 173.74, 'high': 175.99, 'low': 170.95, 'close': 173.20 },
        { 'time': '2018-10-30', 'open': 173.16, 'high': 176.43, 'low': 172.64, 'close': 176.24 },
        { 'time': '2018-10-31', 'open': 177.98, 'high': 178.85, 'low': 175.59, 'close': 175.88 },
        { 'time': '2018-11-01', 'open': 176.84, 'high': 180.86, 'low': 175.90, 'close': 180.46 },
        { 'time': '2018-11-02', 'open': 182.47, 'high': 183.01, 'low': 177.39, 'close': 179.93 },
        { 'time': '2018-11-05', 'open': 181.02, 'high': 182.41, 'low': 179.30, 'close': 182.19 },]


# Price chart wrapper
class Chart(rx.Component):
    """Wrapper for qognicafinance/react-lightweight-charts Chart"""
    library = "lightweight-charts"
    # lib_dependencies = ["lightweight-charts", "fast-deep-equal", "react-dom"]
    tag = "createChart"
    is_default = True

    container = rx.el.div("chart")
    options: rx.Var[Dict[str, Any]]


my_options = {
    "height": 600,
    "layout": {
        "background": { "type": "solid", "color": "#131722" },
        "textColor": "#d1d4dc",
    },
    "grid": {
        "horzLines":   { "color": '#2a2e36' },
        "vertLines":   { "color": '#2a2e36' },
    },
    "rightPriceScale": {
        "scaleMargins": { "top": 0.2, "bottom": 0.25 },
        "borderVisible": False,
    },
    "overlayPriceScales": {
        "scaleMargins": { "top": 0.7, "bottom": 0 },
    },
}

def price_chart():
    json_props: Dict[str, Any] = json.dumps(my_options)
    json_data = json.dumps(temp_data)
    json_script = f"""
        // Find the chart container
        const container = document.getElementById('chart');
        // Create the chart
        const chart = LightweightCharts.createChart(container,{json_props});

        // Add a line series and set sample data
        const seriesOptions = {{
            "upColor": "#2ECC71",
            "downColor": "#E74C3C",
            "borderUpColor": "#2ECC71",
            "borderDownColor": "#E74C3C",
            "wickUpColor": "#2ECC71",
            "wickDownColor": "#E74C3C",
            "borderVisible": false,
        }}
        const candleSeries = chart.addSeries(LightweightCharts.CandlestickSeries, seriesOptions);
        candleSeries.setData({json_data});
        """
            
    return rx.fragment(
        rx.el.div(id="chart", style={"width": 1100}),
        rx.script(
            src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js",
            on_load=PriceChartState.chartOptions
        ),
        max_height=300,
    )

def render_price_chart():
    controls = rx.box(
        rx.vstack(
            rx.hstack(
                rx.foreach(
                    PriceChartState.selections,
                    lambda selection: rx.button(
                        selection,
                        on_click=PriceChartState.set_selection(selection),
                        variant=rx.cond(selection == PriceChartState.chart_selection, 'solid', 'outline')
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
                        value=PriceChartState.ma_period,
                        placeholder="e.g 200",
                        on_change=lambda value: PriceChartState.set_ma_period(rx.cond(value is not None, value.to(int), 0)),
                        style={"width": "5rem", "marginRight": "1rem"},
                    ),      
                ),
                rx.vstack(
                    rx.text("RSI: ", fontSize="sm", fontWeight="medium"),
                    rx.input(
                        title="RSI",
                        type="number",
                        min=0,
                        value=PriceChartState.rsi_period,
                        placeholder="e.g 14",
                        on_change=lambda value: PriceChartState.set_rsi_period(rx.cond(value is not None, value.to(int), 0)),
                        style={"width": "5rem"},
                    ),   
                )
            )
        ),
        style={"display": "flex", "alignItems": "center", "marginBottom": "1rem"},
    )

    return rx.box(
        controls,
        rx.box(
            price_chart(),
            style={ "width":  "100%", "position": "relative", "height": "400"}
        ),
    )
    
    