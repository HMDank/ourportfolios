from vnstock import Company, Listing, Screener, Vnstock, Trading
from datetime import time, date, timedelta, datetime
import pandas as pd
import numpy as np
import sqlite3
from typing import List, Dict

def load_historical_data(symbol,
                         start=date.today().strftime(
                             "%Y-%m-%d"),
                         end=(date.today() + timedelta(days=1)
                              ).strftime("%Y-%m-%d"),
                         interval="15m"):
    stock = Vnstock().stock(symbol=symbol, source='TCBS')
    df = stock.quote.history(start=start, end=end, interval=interval)
    return df

def compute_ma(df: pd.DataFrame, ma_period: int):
    """Calculates the Moving Average (MA)."""
    df = df.copy()
    df["value"] = df["close"].rolling(window=ma_period).mean().round(2)
    return df[["time", "value"]].to_dict("records")

def load_price_board(tickers: List[str]) -> pd.DataFrame:
    price_board_df = Trading(source='vci', symbol='ACB').price_board(symbols_list=tickers)
    price_board_df.columns = price_board_df.columns.droplevel(0) # Flatten columns
    price_board_df = price_board_df.drop('exchange', axis=1) # Drop spare column to prevent duplicate column
    price_board_df = price_board_df.loc[:, ~price_board_df.columns.duplicated()]

    return price_board_df


def compute_instrument(df: pd.DataFrame) -> pd.DataFrame:
    # Changes in price
    if 'match_price' in df.columns:
        # Rename for better comprehension
        df = df.rename(columns={'match_price': 'current_price'})

        # latest close price - close price from previous day
        df['price_change'] = (df['current_price'] - df['ref_price'])
        df['pct_price_change'] = (df['price_change'] / df['ref_price']) * 100

    # On the day when the market is closed
    else:
        df = df.rename(columns={'ref_price': 'current_price'})
        df['price_change'] = 0
        df['pct_price_change'] = 0

    # Normalize
    df['current_price'] = round(df['current_price'] * 1e-3, 2)
    df['price_change'] = round(df['price_change'] * 1e-3, 2)
    df['pct_price_change'] = round(df['pct_price_change'], 2)

    return df


df = load_price_board(tickers=["AMV"])
df = compute_instrument(df)
print(df[['ref_price', 'current_price', 'price_change', 'pct_price_change']])
