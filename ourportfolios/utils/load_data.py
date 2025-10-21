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
        "overview",
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


def get_mini_graph_data(df):
    if not np.issubdtype(df["time"].dtype, np.datetime64):
        df["time"] = pd.to_datetime(df["time"])

    time_rev = df["time"].values[::-1]
    latest_date = time_rev[0]
    prev_date = next(t for t in time_rev if t != latest_date)

    latest_mask = df["time"].values == latest_date
    prev_mask = df["time"].values == prev_date

    latest_df = df[latest_mask]
    prev_df = df[prev_mask]

    close_vals = latest_df["close"].values
    min_close = close_vals.min()
    max_close = close_vals.max()

    if max_close != min_close:
        normalized_close = (close_vals - min_close) / (max_close - min_close)
    else:
        normalized_close = np.zeros_like(close_vals)

    latest_df = latest_df.assign(normalized_close=normalized_close).to_dict("records")

    last_close_today = close_vals[-1]
    last_close_prev = prev_df["close"].values[-1]
    percent_diff = round(
        (last_close_today - last_close_prev) / last_close_prev * 100, 2
    )

    return latest_df, percent_diff


def load_company_overview(ticker: str):
    stock = Vnstock().stock(symbol=ticker, source="TCBS")
    company = stock.company
    overview = company.overview().iloc[0].to_dict()
    overview["website"] = (
        overview["website"].removeprefix("https://").removeprefix("http://")
    )
    overview["foreign_percent"] = round(overview["foreign_percent"] * 100, 2)
    return overview


def load_company_shareholders(ticker: str):
    stock = Vnstock().stock(symbol=ticker, source="TCBS")
    company = stock.company
    shareholders_df = company.shareholders()
    shareholders_df["share_own_percent"] = (
        shareholders_df["share_own_percent"] * 100
    ).round(2)
    shareholders = shareholders_df.to_dict("records")
    return shareholders


def load_company_profile(ticker: str):
    stock = Vnstock().stock(symbol=ticker, source="TCBS")
    company = stock.company
    profile = company.profile()
    profile = profile.to_dict("records")[0]
    return profile


def load_company_events(ticker: str):
    stock = Vnstock().stock(symbol=ticker, source="TCBS")
    company = stock.company
    events = company.events()
    events["price_change_ratio"] = (events["price_change_ratio"] * 100).round(2)
    events = events.to_dict("records")
    processed_events = process_events_for_display(events)
    return processed_events


def load_company_news(ticker: str):
    stock = Vnstock().stock(symbol=ticker, source="TCBS")
    company = stock.company
    news = company.news()
    news["price_change_ratio"] = pd.to_numeric(
        news["price_change_ratio"], errors="coerce"
    )
    news = news[~news["title"].str.contains("insider", case=False, na=False)]
    news["price_change_ratio"] = (news["price_change_ratio"] * 100).round(2)
    news = news.to_dict("records")
    return news


def load_officers_info(ticker: str):
    stock = Vnstock().stock(symbol=ticker, source="TCBS")
    company = stock.company
    officers = (
        company.officers()
        .dropna(subset=["officer_name"])
        .fillna("")
        .groupby("officer_name")
        .agg(
            {
                "officer_position": lambda x: ", ".join(
                    sorted(
                        set(
                            pos.strip()
                            for pos in x
                            if isinstance(pos, str) and pos.strip()
                        )
                    )
                ),
                "officer_own_percent": "first",
            }
        )
        .reset_index()
        .sort_values(by="officer_own_percent", ascending=False)
    )
    officers["officer_own_percent"] = (officers["officer_own_percent"] * 100).round(2)

    officers = officers.sort_values(by="officer_own_percent", ascending=False).to_dict(
        "records"
    )

    return officers


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
