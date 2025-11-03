"""Load and preprocess stock and company data.

This module provides utilities to fetch company data via vnstock (overview,
shareholders, events, news, profile, officers), preprocess those datasets,
load price boards and historical quotes, and populate the database on a
scheduled interval using the configured scheduler and database settings.
"""

import time
import warnings
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import text
from tqdm import tqdm
from vnstock import Screener, Trading, Vnstock

from .preprocess_texts import process_events_for_display
from .scheduler import db_scheduler, db_settings

warnings.filterwarnings("ignore")


@db_scheduler.scheduled_job(
    trigger="interval",
    seconds=db_settings.interval,
    id="populate_db",
    start_date=datetime.now() + timedelta(seconds=db_settings.interval),
)
def populate_db() -> None:
    with db_settings.conn.connect() as connection:
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS tickers"))
        connection.commit()

    stats_df = fetch_stats_df()
    ticker_list = stats_df["ticker"].to_list()

    overview_list = []
    shareholders_list = []
    events_list = []
    news_list = []
    profile_list = []
    officers_list = []

    for ticker in tqdm(ticker_list, desc="Fetching company data"):
        try:
            company = Vnstock().stock(symbol=ticker, source="TCBS").company

            overview = company.overview()
            shareholders = company.shareholders()
            events = company.events()
            news = company.news()
            profile = company.profile()
            officers_info = company.officers()

            if overview is not None and not overview.empty:
                market_cap_value = stats_df.loc[
                    stats_df["ticker"] == ticker,
                    "market_cap",
                ].squeeze()
                overview["market_cap"] = market_cap_value
                overview_list.append(overview)

            if shareholders is not None and not shareholders.empty:
                shareholders["symbol"] = ticker
                shareholders_list.append(shareholders)

            if events is not None and not events.empty:
                events["symbol"] = ticker
                events_list.append(events)

            if news is not None and not news.empty:
                news["symbol"] = ticker
                news_list.append(news)

            if profile is not None and not profile.empty:
                profile_list.append(profile)

            if officers_info is not None and not officers_info.empty:
                officers_info["symbol"] = ticker
                officers_list.append(officers_info)

            time.sleep(1)
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")  # noqa: T201
            continue

    overview_df = preprocess_overview(overview_list)
    shareholders_df = preprocess_shareholders(shareholders_list)
    events_df = preprocess_events(events_list)
    news_df = preprocess_news(news_list)
    profile_df = preprocess_profile(profile_list)
    officers_df = preprocess_officers(officers_list)

    overview_df.to_sql(
        "overview_df",
        db_settings.conn,
        schema="tickers",
        if_exists="replace",
        index=False,
    )

    shareholders_df.to_sql(
        "shareholders_df",
        db_settings.conn,
        schema="tickers",
        if_exists="replace",
        index=False,
    )

    events_df.to_sql(
        "events_df",
        db_settings.conn,
        schema="tickers",
        if_exists="replace",
        index=False,
    )

    news_df.to_sql(
        "news_df",
        db_settings.conn,
        schema="tickers",
        if_exists="replace",
        index=False,
    )

    profile_df.to_sql(
        "profile_df",
        db_settings.conn,
        schema="tickers",
        if_exists="replace",
        index=False,
    )

    officers_df.to_sql(
        "officers_df",
        db_settings.conn,
        schema="tickers",
        if_exists="replace",
        index=False,
    )

    stats_df.to_sql(
        "stats_df",
        db_settings.conn,
        schema="tickers",
        if_exists="replace",
        index=False,
    )

    price_df = load_price_df(ticker_list)
    price_df.to_sql(
        "price_df",
        db_settings.conn,
        schema="tickers",
        if_exists="replace",
        index=False,
    )


def preprocess_overview(overview_list: list) -> pd.DataFrame:
    df = pd.concat(overview_list, ignore_index=True)
    df["website"] = (
        df["website"].str.removeprefix("https://").str.removeprefix("http://")
    )
    df["foreign_percent"] = round(df["foreign_percent"] * 100, 2)
    df = df.drop(
        [
            "industry_id",
            "industry_id_v2",
            "delta_in_year",
            "delta_in_month",
            "delta_in_week",
            "stock_rating",
            "company_type",
        ],
        axis=1,
    )

    return df


def preprocess_shareholders(shareholders_list: list) -> pd.DataFrame:
    df = pd.concat(shareholders_list, ignore_index=True)
    df["share_own_percent"] = (df["share_own_percent"] * 100).round(2)
    return df


def preprocess_profile(profile_list: list) -> pd.DataFrame:
    df = pd.concat(profile_list, ignore_index=True)
    return df


def preprocess_events(events_list: list) -> pd.DataFrame:
    df = pd.concat(events_list, ignore_index=True)
    df["price_change_ratio"] = df["price_change_ratio"].fillna(np.nan)
    df["price_change_ratio"] = (df["price_change_ratio"] * 100).round(2)

    df = pd.DataFrame(process_events_for_display(df.to_dict("records")))
    df = df[["symbol", "event_name", "price_change_ratio", "event_desc"]]
    return df


def preprocess_news(news_list: list) -> pd.DataFrame:
    df = pd.concat(news_list, ignore_index=True)

    df["price_change_ratio"] = pd.to_numeric(df["price_change_ratio"], errors="coerce")
    df = df[~df["title"].str.contains("insider", case=False, na=False)]
    df["price_change_ratio"] = (df["price_change_ratio"] * 100).round(2)
    df = df[["symbol", "title", "publish_date", "price_change_ratio"]]
    return df


def preprocess_officers(officers_list: list) -> pd.DataFrame:
    df = pd.concat(officers_list, ignore_index=True)
    df = df.dropna(subset=["officer_name"])
    df = df.fillna("")
    df = (
        df.groupby(["symbol", "officer_name"])
        .agg(
            {
                "officer_position": lambda x: ", ".join(
                    sorted(
                        {
                            pos.strip()
                            for pos in x
                            if isinstance(pos, str) and pos.strip()
                        },
                    ),
                ),
                "officer_own_percent": "first",
            }
        )
        .reset_index()
    )
    df["officer_own_percent"] = pd.to_numeric(
        df["officer_own_percent"], errors="coerce"
    )
    df["officer_own_percent"] = (df["officer_own_percent"] * 100).round(2)
    df = df.sort_values(by="officer_own_percent", ascending=False)

    return df


def fetch_stats_df() -> list:
    screener = Screener(source="TCBS")
    default_params = {
        "exchangeName": "HOSE,HNX",
        "marketCap": (2000, 99999999999),
    }
    df = screener.stock(default_params, limit=1700, lang="en")
    return df[
        [
            "ticker",
            "roe",
            "roa",
            "ev_ebitda",
            "dividend_yield",
            "gross_margin",
            "net_margin",
            "doe",
            "alpha",
            "beta",
            "pe",
            "pb",
            "eps",
            "ps",
            "ev",
            "rsi14",
        ]
    ]


def load_price_df(tickers: list[str]) -> pd.DataFrame:
    df = Trading(source="vci", symbol="ACB").price_board(symbols_list=tickers)
    df.columns = df.columns.droplevel(0)
    df = df.drop("exchange", axis=1)
    df = df.loc[:, ~df.columns.duplicated()]

    # Compute instrument
    if "match_price" in df.columns:
        df = df.rename(columns={"match_price": "current_price"})
        df["price_change"] = df["current_price"] - df["ref_price"]
        df["pct_price_change"] = (df["price_change"] / df["ref_price"]) * 100

    else:
        df = df.rename(columns={"ref_price": "current_price"})
        df["price_change"] = 0
        df["pct_price_change"] = 0

    # Normalize
    df["current_price"] = round(df["current_price"] * 1e-3, 2)
    df["price_change"] = round(df["price_change"] * 1e-3, 2)
    df["pct_price_change"] = round(df["pct_price_change"], 2)

    return df[
        [
            "symbol",
            "current_price",
            "price_change",
            "pct_price_change",
            "accumulated_volume",
        ]
    ]


def load_historical_data(
    symbol,
    start=date.today().strftime("%Y-%m-%d"),
    end=(date.today() + timedelta(days=1)).strftime("%Y-%m-%d"),
    interval="15m",
) -> pd.DataFrame:
    stock = Vnstock().stock(symbol=symbol, source="TCBS")
    df = stock.quote.history(start=start, end=end, interval=interval)
    return df.drop_duplicates(keep="last")


def fetch_company_data(symbol: str) -> dict[dict]:
    """Fetch all company data tables for a given ticker from the tickers schema.

    Returns a dict with dataframes for each data type.
    """
    tables = [
        "overview",
        "shareholders",
        "events",
        "news",
        "profile",
        "officers",
        "price",
    ]

    result = {}

    try:
        for table in tables:
            try:
                df = pd.read_sql(
                    text(f"SELECT * FROM tickers.{table}_df WHERE symbol = :symbol"),
                    db_settings.conn,
                    params={"symbol": symbol},
                )
                result[table] = df if not df.empty else pd.DataFrame()
            except Exception as e:
                print(f"Error fetching {table} data for {symbol}: {e}")
                result[table] = pd.DataFrame()
    except Exception as e:
        print(f"Error fetching company data for {symbol}: {e}")
        # Return empty dataframes for all tables
        for table in tables:
            result[table] = pd.DataFrame()

    return result
