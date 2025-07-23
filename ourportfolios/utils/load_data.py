from .preprocess_texts import process_events_for_display
import pandas as pd
import numpy as np
import sqlite3
from datetime import date, timedelta
from vnstock import Vnstock, Screener, Trading
import asyncio
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
        "SELECT name FROM sqlite_master WHERE type='table' AND name='data_vni'"
    )
    if cursor.fetchone():
        cursor.execute("SELECT COUNT(*) FROM data_vni")
        if cursor.fetchone()[0] > 0:
            print("Data already loaded. Skipping.")
            conn.close()
            data_vni_loaded = True
            return

    # Stocks
    screener = Screener(source="TCBS")
    default_params = {
        "exchangeName": "HOSE,HNX",
        "marketCap": (2000, 99999999999),
    }
    stock_df = screener.stock(default_params, limit=1700, lang="en")

    # Remove unstable columns
    stock_df = stock_df.drop(
        [x for x in stock_df.columns if x.startswith("price_vs")], axis=1
    )

    # Price board data
    price_board_df = load_price_board(tickers=stock_df["ticker"].tolist())

    # Result
    df = pd.merge(
        left=stock_df, right=price_board_df, left_on="ticker", right_on="symbol"
    )

    # Add additional instrument
    df = compute_instrument(df)

    df.to_sql("data_vni", conn, if_exists="replace", index=False)
    conn.close()
    data_vni_loaded = True
    print("Data loaded successfully.")


def load_price_board(tickers: list[str]) -> pd.DataFrame:
    price_board_df = Trading(source="vci", symbol="ACB").price_board(
        symbols_list=tickers
    )
    price_board_df.columns = price_board_df.columns.droplevel(0)  # Flatten columns
    price_board_df = price_board_df.drop("exchange", axis=1)
    price_board_df = price_board_df.loc[:, ~price_board_df.columns.duplicated()]

    return price_board_df


def compute_instrument(df: pd.DataFrame) -> pd.DataFrame:
    if "match_price" in df.columns:
        df = df.rename(columns={"match_price": "current_price"})
        df["price_change"] = df["current_price"] - df["ref_price"]
        df["pct_price_change"] = (df["price_change"] / df["ref_price"]) * 100

    # On the day when the market is closed
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


def fetch_data_for_symbols(symbols: list[str]):
    graph_data = []
    for symbol in symbols:
        df = load_historical_data(symbol)
        scaled_data, percent_diff = get_mini_graph_data(df)
        graph_data.append(
            {"label": symbol, "data": scaled_data, "percent_diff": percent_diff}
        )
    return graph_data


def load_company_overview(ticker: str):
    stock = Vnstock().stock(symbol=ticker, source="TCBS")
    company = stock.company
    overview = company.overview().iloc[0].to_dict()
    overview["website"] = (
        overview["website"].removeprefix("https://").removeprefix("http://")
    )
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
        asyncio.to_thread(load_officers_info, ticker),
        asyncio.to_thread(load_historical_data, ticker),
        asyncio.to_thread(load_income_statement, ticker),
        asyncio.to_thread(load_balance_sheet, ticker),
        asyncio.to_thread(load_cash_flow, ticker),
    ]
    (
        overview,
        shareholders,
        events,
        news,
        officers,
        price_data,
        income_statement,
        balance_sheet,
        cash_flow,
    ) = await asyncio.gather(*tasks)
    return {
        "overview": overview,
        "shareholders": shareholders,
        "events": events,
        "news": news,
        "officers": officers,
        "price_data": price_data,
        "income_statement": income_statement,
        "balance_sheet": balance_sheet,
        "cash_flow": cash_flow,
    }


if __name__ == "__main__":
    populate_db()
