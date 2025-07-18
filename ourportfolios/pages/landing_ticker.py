import pandas as pd
import reflex as rx
import sqlite3
from typing import Any, List, Dict

from ..components.price_chart import PriceChartState
from ..components.navbar import navbar
from ..components.cards import card_wrapper
from ..components.drawer import drawer_button, CartState
from ..components.financial_statement import financial_statements
from ..components.loading import loading_screen

from ..utils.load_data import load_company_data_async
from ..utils.preprocessing.financial_statements import (
    get_transformed_dataframes,
    format_quarter_data,
)


def fetch_technical_metrics(ticker: str) -> dict:
    conn = sqlite3.connect("ourportfolios/data/data_vni.db")
    df = pd.read_sql("SELECT * FROM data_vni WHERE ticker = ?", conn, params=(ticker,))
    conn.close()
    return df.iloc[0].to_dict() if not df.empty else {}


class State(rx.State):
    switch_value: str = "yearly"
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
    transformed_dataframes: dict = {}
    available_metrics_by_category: Dict[str, List[str]] = {}
    selected_metrics: Dict[str, str] = {}
    selected_metric: str = "P/E"
    available_metrics: List[str] = [
        "P/E",
        "P/B",
        "P/S",
        "P/Cash Flow",
        "ROE (%)",
        "ROA (%)",
        "Debt/Equity",
    ]
    selected_margin_metric: str = "gross_margin"

    @rx.event
    async def toggle_switch(self, value: bool):
        self.switch_value = "yearly" if value else "quarterly"
        yield
        await self.load_transformed_dataframes()

    @rx.event
    def load_technical_metrics(self):
        ticker = self.router.page.params.get("ticker", "")
        self.technical_metrics = fetch_technical_metrics(ticker)

    @rx.event
    async def load_company_data(self):
        ticker = self.router.page.params.get("ticker", "")
        data = await load_company_data_async(ticker)
        self.overview = data["overview"]
        self.shareholders = data["shareholders"]
        self.events = data["events"]
        self.news = data["news"]
        self.officers = data["officers"]
        self.price_data = data["price_data"]

    @rx.event
    async def load_transformed_dataframes(self):
        ticker = self.router.page.params.get("ticker", "")
        period_mapping = {"quarterly": "quarter", "yearly": "year"}
        mapped_period = period_mapping.get(self.switch_value, "year")

        result = await get_transformed_dataframes(ticker, period=mapped_period)

        self.transformed_dataframes = result
        self.income_statement = result["transformed_income_statement"]
        self.balance_sheet = result["transformed_balance_sheet"]
        self.cash_flow = result["transformed_cash_flow"]

        categorized_ratios = result.get("categorized_ratios", {})
        self.available_metrics_by_category = {}
        self.selected_metrics = {}
        excluded_columns = {"Year", "Quarter"}

        for category, data in categorized_ratios.items():
            if data:
                metrics = [col for col in data[0].keys() if col not in excluded_columns]
                self.available_metrics_by_category[category] = metrics
                if metrics:
                    self.selected_metrics[category] = metrics[0]

    @rx.event
    def set_metric_for_category(self, category: str, metric: str):
        self.selected_metrics[category] = metric

    @rx.var
    def get_chart_data_for_category(self) -> Dict[str, List[Dict[str, Any]]]:
        chart_data = {}
        categorized_ratios = self.transformed_dataframes.get("categorized_ratios", {})

        for category, data in categorized_ratios.items():
            selected_metric = self.selected_metrics.get(category)
            if selected_metric:
                if self.switch_value == "quarterly":
                    formatted_data = format_quarter_data(data)
                    time_key = "formatted_quarter"
                else:
                    formatted_data = data
                    time_key = "Year"

                chart_data[category] = [
                    {
                        "year": row.get(time_key, ""),
                        "value": row.get(selected_metric, 0) or 0,
                    }
                    for row in reversed(formatted_data)
                ][-8:]
            else:
                chart_data[category] = []

        return chart_data

    @rx.var
    def get_categories_list(self) -> List[str]:
        return list(self.transformed_dataframes.get("categorized_ratios", {}).keys())

    @rx.var
    def pie_data(self) -> list[dict[str, object]]:
        palettes = ["accent", "plum", "iris"]
        indices = [6, 7, 8]
        colors = [
            rx.color(palette, idx, True) for palette in palettes for idx in indices
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


def create_chart_component(category: str, position: int, is_placeholder: bool = False):
    if is_placeholder:
        return rx.card(
            rx.vstack(
                rx.hstack(
                    rx.heading(f"Chart {position + 1}", size="4", weight="medium"),
                    rx.spacer(),
                    rx.select(
                        [f"Metric {position + 1}.1", f"Metric {position + 1}.2"],
                        value=f"Metric {position + 1}.1",
                        size="1",
                    ),
                    align="center",
                    justify="between",
                    width="100%",
                ),
                rx.box(
                    rx.center(
                        rx.text(
                            f"Placeholder for Chart {position + 1}",
                            size="3",
                            color="gray",
                        ),
                        height="280px",
                    ),
                    width="100%",
                    style={
                        "overflow": "hidden",
                        "border": "2px dashed #ccc",
                        "borderRadius": "8px",
                    },
                ),
                spacing="3",
                align="stretch",
            ),
            width="100%",
            flex="1",
            min_width="0",
            max_width="100%",
            style={"padding": "1em", "minWidth": 0, "overflow": "hidden"},
        )

    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading(category, size="4", weight="medium"),
                rx.spacer(),
                rx.select(
                    State.available_metrics_by_category[category],
                    value=State.selected_metrics[category],
                    on_change=lambda value: State.set_metric_for_category(
                        category, value
                    ),
                    size="1",
                ),
                align="center",
                justify="between",
                width="100%",
            ),
            rx.box(
                rx.recharts.line_chart(
                    rx.recharts.line(
                        data_key="value",
                        stroke_width=3,
                        type_="monotone",
                        dot=False,
                    ),
                    rx.recharts.x_axis(
                        data_key="year",
                        angle=-45,
                        text_anchor="end",
                        padding={"left": 20, "right": 20},
                    ),
                    rx.recharts.y_axis(),
                    rx.recharts.tooltip(),
                    data=State.get_chart_data_for_category[category],
                    width="100%",
                    height=280,
                    margin={"top": 10, "right": 10, "left": 5, "bottom": 35},
                ),
                width="100%",
                style={"overflow": "hidden"},
            ),
            spacing="3",
            align="stretch",
        ),
        width="100%",
        flex="1",
        min_width="0",
        max_width="100%",
        style={"padding": "1em", "minWidth": 0, "overflow": "hidden"},
    )


def create_chart_row(start_idx: int, end_idx: int):
    categories = State.get_categories_list

    charts = []
    for i in range(start_idx, end_idx):
        charts.append(
            rx.cond(
                categories.length() > i,
                rx.foreach(
                    categories[i : i + 1],
                    lambda category, index: create_chart_component(category, i),
                ),
                create_chart_component("", i, is_placeholder=True),
            )
        )

    return rx.hstack(
        *charts,
        spacing="4",
        width="100%",
        align="stretch",
        justify="between",
    )


def performance_cards():
    return rx.vstack(
        create_chart_row(0, 3),
        create_chart_row(3, 6),
        spacing="3",
        width="100%",
        align="stretch",
    )


def name_card():
    return card_wrapper(
        rx.vstack(
            rx.hstack(
                rx.heading(State.technical_metrics["ticker"], size="9"),
                rx.button(
                    rx.icon("plus", size=16),
                    size="2",
                    variant="soft",
                    on_click=lambda: CartState.add_item(
                        State.technical_metrics["ticker"]
                    ),
                ),
                justify="center",
                align="center",
            ),
            rx.hstack(
                rx.badge(f"{State.technical_metrics['exchange']}", variant="surface"),
                rx.badge(f"{State.technical_metrics['industry']}"),
            ),
        ),
        style={"width": "100%", "padding": "1em"},
    )


def general_info_card():
    return rx.vstack(
        card_wrapper(
            rx.text(f"Market cap: {State.technical_metrics['market_cap']}"),
            rx.text(
                f"{State.overview['short_name']} (Est. {State.overview['established_year']})"
            ),
            rx.link(
                State.overview.get("website", ""),
                href=f"https://{State.overview.get('website', '')}",
                is_external=True,
            ),
            style={"width": "100%", "padding": "1em"},
        ),
    )


def key_metrics_card():
    return rx.card(
        rx.vstack(
            rx.tabs.root(
                rx.hstack(
                    rx.tabs.list(
                        rx.tabs.trigger("Performance", value="performance"),
                        rx.tabs.trigger("Financial Statements", value="statement"),
                    ),
                    rx.spacer(),
                    rx.hstack(
                        rx.badge(
                            "Quarterly",
                            color_scheme=rx.cond(
                                State.switch_value == "quarterly", "accent", "gray"
                            ),
                        ),
                        rx.switch(
                            checked=State.switch_value == "yearly",
                            on_change=State.toggle_switch,
                        ),
                        rx.badge(
                            "Yearly",
                            color_scheme=rx.cond(
                                State.switch_value == "yearly", "accent", "gray"
                            ),
                        ),
                        justify="center",
                        align="center",
                    ),
                    width="100%",
                    align="center",
                ),
                rx.tabs.content(
                    performance_cards(),
                    value="performance",
                    padding_top="1em",
                ),
                rx.tabs.content(
                    rx.box(
                        financial_statements(
                            [
                                State.income_statement,
                                State.balance_sheet,
                                State.cash_flow,
                            ]
                        ),
                        display="flex",
                        justify_content="center",
                        width="100%",
                    ),
                    value="statement",
                    padding_top="1em",
                ),
                default_value="performance",
                width="100%",
            ),
            spacing="0",
            justify="center",
            width="100%",
        ),
        padding="1em",
        flex=2,
        width="100%",
        min_width=0,
        max_width="100%",
    )


def price_chart_card():
    return rx.card(
        rx.flex(
            rx.script(
                src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js",
            ),
            rx.script(src="/chart.js"),
            rx.vstack(
                rx.box(id="price_chart", width="65vw", height="30vw"),
                rx.hstack(
                    rx.spacer(),
                    rx.foreach(
                        PriceChartState.date_range.keys(),
                        lambda item: rx.button(
                            item,
                            variant=rx.cond(
                                PriceChartState.selected_date_range == item,
                                "surface",
                                "soft",
                            ),
                            on_click=PriceChartState.set_date_range(item),
                        ),
                    ),
                    spacing="2",
                    paddingLeft="2em",
                    width="100%",
                ),
            ),
            rx.flex(
                rx.menu.root(
                    rx.menu.trigger(
                        rx.button(rx.icon("settings", size=20), variant="ghost")
                    ),
                    rx.menu.content(
                        rx.menu.sub(
                            rx.menu.sub_trigger("MA"),
                            rx.menu.sub_content(
                                rx.vstack(
                                    rx.foreach(
                                        PriceChartState.selected_ma_period.items(),
                                        lambda item: rx.checkbox(
                                            rx.text(
                                                f"MA{item[0]}",
                                                color=PriceChartState.ma_period[
                                                    item[0]
                                                ],
                                                weight="medium",
                                            ),
                                            checked=item[1],
                                            on_change=lambda value: PriceChartState.add_ma_period(
                                                value, item[0]
                                            ),
                                        ),
                                    ),
                                    spacing="3",
                                )
                            ),
                            modal=False,
                        ),
                        rx.menu.sub(
                            rx.menu.sub_trigger("RSI"),
                            rx.menu.sub_content(
                                rx.checkbox(
                                    rx.text("RSI14", weight="medium"),
                                    checked=PriceChartState.rsi_line,
                                    on_change=PriceChartState.add_rsi_line,
                                )
                            ),
                        ),
                    ),
                    modal=False,
                ),
                rx.button(
                    rx.icon(
                        rx.cond(
                            PriceChartState.selected_chart == "Candlestick",
                            "chart-candlestick",
                            "chart-spline",
                        ),
                        size=15,
                    ),
                    variant="ghost",
                    on_click=PriceChartState.set_selection,
                ),
                direction="column",
                spacing="3",
            ),
            width="100%",
            height="100%",
            direction="row",
            spacing="3",
        ),
    )


def officers_section():
    return rx.card(
        rx.scroll_area(
            rx.vstack(
                rx.foreach(
                    State.officers,
                    lambda officer: rx.box(
                        rx.hstack(
                            rx.heading(
                                officer["officer_name"],
                                weight="medium",
                                size="3",
                            ),
                            rx.badge(
                                f"{officer['officer_own_percent']}%",
                                color_scheme="gray",
                                variant="surface",
                                high_contrast=True,
                            ),
                            align="center",
                        ),
                        rx.text(officer["officer_position"], size="2"),
                    ),
                ),
                spacing="3",
                width="100%",
            ),
            style={"height": "24.3em"},
        ),
        width="100%",
    )


def events_section():
    return rx.scroll_area(
        rx.vstack(
            rx.foreach(
                State.events,
                lambda event: rx.box(
                    rx.card(
                        rx.hstack(
                            rx.heading(
                                event["event_name"],
                                weight="medium",
                                size="3",
                            ),
                            rx.badge(f"{event['price_change_ratio']}%"),
                            align="center",
                        ),
                        rx.text(
                            event["event_desc"],
                            weight="regular",
                            size="1",
                        ),
                    ),
                ),
            ),
            spacing="3",
        ),
        style={"height": "45.3em"},
    )


def news_section():
    return rx.scroll_area(
        rx.vstack(
            rx.foreach(
                State.news,
                lambda news: rx.card(
                    rx.hstack(
                        rx.text(
                            f"{news['title']} ({news['publish_date']})",
                            weight="regular",
                            size="2",
                        ),
                        rx.cond(
                            (news["price_change_ratio"] != None)
                            & ~(
                                news["price_change_ratio"] != news["price_change_ratio"]
                            ),
                            rx.badge(f"{news['price_change_ratio']}%"),
                        ),
                        align="center",
                        justify="between",
                        width="100%",
                    ),
                    width="100%",
                ),
            ),
        ),
        spacing="2",
        width="100%",
        style={"height": "45.3em"},
    )


def company_card():
    return rx.card(
        rx.vstack(
            rx.box(
                rx.segmented_control.root(
                    rx.segmented_control.item("Shares", value="shares"),
                    rx.segmented_control.item("Events", value="events"),
                    rx.segmented_control.item("News", value="news"),
                    on_change=State.setvar("company_control"),
                    value=State.company_control,
                    size="3",
                ),
                width="100%",
                display="flex",
                justify_content="center",
            ),
            rx.cond(
                State.company_control == "shares",
                rx.vstack(
                    rx.box(
                        shareholders_pie_chart(),
                        width="100%",
                        display="flex",
                        justify_content="center",
                        align_items="center",
                        style={"marginTop": "2.5em", "marginBottom": "2.5em"},
                    ),
                    officers_section(),
                    justify="center",
                    align="center",
                    width="100%",
                ),
                rx.cond(
                    State.company_control == "events",
                    events_section(),
                    news_section(),
                ),
            ),
            justify="center",
            align="center",
            width="100%",
            style={"height": "100%"},
        ),
        width="100%",
        flex=0.6,
        min_width=0,
        max_width="20em",
        style={"height": "100%"},
    )


def shareholders_pie_chart():
    return rx.recharts.PieChart.create(
        rx.recharts.Pie.create(
            data=State.pie_data,
            data_key="value",
            name_key="name",
            cx="50%",
            cy="50%",
            outer_radius=90,
            label=False,
        ),
        rx.recharts.GraphingTooltip.create(
            view_box={"width": 100, "height": 50},
        ),
        width=220,
        height=220,
    )


@rx.page(
    route="/analyze/[ticker]",
    on_load=[
        State.load_technical_metrics,
        State.load_company_data,
        State.load_transformed_dataframes,
        PriceChartState.load_chart_data,
        PriceChartState.load_chart_options,
    ],
)
def index():
    return rx.fragment(
        loading_screen(),
        navbar(),
        rx.box(
            rx.link(
                rx.hstack(
                    rx.icon("chevron_left", size=22),
                    rx.text("select", margin_top="-2px"),
                    spacing="0",
                ),
                href="/select",
                underline="none",
            ),
            position="fixed",
            justify="center",
            style={"paddingTop": "1em", "paddingLeft": "0.5em"},
            z_index="1",
        ),
        rx.center(
            rx.vstack(
                rx.box(
                    rx.hstack(
                        rx.vstack(
                            name_card(),
                            general_info_card(),
                            spacing="4",
                            align="center",
                        ),
                        price_chart_card(),
                        paddingBottom="1em",
                        width="100%",
                    ),
                    width="100%",
                ),
                rx.box(
                    rx.hstack(
                        key_metrics_card(),
                        company_card(),
                        width="100%",
                        wrap="wrap",
                    ),
                    width="100%",
                ),
                spacing="0",
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
