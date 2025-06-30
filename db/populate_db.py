from config import load_config
from psycopg2 import sql
from psycopg2.extras import execute_values
import glob
import os
import psycopg2


def load_sql_files(root_dir: str):
    """
    Walk `root_dir`, find all .sql files, sort them by path,
    and return the list of full paths.
    """
    pattern = os.path.join(root_dir, "**", "*.sql")
    files = glob.glob(pattern, recursive=True)
    files.sort()
    return files


def create_all_tables(sql_root: str):
    """
    Connect to Postgres and run every .sql file under sql_root.
    """
    config = load_config()
    sql_files = load_sql_files(sql_root)

    with psycopg2.connect(**config) as conn:
        with conn.cursor() as cur:
            for path in sql_files:
                print(f"Applying {os.path.relpath(path, sql_root)}...")
                with open(path, 'r') as f:
                    sql_code = f.read()
                cur.execute(sql_code)
        conn.commit()
    print("All tables created successfully.")


def ingest_dataframe(df, table_name, schema="public", conn=None):
    """
    Bulk-insert the Pandas DataFrame `df` into `schema.table_name`.
    Requires column names in df matching the target table.
    """
    # If no existing connection passed, open a new one
    own_conn = False
    if conn is None:
        config = load_config()
        conn = psycopg2.connect(**config)
        own_conn = True

    cols = list(df.columns)
    insert_sql = sql.SQL(
        "INSERT INTO {schema}.{table} ({fields}) VALUES %s ON CONFLICT DO NOTHING"
    ).format(
        schema=sql.Identifier(schema),
        table=sql.Identifier(table_name),
        fields=sql.SQL(", ").join(map(sql.Identifier, cols)),
    )

    # Convert df rows to list of tuples
    data = [tuple(x) for x in df.to_numpy()]

    with conn.cursor() as cur:
        # execute_values does very fast bulk inserts
        execute_values(cur, insert_sql.as_string(conn), data)
    if own_conn:
        conn.commit()
        conn.close()
    else:
        conn.commit()


if __name__ == "__main__":
    here = os.path.dirname(__file__)
    sql_root = os.path.abspath(os.path.join(here, "..", "db/sql"))

    # 🔁 Change this to the SQL file you want to test
    test_sql_file = os.path.join(sql_root, "ticker/tickers.sql")

    # ✅ Read and execute just this one file
    config = load_config()
    with psycopg2.connect(**config) as conn:
        with conn.cursor() as cur:
            with open(test_sql_file, "r") as f:
                sql_code = f.read().strip()
            if sql_code:
                print(f"Running {os.path.relpath(test_sql_file, sql_root)}...")
                cur.execute(sql_code)
        conn.commit()
