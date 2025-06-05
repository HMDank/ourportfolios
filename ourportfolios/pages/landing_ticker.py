import pandas as pd
import reflex as rx
import sqlite3
from typing import Any
from vnstock import Vnstock

from ourportfolios.components.loading import loading_wrapper

from ..components.navbar import navbar
from ..components.cards import card_wrapper
from ..components.drawer import drawer_button, CartState
from ..utils.load_data import load_company_info, load_officers_info
from ..utils.preprocess_texts import preprocess_events_texts


def fetch_technical_metrics(ticker: str) -> dict:
    conn = sqlite3.connect("ourportfolios/data/data_vni.db")
    df = pd.read_sql(
        "SELECT * FROM data_vni WHERE ticker = ?", conn, params=(ticker,))
    conn.close()
    return df.iloc[0].to_dict() if not df.empty else {}


class State(rx.State):
    control: str = "officers"
    technical_metrics: dict = {}
    company_info: dict = {}
    overview: dict = {}
    officers: list[dict[str, Any]] = []
    shareholders: list[dict] = []
    events: list[dict] = []

    @rx.event
    def load_ticker_info(self):
        params = self.router.page.params
        ticker = params.get("ticker", "")
        self.technical_metrics = fetch_technical_metrics(ticker)
        self.overview, self.shareholders, self.events = load_company_info(
            ticker)
        self.officers = load_officers_info(ticker)

    @rx.var
    def pie_data(self) -> list[dict[str, object]]:

        palettes = ["accent", "plum", "iris"]
        indices = [6, 7, 8]
        colors = [
            rx.color(palette, idx, True)
            for palette in palettes
            for idx in indices
        ]
        data = [
            {"name": shareholder["share_holder"],
                "value": shareholder["share_own_percent"]}
            for shareholder in self.shareholders

        ]
        for idx, d in enumerate(data):
            d["fill"] = colors[idx % len(colors)]
        return data


@rx.page(route="/select/[ticker]", on_load=State.load_ticker_info)
@loading_wrapper
def index():
    return rx.fragment(
        navbar(),
        rx.box(
            rx.link(
                rx.hstack(rx.icon("chevron_left", size=22),
                          rx.text("select", margin_top="-2px"), spacing="0"),
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
                    ticker_summary(State.overview),
                    rx.card(
                        rx.text("graph :D"),
                        width="100%"
                    ),
                    width="100%"
                ),
                rx.hstack(
                    key_metrics_card(State.technical_metrics),
                    company_card(State.events)
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
                        size="2",
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


def company_card(events):
    return rx.box(
        rx.card(
            rx.segmented_control.root(
                rx.segmented_control.item(
                    "Shareholders", value="shareholders"),
                rx.segmented_control.item("Events", value="events"),
                on_change=State.setvar("control"),
                value=State.control,
                size="2",
                style={"height": "2.5em"}
            ),
        ),
        rx.cond(
            State.control == "shareholders",
            rx.card(
                rx.vstack(
                    rx.vstack(
                        shareholders_pie_chart(),
                        rx.card(
                            rx.foreach(
                                State.officers,
                                lambda officer: rx.box(
                                    rx.hstack(
                                        rx.heading(
                                            officer["officer_name"],
                                            weight="bold",
                                            size='3'
                                        ),
                                        rx.badge(
                                            f"{officer["officer_own_percent"]}%",
                                            color_scheme="gray",
                                            variant="surface",
                                            high_contrast=True
                                        ),
                                        align="center"
                                    ),
                                    rx.text(
                                        officer["officer_position"], size='2'),
                                    padding="1em",
                                )
                            ),
                        ),
                    ),
                    width="100%"
                ),
            ),
            rx.card(
                rx.foreach(
                    events,
                    lambda event: rx.box(
                        rx.heading(event["event_name"], weight="bold"),
                        rx.text(event["event_desc"], weight="regular"),
                    )
                ),
                width="100%"
            )
        ),
        width="100%"
    )


def shareholders_pie_chart():
    return rx.center(
        rx.vstack(
            rx.recharts.PieChart.create(
                rx.recharts.Pie.create(
                    data=State.pie_data,
                    data_key="value",
                    name_key="name",
                    cx="50%",
                    cy="50%",
                    outer_radius=100,
                    label=True,
                ),
                rx.recharts.GraphingTooltip.create(),
                width=300,
                height=300,
            ),
            spacing="1",
        ),
        width="100%",
        height="100%",
    )
