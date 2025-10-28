import pandas as pd
import reflex as rx
from typing import Any, List, Dict
from vnstock import Finance

from ..components.price_chart import PriceChartState
from ..components.navbar import navbar
from ..components.cards import card_wrapper
from ..components.drawer import drawer_button, CartState
from ..components.financial_statement import financial_statements
from ..components.loading import loading_screen

from ..utils.load_data import fetch_company_data
from ..utils.preprocessing.financial_statements import get_transformed_dataframes


class State(rx.State):
    switch_value: str = "year"

    company_control: str = "shares"

    # Change to DataFrames
    overview_df: pd.DataFrame = pd.DataFrame()
    profile_df: pd.DataFrame = pd.DataFrame()
    shareholders_df: pd.DataFrame = pd.DataFrame()
    events_df: pd.DataFrame = pd.DataFrame()
    news_df: pd.DataFrame = pd.DataFrame()
    officers_df: pd.DataFrame = pd.DataFrame()

    price_data: pd.DataFrame = pd.DataFrame()
    income_statement: list[dict] = []
    balance_sheet: list[dict] = []
    cash_flow: list[dict] = []

    financial_df: pd.DataFrame = pd.DataFrame()

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
        self.switch_value = "year" if value else "quarter"
        await self.load_transformed_dataframes()

    @rx.event
    async def load_company_data(self):
        ticker = self.ticker

        company_data = fetch_company_data(ticker)

        self.overview_df = company_data["overview"]
        self.shareholders_df = company_data["shareholders"]
        self.events_df = company_data["events"]
        self.news_df = company_data["news"]
        self.profile_df = company_data["profile"]
        self.officers_df = company_data["officers"]

    @rx.var(cache=True)
    def overview(self) -> dict:
        """Get overview as dict."""
        if self.overview_df.empty:
            return {}
        return self.overview_df.iloc[0].to_dict()

    @rx.var(cache=True)
    def profile(self) -> dict:
        """Get profile as dict."""
        if self.profile_df.empty:
            return {}
        return self.profile_df.iloc[0].to_dict()

    @rx.var(cache=True)
    def shareholders(self) -> list[dict]:
        """Get shareholders as list of dicts."""
        if self.shareholders_df.empty:
            return []
        return self.shareholders_df.to_dict("records")

    @rx.var(cache=True)
    def events(self) -> list[dict]:
        """Get events as list of dicts."""
        if self.events_df.empty:
            return []
        return self.events_df.to_dict("records")

    @rx.var(cache=True)
    def news(self) -> list[dict]:
        """Get news as list of dicts."""
        if self.news_df.empty:
            return []
        return self.news_df.to_dict("records")

    @rx.var(cache=True)
    def officers(self) -> list[dict]:
        """Get officers as list of dicts."""
        if self.officers_df.empty:
            return []
        return self.officers_df.to_dict("records")

    @rx.event
    def load_financial_ratios(self):
        """Load financial ratios data dynamically."""
        ticker = self.ticker

        report_range = self.switch_value
        financial_df = Finance(symbol=ticker, source="VCI").ratio(
            report_range=report_range, is_all=True
        )
        financial_df.columns = financial_df.columns.droplevel(0)

        self.financial_df = financial_df

    @rx.event
    async def load_transformed_dataframes(self):
        if self.transformed_dataframes:
            return

        ticker = self.ticker

        result = await get_transformed_dataframes(ticker, period=self.switch_value)

        self.transformed_dataframes = result
        self.income_statement = result["transformed_income_statement"]
        self.balance_sheet = result["transformed_balance_sheet"]
        self.cash_flow = result["transformed_cash_flow"]

        categorized_ratios = result.get("categorized_ratios", {})
        self.available_metrics_by_category = {}
        self.selected_metrics = {}

        for category, financial_data in categorized_ratios.items():
            if financial_data:
                excluded_columns = {"Year", "Quarter", "Date", "Period"}
                metrics = [
                    col
                    for col in financial_data[0]
                    if col not in excluded_columns
                ]
                self.available_metrics_by_category[category] = metrics
                if metrics:
                    self.selected_metrics[category] = metrics[0]

    @rx.event
    def set_metric_for_category(self, category: str, metric: str):
        """Set selected metric for a specific category"""
        self.selected_metrics[category] = metric

    @rx.var()
    def get_chart_data_for_category(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get chart data for all categories"""
        chart_data = {}
        categorized_ratios = self.transformed_dataframes.get("categorized_ratios", {})

        for category, data in categorized_ratios.items():
            selected_metric = self.selected_metrics[category]
            chart_data[category] = [
                {"year": row["Year"], "value": row.get(selected_metric, 0) or 0}
                for row in reversed(data)
            ][-8:]

        return chart_data

    @rx.var
    def get_categories_list(self) -> List[str]:
        """Get list of available categories"""
        return list(self.transformed_dataframes.get("categorized_ratios", {}).keys())

    @rx.var(cache=True)
    def pie_data(self) -> list[dict[str, object]]:
        palettes = ["accent", "plum", "iris"]
        indices = [6, 7, 8]
        colors = [
            rx.color(palette, idx, True) for palette in palettes for idx in indices
        ]

        pie_data = [
            {
                "name": shareholder["share_holder"],
                "value": shareholder["share_own_percent"],
            }
            for shareholder in self.shareholders
        ]
        for idx, d in enumerate(pie_data):
            d["fill"] = colors[idx % len(colors)]
        return pie_data


def create_dynamic_chart(category: str):
    """Create a dynamic chart for a specific category"""
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


def create_placeholder_chart(title: str, position: int):
    """Create placeholder chart when no data is available"""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading(title, size="4", weight="medium"),
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
                    rx.text(f"Placeholder for {title}", size="3", color="gray"),
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


def performance_cards():
    """Create performance cards with dynamic charts"""
    categories = State.get_categories_list

    return rx.cond(
        categories.length() > 0,
        rx.vstack(
            rx.hstack(
                rx.foreach(
                    categories[:3],
                    lambda category: create_dynamic_chart(category),
                ),
                spacing="4",
                width="100%",
            ),
            rx.hstack(
                rx.foreach(
                    categories[3:6],
                    lambda category: create_dynamic_chart(category),
                ),
                spacing="4",
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        rx.center(
            rx.spinner(size="3"),
        ),
    )


def name_card():
    overview = State.overview
    return (
        card_wrapper(
            rx.vstack(
                rx.hstack(
                    rx.heading(overview["symbol"], size="9"),
                    rx.button(
                        rx.icon("plus", size=16),
                        size="2",
                        variant="soft",
                        on_click=lambda: CartState.add_item(overview["symbol"]),
                    ),
                    justify="center",
                    align="center",
                ),
                rx.hstack(
                    rx.badge(f"{overview['exchange']}", variant="surface"),
                    rx.badge(f"{overview['industry']}"),
                ),
            ),
            style={"width": "100%", "padding": "1em"},
        ),
    )


def general_info_card():  # TODO: ALL DATA SHOULD COME FROM OVERVIEW_DF
    overview = State.overview
    website = overview["website"]
    return rx.vstack(
        card_wrapper(
            rx.text(f"{overview['short_name']} (Est. {overview['established_year']})"),
            rx.link(website, href=f"https://{website}", is_external=True),
            rx.text(f"Market cap: {overview['market_cap']} B. VND"),
            rx.text(f"Issue Shares: {overview['issue_share']}"),
            rx.text(f"Outstanding Shares: {overview['outstanding_share']}"),
            rx.text(
                f"{overview['no_shareholders']} shareholders ({overview['foreign_percent']}% foreign)"
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
                                State.switch_value == "quarter", "accent", "gray"
                            ),
                        ),
                        rx.switch(
                            checked=State.switch_value == "year",
                            on_change=State.toggle_switch,
                        ),
                        rx.badge(
                            "Yearly",
                            color_scheme=rx.cond(
                                State.switch_value == "year", "accent", "gray"
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
                        width="100%",
                        padding_top="2em",
                        padding_left="0.5em",
                        style={
                            "display": "block",
                            "textAlign": "left",
                        },
                    ),
                    value="statement",
                    padding_top="1em",
                    on_mount=lambda: [
                        State.load_financial_ratios(),
                        State.load_transformed_dataframes(),
                    ],
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
                rx.box(
                    id="price_chart",
                    width="100%",
                    height="100%",
                    min_width="0",
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.foreach(
                        PriceChartState.df_by_interval.keys(),
                        lambda item: rx.button(
                            item,
                            variant=rx.cond(
                                PriceChartState.selected_interval == item,
                                "surface",
                                "soft",
                            ),
                            on_click=PriceChartState.set_interval(item),
                        ),
                    ),
                    spacing="2",
                ),
                flex="1",
                min_width="0",
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
                flex="0 0 auto",
                align="center",
            ),
            width="100%",
            height="100%",
            direction="row",
            spacing="3",
            align="stretch",
        ),
        flex="1",
        min_width="0",
        width="100%",
    )


def company_generic_info_card():
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
                    rx.card(
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
                    ),
                    justify="center",
                    align="center",
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
                    ),
                    rx.scroll_area(
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
                                            (news["price_change_ratio"] is not None)
                                            & ~(
                                                news["price_change_ratio"]
                                                != news["price_change_ratio"]
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
                    ),
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


def company_profile_card():
    profile_data = State.profile
    PROFILE_CONTENT_HEIGHT = "12em"

    def create_profile_tab_content(content_key: str, tab_value: str):
        return rx.tabs.content(
            rx.scroll_area(
                rx.text(
                    profile_data[content_key],
                    size="3",
                    weight="regular",
                    style={
                        "whiteSpace": "pre-wrap",
                        "wordWrap": "break-word",
                        "textAlign": "justify",
                        "lineHeight": "1.6",
                    },
                ),
                height=PROFILE_CONTENT_HEIGHT,
                padding="0.5em",
            ),
            value=tab_value,
            padding_top="0.8em",
        )

    return rx.card(
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger("Company Profile", value="profile"),
                rx.tabs.trigger("History", value="history"),
                rx.tabs.trigger("Promises", value="promises"),
                rx.tabs.trigger("Risks", value="risks"),
                rx.tabs.trigger("Developments", value="developments"),
                rx.tabs.trigger("Strategies", value="strategies"),
                variant="surface",
            ),
            create_profile_tab_content("company_profile", "profile"),
            create_profile_tab_content("history_dev", "history"),
            create_profile_tab_content("company_promise", "promises"),
            create_profile_tab_content("business_risk", "risks"),
            create_profile_tab_content("key_developments", "developments"),
            create_profile_tab_content("business_strategies", "strategies"),
            default_value="profile",
        ),
        width="100%",
        padding="1em",
    )


@rx.page(
    route="/analyze/[ticker]",
    on_load=[
        State.load_company_data,
        PriceChartState.load_state,
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
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.vstack(
                            name_card(),
                            general_info_card(),
                            spacing="4",
                            align="center",
                            flex="0 0 auto",
                        ),
                        price_chart_card(),
                        spacing="4",
                        width="100%",
                        align="stretch",
                        height="450px",  # Give explicit height to this row
                    ),
                    company_profile_card(),
                    rx.hstack(
                        key_metrics_card(),
                        company_generic_info_card(),
                        spacing="4",
                        width="100%",
                        align="stretch",
                    ),
                    spacing="4",
                    width="100%",
                    justify="between",
                    align="start",
                ),
                width="86vw",
                style={"minHeight": "80vh"},
            ),
            width="100%",
            padding="2em",
            padding_top="5em",
            position="relative",
        ),
        drawer_button(),
    )
