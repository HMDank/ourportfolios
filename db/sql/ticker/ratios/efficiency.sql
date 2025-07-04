CREATE TABLE IF NOT EXISTS "TICKER".per_share_value (
    id SERIAL PRIMARY KEY,
    "Year" INT,
    "Asset Turnover" NUMERIC,
    "Inventory Turnover" NUMERIC,
    "ROA" NUMERIC,
    "Dividend Payout %" NUMERIC,
    "Cash Conversion Cycle" NUMERIC
);