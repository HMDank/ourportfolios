import pandas as pd
import reflex as rx


df = pd.DataFrame([
    {"ticker": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
    {"ticker": "GOOG", "name": "Alphabet Inc.", "sector": "Technology"},
    {"ticker": "TSLA", "name": "Tesla Inc.", "sector": "Automotive"},
])


class State(rx.State):
    @rx.var(cache=True)
    def ticker_info(self) -> dict:
        row = df[df["ticker"] == self.ticker]
        if not row.empty:
            return row.iloc[0].to_dict()
        return {"ticker": self.ticker, "name": "Unknown", "sector": "Unknown"}


@rx.page(route="/[ticker]")
def landing_ticker():
    return rx.vstack(
        rx.heading(f"Ticker: {State.ticker_info['ticker']}"),
        rx.text(f"Name: {State.ticker_info['name']}"),
        rx.text(f"Sector: {State.ticker_info['sector']}"),
    )
