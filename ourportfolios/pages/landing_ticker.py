import pandas as pd
import reflex as rx
import sqlite3
from sqlmodel import over
from vnstock import Vnstock

from ..components.navbar import navbar
from ..components.cards import card_wrapper
from ..components.drawer import drawer_button, CartState


def fetch_technical_metrics(ticker: str) -> dict:
    conn = sqlite3.connect("ourportfolios/data/data_vni.db")
    df = pd.read_sql(
        "SELECT * FROM data_vni WHERE ticker = ?", conn, params=(ticker,))
    conn.close()
    return df.iloc[0].to_dict() if not df.empty else {}


def load_company_info(ticker: str):
    stock = Vnstock().stock(symbol=ticker, source='TCBS')
    company = stock.company
    finance = stock.finance

    overview = company.overview().iloc[0].to_dict()
    overview['website'] = overview['website'].removeprefix(
        'https://').removeprefix('http://').removeprefix('www.')

    officers = (
        company.officers().dropna().groupby("officer_name")
        .agg({
            "officer_position": lambda x: ", ".join(sorted(set(x))),
            "officer_own_percent": "first"
        })
        .reset_index()
        .sort_values(by="officer_own_percent", ascending=False)
    )
    events = company.events()

    return overview


class State(rx.State):
    technical_metrics: dict = {}
    company_info: dict = {}
    overview: dict = {}

    @rx.event
    def load_ticker_info(self):
        params = self.router.page.params
        ticker = params.get("ticker", "")
        self.technical_metrics = fetch_technical_metrics(ticker)
        self.overview = load_company_info(ticker)

    @rx.event
    def load_company_info(self):
        return


@rx.page(route="/select/[ticker]", on_load=State.load_ticker_info)
def index():
    technical_metrics = State.technical_metrics
    overview = State.overview
    return rx.fragment(
        navbar(),
        rx.box(
            rx.link(
                rx.hstack(rx.icon("chevron_left", size=22),
                          rx.text("select"), spacing="1"),
                href='/select',
                underline="none"
            ),
            position="fixed",
            justify="center",
            style={"paddingTop": "1em", "paddingLeft": "0.5em"},
            z_index="1",
        ),
        rx.box(
            rx.vstack(
                rx.hstack(
                    ticker_summary(overview),
                    rx.card(
                        rx.text("graph :D"),
                        width="100%"
                    ),
                    width="100%"
                ),
                rx.hstack(
                    key_metrics_card(technical_metrics),
                ),
                width="100%",
                spacing="6",
            ),
            width="100%",
            padding="2em",
            padding_top="5em",
            style={"maxWidth": "90vw", "margin": "0 auto"},
            position="relative",
        ),
        drawer_button(),
    )


def ticker_summary(info):
    website = info.get('website', '')
    card_style = {"width": "100%", "padding": "1em"}
    return rx.vstack(
        card_wrapper(
            rx.vstack(
                rx.hstack(
                    rx.heading(info['symbol'], size='9'),
                    rx.button(
                        rx.icon("plus", size=16),
                        size="3",
                        variant="soft",
                        on_click=lambda: CartState.add_item(info['symbol']),
                    ),
                    justify="center",
                    align="center",
                ),
                rx.hstack(
                    rx.badge(f"{info['exchange']}", variant='surface'),
                    rx.badge(f"{info['industry']}")
                ),
            ),
            style=card_style
        ),
        card_wrapper(
            rx.text(f"{info['short_name']} (Est. {info['established_year']})"),
            rx.link(website, href=f"https://{website}", is_external=True),
            style=card_style
        ),
        spacing="4",
        width="16em",
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
