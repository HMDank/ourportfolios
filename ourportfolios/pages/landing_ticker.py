from turtle import width
import pandas as pd
import reflex as rx
import sqlite3
from typing import Any
from vnstock import Vnstock


# from ..components.loading import loading_wrapper
from ..components.price_chart import PriceChartState, render_price_chart
from ..components.navbar import navbar
from ..components.cards import card_wrapper
from ..components.drawer import drawer_button, CartState
from ..utils.load_data import load_company_info, load_officers_info, load_historical_data, load_financial_statements
from ..utils.preprocess_texts import preprocess_events_texts
from ..components.financial_statement import financial_statements


def fetch_technical_metrics(ticker: str) -> dict:
    conn = sqlite3.connect("ourportfolios/data/data_vni.db")
    df = pd.read_sql(
        "SELECT * FROM data_vni WHERE ticker = ?", conn, params=(ticker,))
    conn.close()
    return df.iloc[0].to_dict() if not df.empty else {}


class State(rx.State):
    company_control: str = "shares"
    technical_metrics: dict = {}
    company_info: dict = {}
    overview: dict = {}
    officers: list[dict[str, Any]] = []
    shareholders: list[dict] = []
    events: list[dict] = []
    news: list[dict] = []
    price_data: pd.DataFrame = pd.DataFrame()
    income_statement: list[dict] = []
    balance_sheet: list[dict] = []
    cash_flow: list[dict] = []

    @rx.event
    def load_ticker_info(self):
        params = self.router.page.params
        ticker = params.get("ticker", "")

        self.technical_metrics = fetch_technical_metrics(ticker)
        self.overview, self.shareholders, self.events, self.news = load_company_info(
            ticker)
        self.officers = load_officers_info(ticker)
        self.price_data = load_historical_data(ticker)
        self.income_statement, self.balance_sheet, self.cash_flow = load_financial_statements(
            ticker)

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
            {
                "name": shareholder["share_holder"],
                "value": shareholder["share_own_percent"],
            }
            for shareholder in self.shareholders

        ]
        for idx, d in enumerate(data):
            d["fill"] = colors[idx % len(colors)]
        return data


@rx.page(route="/select/[ticker]", on_load=[State.load_ticker_info, PriceChartState.load_data])
# @loading_wrapper
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
                rx.box(
                    rx.hstack(
                        ticker_summary(),
                        display_price_plot(),
                        width="100%",
                    ),
                ),
                rx.box(
                    rx.hstack(
                        key_metrics_card(),
                        company_card(),
                        width="90vw",
                        wrap="wrap",
                    ),
                ),
                spacing='0',
                width="100%",
                justify="between",
                align="start",
                style={"maxWidth": "90vw", "margin": "0 auto"},
            ),
            width="100%",
            padding="2em",
            padding_top="5em",

            style={"maxWidth": "90vw", "margin": "0 auto"},
            position="relative",
        ),
        drawer_button(),
    )


def ticker_summary():
    technical_metrics = State.technical_metrics
    info = State.overview
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
            rx.text(f'Market cap: {technical_metrics['market_cap']}'),
            rx.text(f"{info['short_name']} (Est. {info['established_year']})"),
            rx.link(website, href=f"https://{website}", is_external=True),
            style=card_style
        ),
        spacing="4",
        # width="22em",
        align="center",
    )


def key_metrics_card():
    technical_metrics = State.technical_metrics
    performance = [
        ("Alpha", f"{technical_metrics['alpha']}"),
        ("Beta", f"{technical_metrics['beta']}"),
        ("EPS", f"{technical_metrics['eps']}"),
        ("Net Margin", f"{technical_metrics['net_margin']}%"),
        ("Gross Margin", f"{technical_metrics['gross_margin']}%"),
    ]
    growth = [
        ("Revenue Growth 1Y", f"{technical_metrics['revenue_growth_1y']}%"),
        ("EPS Growth 1Y", f"{technical_metrics['eps_growth_1y']}%"),
        ("Price vs SMA20", f"{technical_metrics.get('price_vs_sma20', '')}"),
        ("RSI 14", f"{technical_metrics['rsi14']}")
    ]

    def metric_group(title, metrics):
        return rx.card(
            rx.vstack(
                rx.heading(title, weight="bold", size="6"),
                *[
                    rx.hstack(
                        rx.text(label + ":", weight="medium"),
                        rx.text(str(value)),
                        spacing="2",
                        justify="between",
                        width="100%",
                    )
                    for label, value in metrics
                ],
                spacing="4",
                align="center",
                width="100%",
                max_width="400px",
            ),
            display="flex",
            justify_content="center",
            align_items="center",
            height="100%",
            padding="8",
        )

    return rx.card(
        rx.vstack(
            rx.tabs.root(
                rx.tabs.list(
                    rx.tabs.trigger("Performance", value="performance"),
                    rx.tabs.trigger("Growth & Technical", value="growth"),
                    rx.tabs.trigger("Financial Statements", value="statement"),
                ),
                rx.tabs.content(
                    rx.box(
                        metric_group("Performance", performance),
                        padding_top="1.5em",
                    ),
                    value="performance",
                ),
                rx.tabs.content(
                    metric_group("Growth & Technical", growth),
                    value="growth",
                    padding_top="1.5em",
                ),
                rx.tabs.content(
                    rx.box(
                        financial_statements([
                            State.income_statement,
                            State.balance_sheet,
                            State.cash_flow
                        ]),
                        display="flex",
                        justify_content="center",
                        width="100%",
                    ),
                    value="statement",
                    padding_top="1.5em",
                ),
                default_value="performance",
                height="100%",
            ),
            spacing="0",   # Remove spacing since we're using margin_top
            justify='center',
        ),
        padding="6",
        flex="1",
        min_height="50em",
    )


def company_card():
    return rx.card(
        rx.vstack(
            rx.box(
                rx.segmented_control.root(
                    rx.segmented_control.item(
                        "Shares", value="shares"),
                    rx.segmented_control.item("Events", value="events"),
                    rx.segmented_control.item("News", value="news"),
                    on_change=State.setvar("company_control"),
                    value=State.company_control,
                    size='3',
                ),
                justify_content='center',
            ),
            rx.cond(
                State.company_control == "shares",
                rx.vstack(
                    shareholders_pie_chart(),
                    rx.card(
                        rx.scroll_area(
                            rx.vstack(
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
                                    )
                                ),
                                spacing="3",
                                width="100%",
                            ),
                            style={"height": "24.3em"},
                        ),
                        width="100%",
                    ),
                    justify='center',
                    width="100%",
                ),
                rx.cond(
                    State.company_control == "events",
                    rx.scroll_area(
                        rx.vstack(
                            rx.foreach(
                                State.events,
                                lambda event: rx.box(
                                    rx.card(
                                        rx.hstack(
                                            rx.heading(
                                                event["event_name"],
                                                weight="bold",
                                                size='3'),
                                            rx.badge(
                                                f"{event['price_change_ratio']}%"),
                                            align='center',
                                        ),
                                        rx.text(event["event_desc"],
                                                weight="regular",
                                                size='1'),
                                    ),
                                ),
                            ),
                            spacing="3",
                        ),
                        style={"height": "45.3em"},
                    ),

                    rx.scroll_area(
                        rx.vstack(
                            rx.foreach(
                                State.news,
                                lambda news: rx.card(
                                    rx.hstack(
                                        rx.text(f'{news["title"]} ({news["publish_date"]})',
                                                weight="regular", size="2"),
                                        rx.cond(
                                            (news["price_change_ratio"] != None) & ~(
                                                news["price_change_ratio"] != news["price_change_ratio"]),
                                            rx.badge(
                                                f"{news['price_change_ratio']}%"),
                                        ),
                                        align="center",
                                        justify="between",
                                        width="100%",
                                    ),
                                    width="100%",
                                )
                            ),
                        ),
                        spacing="2",
                        width="100%",
                        style={"height": "45.3em"}
                    ),
                ),
            ),
            justify='center',
            align='center',
        ),
        width='24em',
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
                    outer_radius="80%",
                    label=False,
                ),
                rx.recharts.GraphingTooltip.create(
                    view_box={"width": 100, "height": 50},),
                width=300,
                height=300,
            ),
            spacing="1",
        ),
        width="100%",
        height="100%",
    )

def display_price_plot():
    return render_price_chart()