import pandas as pd
import numpy as np
import sqlite3
from datetime import date, timedelta
from vnstock import Vnstock, Screener
import warnings
warnings.filterwarnings("ignore")

data_vni_loaded = False


def populate_db() -> None:
    global data_vni_loaded
    if data_vni_loaded:
        print("Data already loaded. Skipping.")
        return

    conn = sqlite3.connect("ourportfolios/data/data_vni.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='data_vni'")
    if cursor.fetchone():
        cursor.execute("SELECT COUNT(*) FROM data_vni")
        if cursor.fetchone()[0] > 0:
            print("Data already loaded. Skipping.")
            conn.close()
            data_vni_loaded = True
            return

    screener = Screener(source='TCBS')
    default_params = {
        'exchangeName': 'HOSE,HNX',
        'marketCap': (100, 99999999999),
    }
    df = screener.stock(default_params, limit=1700, lang='en')

    df.to_sql("data_vni", conn, if_exists="replace", index=False)
    conn.close()
    data_vni_loaded = True
    print("Data loaded successfully.")


if __name__ == "__main__":
    load_data_vni()


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
