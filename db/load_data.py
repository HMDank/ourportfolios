from preprocess_texts import process_events_for_display
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
        'marketCap': (2000, 99999999999),
    }
    df = screener.stock(default_params, limit=1700, lang='en')

    df.to_sql("data_vni", conn, if_exists="replace", index=False)
    conn.close()
    data_vni_loaded = True
    print("Data loaded successfully.")


def load_company_info(ticker: str):
    stock = Vnstock().stock(symbol=ticker, source='TCBS')
    company = stock.company

    overview = company.overview().iloc[0].to_dict()
    overview['website'] = overview['website'].removeprefix(
        'https://').removeprefix('http://')

    shareholders_df = company.shareholders()
    shareholders_df["share_own_percent"] = (
        shareholders_df["share_own_percent"] * 100).round(2)

    shareholders = shareholders_df.to_dict("records")
    events = company.events()
    events['price_change_ratio'] = (events['price_change_ratio']*100).round(2)
    events = events.to_dict("records")
    processed_events = process_events_for_display(events)

    news = company.news()
    news = news[~news['title'].str.contains('insider', case=False, na=False)]
    news['price_change_ratio'] = (news['price_change_ratio']*100).round(2)
    news = news.to_dict("records")

    return overview, shareholders, processed_events, news


def load_officers_info(ticker: str):
    stock = Vnstock().stock(symbol=ticker, source='TCBS')
    company = stock.company
    officers = (
        company.officers().dropna(subset=["officer_name"]).fillna(
            "").groupby("officer_name")
        .agg({
            "officer_position": lambda x: ", ".join(sorted(set(pos.strip() for pos in x if isinstance(pos, str) and pos.strip()))),
            "officer_own_percent": "first"
        })
        .reset_index()
        .sort_values(by="officer_own_percent", ascending=False)
    )
    officers["officer_own_percent"] = (
        officers["officer_own_percent"] * 100).round(2)

    officers = officers.sort_values(
        by="officer_own_percent", ascending=False).to_dict("records")

    return officers


def load_financial_statements(ticker: str):
    stock = Vnstock().stock(symbol=ticker, source='TCBS')
    finance = stock.finance
    income_statement = finance.income_statement(period='year').reset_index()
    balance_sheet = finance.balance_sheet(period='year').reset_index()
    cash_flow = finance.cash_flow(period='year').reset_index()

    return income_statement.to_dict("records"), balance_sheet.to_dict("records"), cash_flow.to_dict("records")

def load_tickers(filter_df):
    tickers = filter_df['ticker']
    for ticker in tickers:
        stock = Vnstock().stock(symbol=ticker, source='TCBS')
        company = stock.company

        profile = company.profile().iloc[0].to_dict()
        name = profile['company_name']
        tickers['name'] = name

        overview = company.overview().iloc[0].to_dict()
        short_name = overview['shortname']
        tickers['short_name'] = short_name

    return tickers

if __name__ == "__main__":
    populate_db()
