DROP TABLE IF EXISTS tickers;

CREATE TABLE tickers (
  id         SERIAL PRIMARY KEY,
  ticker     TEXT   NOT NULL,
  name       TEXT,
  exchange   TEXT   NOT NULL,
  UNIQUE(ticker, exchange)
);
