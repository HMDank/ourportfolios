import sqlite3
from vnstock import Screener, Listing, Trading
import pandas as pd

data_vni_loaded = False
price_board_loaded = False

def load_data_vni() -> None:
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

    # Stocks
    screener = Screener(source='TCBS')
    default_params = {
        'exchangeName': 'HOSE,HNX',
        'marketCap': (100, 99999999999),
    }
    stock_df = screener.stock(default_params, limit=1700, lang='en')

    # Price board data 
    price_board_df = Trading(source='vci',symbol='ACB').price_board(symbols_list=stock_df['ticker'].tolist())
    price_board_df.columns = price_board_df.columns.droplevel(0) # Flatten columns
    price_board_df = price_board_df.drop('exchange', axis=1) # Drop spare column to prevent duplicate column
    price_board_df = price_board_df.loc[:, ~price_board_df.columns.duplicated()]
    
    df = pd.merge(left=stock_df, right=price_board_df, left_on='ticker', right_on='symbol')
    
    # Compute additional instrument
    df = compute_instrument(df)
    df.to_sql("data_vni", conn, if_exists="replace", index=False)
    conn.close()
    data_vni_loaded = True
    print("Data loaded successfully.")


def compute_instrument(df: pd.DataFrame) -> pd.DataFrame:
    # Changes in price
    df = df.rename(columns={'bid_1_price': 'current_price'}) # rename for better comprehension
    df['price_change'] = df['current_price'] - df['ref_price'] # latest close price - close price from previous day
    df['current_price'] = round(df['current_price'] * 1e-3, 2)
    df['pct_price_change'] = round((df['price_change'] / df['ref_price']) * 100, 2)
    return df

if __name__ == "__main__":
    load_data_vni()