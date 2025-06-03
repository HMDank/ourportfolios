import pandas as pd
import reflex as rx
import sqlite3

from ..components.navbar import navbar
from ..components.cards import card_wrapper


def fetch_ticker_data(ticker: str) -> dict:
    conn = sqlite3.connect("ourportfolios/data/data_vni.db")
    df = pd.read_sql(
        "SELECT * FROM data_vni WHERE ticker = ?", conn, params=(ticker,))
    conn.close()
    return df.iloc[0].to_dict() if not df.empty else {}


class State(rx.State):
    ticker_info: dict = {}

    @rx.event
    def load_ticker_info(self):
        params = self.router.page.params
        ticker = params.get("ticker", "")
        self.ticker_info = fetch_ticker_data(ticker)


@rx.page(route="/analyze/[ticker]", on_load=State.load_ticker_info)
def index():
    info = State.ticker_info
    return rx.fragment(
        navbar(),
        rx.button(
            rx.text("back")
        ),
        rx.box(
            rx.vstack(
                ticker_summary(info),
                key_metrics_card(info),
                width="100%",
                spacing="6",
            ),
            width="100%",
            padding="2em",
            padding_top="5em"
        ),
        max_width="600px",
        padding_x="4",
        padding_y="6",
    )


def ticker_summary(info):
    return rx.box(
        card_wrapper(
            rx.heading(info['ticker'], size='9'),
            rx.text(f"{info['industry']} ()")
        ),

    )


def key_metrics_card(info):
    # Group the metrics for clarity
    performance = [
        ("Alpha", f"{info['alpha']}"),
        ("Beta", f"{info['beta']}"),
        ("EPS", f"{info['eps']}"),
        ("Net Margin", f"{info['net_margin']}%"),
        ("Gross Margin", f"{info['gross_margin']}%"),
    ]
    growth = [
        ("Revenue Growth 1Y", f"{info['revenue_growth_1y']}%"),
        ("EPS Growth 1Y", f"{info['eps_growth_1y']}%"),
        ("Price vs SMA20", f"{info.get('price_vs_sma20', '')}"),
        ("RSI 14", f"{info['rsi14']}"),
    ]
    sentiment = [
        ("Foreign Transaction", f"{info['foreign_transaction']}"),
        ("Strong Buy %", f"{info['strong_buy_pct']}%"),
        ("Active Buy %", f"{info['active_buy_pct']}%"),
        ("Price Near Realtime", f"{info['price_near_realtime']}"),
    ]

    def metric_group(title, metrics):
        return rx.card(
            rx.vstack(
                rx.heading(title, weight="bold", size="6"),
                *[
                    rx.hstack(
                        rx.text(label + ":", weight="medium"),
                        rx.text(str(value)),
                        align="baseline",
                    )
                    for label, value in metrics
                ],
                # spacing="2"
            ),
            style={"width": "100%"}
        )

    return rx.card(
        rx.hstack(
            metric_group("Performance", performance),
            metric_group("Growth & Technical", growth),
            metric_group("Market Sentiment", sentiment),
            spacing="2",
            align="start",
            wrap="wrap"
        ),
        style={"width": "100%", "marginTop": "2em"}
    )
