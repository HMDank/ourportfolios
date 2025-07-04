CREATE TABLE IF NOT EXISTS "TICKER".cash_flow_quarterly (
    id SERIAL PRIMARY KEY,
    "Year" INT,
    "Quarter" INT,
    "Operating cash flow" NUMERIC,
    "Investing cash flow" NUMERIC,
    "Financing cash flow" NUMERIC,
    "Ending cash position" NUMERIC,
    "Dividends paid" NUMERIC,
    "Share repurchase" NUMERIC,
    "Capital expenditure" NUMERIC,
    "Free cash flow" NUMERIC
);