import pandas as pd
import numpy as np
from vnstock import Vnstock
from datetime import date, timedelta
import warnings
warnings.filterwarnings("ignore")


def load_historical_data(symbol,
                         start=date.today().strftime(
                             "%Y-%m-%d"),
                         end=(date.today() + timedelta(days=1)
                              ).strftime("%Y-%m-%d"),
                         interval="15m"):
    stock = Vnstock().stock(symbol=symbol, source='TCBS')
    df = stock.quote.history(start=start, end=end, interval=interval)
    return df


def get_mini_graph_data(df):
    if not np.issubdtype(df['time'].dtype, np.datetime64):
        df['time'] = pd.to_datetime(df['time'])

    time_rev = df['time'].values[::-1]
    latest_date = time_rev[0]
    prev_date = next(t for t in time_rev if t != latest_date)

    latest_mask = df['time'].values == latest_date
    prev_mask = df['time'].values == prev_date

    latest_df = df[latest_mask]
    prev_df = df[prev_mask]

    close_vals = latest_df['close'].values
    min_close = close_vals.min()
    max_close = close_vals.max()

    if max_close != min_close:
        normalized_close = (close_vals - min_close) / \
            (max_close - min_close)
    else:
        normalized_close = np.zeros_like(close_vals)

    latest_df = latest_df.assign(
        normalized_close=normalized_close).to_dict("records")

    last_close_today = close_vals[-1]
    last_close_prev = prev_df['close'].values[-1]
    percent_diff = round((last_close_today - last_close_prev) /
                         last_close_prev * 100, 2)

    return latest_df, percent_diff


def fetch_data_for_symbols(symbols: list[str]):
    graph_data = []
    for symbol in symbols:
        df = load_historical_data(symbol)
        scaled_data, percent_diff = get_mini_graph_data(
            df)
        graph_data.append({
            "label": symbol,
            "data": scaled_data,
            "percent_diff": percent_diff
        })
    return graph_data
