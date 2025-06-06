import numpy as np
import pandas as pd

from typing import List, Dict, Any

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