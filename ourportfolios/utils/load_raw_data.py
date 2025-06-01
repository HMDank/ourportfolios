import sqlite3
from vnstock import Screener

data_vni_loaded = False


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
