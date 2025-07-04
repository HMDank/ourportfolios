CREATE TABLE IF NOT EXISTS "TICKER".per_share_value (
    id SERIAL PRIMARY KEY,
    "Year" INT,
    "Earnings" NUMERIC,
    "Free Cash Flow" NUMERIC,
    "Dividend" NUMERIC,
    "Book Value" NUMERIC,
    "Revenues" NUMERIC
);