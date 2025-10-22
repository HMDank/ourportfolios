from .preprocess_texts import process_events_for_display
from .scheduler import db_scheduler, db_settings
from sqlalchemy import text
import pandas as pd
import numpy as np
from datetime import date, timedelta
from vnstock import Vnstock, Screener, Trading, Company
import time
import asyncio
from tqdm import tqdm
import warnings

warnings.filterwarnings("ignore")


@db_scheduler.scheduled_job(
    trigger="interval", seconds=db_settings.interval, id="populate_db"
)
def populate_db():
    with db_settings.conn.connect() as connection:
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS overview"))
        connection.commit()

    screener = Screener(source="TCBS")
    default_params = {
        "exchangeName": "HOSE,HNX",
        "marketCap": (2000, 99999999999),
    }
    df = screener.stock(default_params, limit=1700, lang="en")

    # Remove unstable columns
    df = df.drop([x for x in df.columns if x.startswith("price_vs")], axis=1)
    ticker_list = df["ticker"].tolist()

    overview_list = []

    for ticker in tqdm(ticker_list, desc="Fetching company data"):
        overview = Company("TCBS", ticker).overview()
        if overview is not None and not overview.empty:
            overview_list.append(overview)
        time.sleep(0.5)

    overview_df = pd.concat(overview_list, ignore_index=True).drop(
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
    price_board_df = load_price_board(tickers=ticker_list)[
        ["symbol", "pct_price_change"]
    ]

    result = pd.merge(
        left=overview_df, right=price_board_df, left_on="symbol", right_on="symbol"
    )

    result.to_sql(
        "overview_df",
        db_settings.conn,
        schema="overview",
        if_exists="replace",
        index=False,
    )


def load_price_board(tickers: list[str]) -> pd.DataFrame:
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

    return df


def load_historical_data(
    symbol,
    start=date.today().strftime("%Y-%m-%d"),
    end=(date.today() + timedelta(days=1)).strftime("%Y-%m-%d"),
    interval="15m",
) -> pd.DataFrame:
    stock = Vnstock().stock(symbol=symbol, source="TCBS")
    df = stock.quote.history(start=start, end=end, interval=interval)
    return df.drop_duplicates(keep="last")


def load_income_statement(ticker: str):
    stock = Vnstock().stock(symbol=ticker, source="TCBS")
    finance = stock.finance
    income_statement = finance.income_statement(period="year").reset_index()
    return income_statement.to_dict("records")


def load_balance_sheet(ticker: str):
    stock = Vnstock().stock(symbol=ticker, source="TCBS")
    finance = stock.finance
    balance_sheet = finance.balance_sheet(period="year").reset_index()
    return balance_sheet.to_dict("records")


def load_cash_flow(ticker: str):
    stock = Vnstock().stock(symbol=ticker, source="TCBS")
    finance = stock.finance
    cash_flow = finance.cash_flow(period="year").reset_index()
    return cash_flow.to_dict("records")


async def load_company_data_async(ticker: str):
    tasks = [
        asyncio.to_thread(load_company_overview, ticker),
        asyncio.to_thread(load_company_shareholders, ticker),
        asyncio.to_thread(load_company_events, ticker),
        asyncio.to_thread(load_company_news, ticker),
        asyncio.to_thread(load_company_profile, ticker),
        asyncio.to_thread(load_officers_info, ticker),
        asyncio.to_thread(load_historical_data, ticker),
    ]
    (
        overview,
        shareholders,
        events,
        news,
        profile,
        officers,
        price_data,
    ) = await asyncio.gather(*tasks)
    return {
        "overview": overview,
        "shareholders": shareholders,
        "events": events,
        "profile": profile,
        "news": news,
        "officers": officers,
        "price_data": price_data,
    }


if __name__ == "__main__":
    populate_db()
