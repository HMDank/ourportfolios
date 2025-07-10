import pandas as pd
import reflex as rx
import sqlite3
from typing import Any, List, Dict
from vnstock import Finance

from ..components.price_chart import PriceChartState, render_price_chart
from ..components.navbar import navbar
from ..components.cards import card_wrapper
from ..components.drawer import drawer_button, CartState
from ..utils.load_data import (
    load_company_info,
    load_officers_info,
    load_historical_data,
    load_financial_statements,
)
from ..components.financial_statement import financial_statements


def fetch_technical_metrics(ticker: str) -> dict:
    conn = sqlite3.connect("ourportfolios/data/data_vni.db")
    df = pd.read_sql("SELECT * FROM data_vni WHERE ticker = ?", conn, params=(ticker,))
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

    # Financial ratio data
    financial_df: pd.DataFrame = pd.DataFrame()

    # Mapping for profitability metrics (display name -> data key)
    profitability_metric_mapping: Dict[str, str] = {
        "ROE (TTM)": "ROE (%)",
        "ROA (TTM)": "ROA (%)",
        "Earnings Per Share": "EPS (VND)",
        "Gross Margin": "gross_margin",
        "Net Margin": "net_margin",
    }

    # Mapping for dividend metrics (display name -> data key)
    dividend_metric_mapping: Dict[str, str] = {"Dividend (VND)": "dividend_vnd"}

    # Valuation metrics (no mapping needed - display name = data key)
    valuation_options: List[str] = ["P/E", "P/B", "P/S", "P/Cash Flow", "EV/EBITDA"]

    # Display options for dropdowns
    profitability_display_options: List[str] = [
        "ROE (TTM)",
        "ROA (TTM)",
        "Earnings Per Share",
        "Gross Margin",
        "Net Margin",
    ]
    dividend_display_options: List[str] = ["Dividend (VND)"]

    # Selected metrics
    selected_valuation_metric: str = "P/E"
    selected_profitability_display: str = "ROE (TTM)"
    selected_dividend_display: str = "Dividend (VND)"

    # Internal data keys (computed from mappings)
    selected_profitability_metric: str = "ROE (%)"
    selected_dividend_metric: str = "dividend_vnd"

    # Legacy fields (keeping for backward compatibility)
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
    def load_technical_metrics(self):
        params = self.router.page.params
        ticker = params.get("ticker", "")
        self.technical_metrics = fetch_technical_metrics(ticker)

    @rx.event
    def load_company_data(self):
        params = self.router.page.params
        ticker = params.get("ticker", "")

        self.overview, self.shareholders, self.events, self.news = load_company_info(
            ticker
        )
        self.officers = load_officers_info(ticker)
        self.price_data = load_historical_data(ticker)
        self.income_statement, self.balance_sheet, self.cash_flow = (
            load_financial_statements(ticker)
        )

    @rx.event
    def load_financial_ratios(self):
        """Load financial ratios data dynamically"""
        params = self.router.page.params
        ticker = params.get("ticker", "")

        financial_df = Finance(symbol=ticker, source="VCI").ratio(
            report_range="quarterly", is_all=True
        )
        financial_df.columns = financial_df.columns.droplevel(0)

        self.financial_df = financial_df

    @rx.var
    def transformed_financial_data(self) -> List[Dict[str, Any]]:
        """Transform financial data by creating quarter index"""
        if self.financial_df.empty:
            return []

        df = self.financial_df.copy()
        transformed = []

        for _, row in df.head(8).iterrows():
            quarter_index = f"Q{row['lengthReport']} {row['yearReport']}"
            row_dict = row.to_dict()
            row_dict["quarter_index"] = quarter_index
            transformed.append(row_dict)

        return transformed

    @rx.var
    def margin_data(self) -> List[Dict[str, Any]]:
        """Calculate gross and net margins from income statement"""
        if not self.income_statement:
            return []

        margin_data = []
        for statement in self.income_statement[:8]:
            revenue = (
                float(statement.get("revenue", 0)) if statement.get("revenue") else 0
            )
            gross_profit = (
                float(statement.get("gross_profit", 0))
                if statement.get("gross_profit")
                else 0
            )
            post_tax_profit = (
                float(statement.get("post_tax_profit", 0))
                if statement.get("post_tax_profit")
                else 0
            )

            gross_margin = (gross_profit / revenue * 100) if revenue != 0 else 0
            net_margin = (post_tax_profit / revenue * 100) if revenue != 0 else 0

            # Create quarter label from year and quarter info
            year = statement.get("yearReport", 2024)
            quarter = statement.get("lengthReport", 1)
            quarter_index = f"Q{quarter} {year}"

            margin_data.append(
                {
                    "quarter_index": quarter_index,
                    "gross_margin": round(gross_margin, 2),
                    "net_margin": round(net_margin, 2),
                }
            )

        return margin_data

    @rx.var
    def dividend_data(self) -> List[Dict[str, Any]]:
        """Calculate dividend data using dividend_yield * P/B * BVPS"""
        if not self.transformed_financial_data:
            return []

        dividend_data = []
        for row in self.transformed_financial_data:
            dividend_yield = float(row.get("Dividend yield (%)", 0))
            pb_ratio = float(row.get("P/B", 0)) if row.get("P/B") else 0
            bvps = float(row.get("BVPS (VND)", 10000)) if row.get("BVPS") else 10000

            dividend_vnd = dividend_yield * pb_ratio * bvps

            dividend_data.append(
                {
                    "quarter_index": row["quarter_index"],
                    "dividend_vnd": round(dividend_vnd, 0),
                }
            )

        return dividend_data

    @rx.var
    def valuation_chart_data(self) -> List[Dict[str, Any]]:
        """Get chart data for valuation metrics"""
        if not self.transformed_financial_data:
            return []

        chart_data = []
        metrics = ["P/E", "P/B", "P/S", "P/Cash Flow", "EV/EBITDA"]
        for row in self.transformed_financial_data:
            data_point = {"quarter": row["quarter_index"]}
            for metric in metrics:
                value = row.get(metric, 0)
                if value is None or pd.isna(value):
                    value = 0
                data_point[metric] = float(value)
            chart_data.append(data_point)

        return chart_data

    @rx.var
    def profitability_chart_data(self) -> List[Dict[str, Any]]:
        """Get combined chart data for profitability metrics including margins"""
        if not self.transformed_financial_data:
            return []

        chart_data = []
        for i, row in enumerate(self.transformed_financial_data):
            data_point = {"quarter": row["quarter_index"]}
            profitability_metrics = ["ROE (%)", "ROA (%)", "EPS (VND)"]
            for metric in profitability_metrics:
                value = row.get(metric, 0)
                if value is None or pd.isna(value):
                    value = 0
                data_point[metric] = float(value)

            if i < len(self.margin_data):
                margin_row = self.margin_data[i]
                data_point["gross_margin"] = margin_row.get("gross_margin", 0)
                data_point["net_margin"] = margin_row.get("net_margin", 0)
            else:
                data_point["gross_margin"] = 0
                data_point["net_margin"] = 0

            chart_data.append(data_point)

        return chart_data

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

    # Event handlers for setting metrics
    @rx.event
    def set_valuation_metric(self, value: str):
        """Set valuation metric (no mapping needed)"""
        self.selected_valuation_metric = value

    @rx.event
    def set_profitability_metric(self, display_value: str):
        """Set profitability metric using display value"""
        self.selected_profitability_display = display_value
        self.selected_profitability_metric = self.profitability_metric_mapping.get(
            display_value, display_value
        )

    @rx.event
    def set_dividend_metric(self, display_value: str):
        """Set dividend metric using display value"""
        self.selected_dividend_display = display_value
        self.selected_dividend_metric = self.dividend_metric_mapping.get(
            display_value, display_value
        )

    # Legacy event handlers (keeping for backward compatibility)
    @rx.event
    def set_margin_metric(self, value: str):
        self.selected_margin_metric = value

    @rx.var
    def current_profitability_data_key(self) -> str:
        """Get the actual data key for the selected profitability metric"""
        return self.profitability_metric_mapping.get(
            self.selected_profitability_display, self.selected_profitability_display
        )

    @rx.var
    def current_dividend_data_key(self) -> str:
        """Get the actual data key for the selected dividend metric"""
        return self.dividend_metric_mapping.get(
            self.selected_dividend_display, self.selected_dividend_display
        )

    # Single metric chart data methods
    @rx.var
    def valuation_chart_data_single(self) -> list[dict]:
        if not self.transformed_financial_data:
            return []
        metric = self.selected_valuation_metric
        return [
            {"quarter": row["quarter_index"], metric: row.get(metric, 0) or 0}
            for row in reversed(self.transformed_financial_data)
        ]

    @rx.var
    def profitability_chart_data_single(self) -> list[dict]:
        if not self.transformed_financial_data:
            return []

        metric = self.selected_profitability_metric

        # Handle margin metrics separately since they come from margin_data
        if metric in ["gross_margin", "net_margin"]:
            if not self.margin_data:
                return []
            return [
                {"quarter": row["quarter_index"], metric: row.get(metric, 0) or 0}
                for row in reversed(self.margin_data)
            ]

        # Handle other profitability metrics from transformed_financial_data
        return [
            {"quarter": row["quarter_index"], metric: row.get(metric, 0) or 0}
            for row in reversed(self.transformed_financial_data)
        ]

    @rx.var
    def dividend_data_single(self) -> list[dict]:
        if not self.dividend_data:
            return []
        metric = self.selected_dividend_metric
        return [
            {"quarter_index": row["quarter_index"], metric: row.get(metric, 0) or 0}
            for row in reversed(self.dividend_data)
        ]


def graph_card(
    title: str,
    metric_options: list[str],
    selected_metric: str,
    set_metric_event,
    chart_data,
    data_key: str,
    x_axis_key: str,
):
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading(title, size="4", weight="medium"),
                rx.spacer(),
                rx.select(
                    metric_options,
                    value=selected_metric,
                    on_change=set_metric_event,
                    size="1",
                ),
                align="center",
                justify="between",
                width="100%",
            ),
            rx.box(
                rx.recharts.line_chart(
                    rx.recharts.line(
                        data_key=data_key,
                        stroke_width=3,
                        type_="monotone",
                        dot=False,
                    ),
                    rx.recharts.x_axis(
                        data_key=x_axis_key,
                        angle=-45,
                        text_anchor="end",
                        padding={"left": 20, "right": 20},
                    ),
                    rx.recharts.y_axis(),
                    rx.recharts.tooltip(),
                    data=chart_data,
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


def create_valuation_chart():
    return graph_card(
        title="Valuation",
        metric_options=State.valuation_options,
        selected_metric=State.selected_valuation_metric,
        set_metric_event=State.set_valuation_metric,
        chart_data=State.valuation_chart_data_single,
        data_key=State.selected_valuation_metric,
        x_axis_key="quarter",
    )


def create_profitability_chart():
    return graph_card(
        title="Profitability",
        metric_options=State.profitability_display_options,
        selected_metric=State.selected_profitability_display,
        set_metric_event=State.set_profitability_metric,
        chart_data=State.profitability_chart_data_single,
        data_key=State.current_profitability_data_key,
        x_axis_key="quarter",
    )


def create_placeholder_chart_a():
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Chart A", size="4", weight="medium"),
                rx.spacer(),
                rx.select(
                    ["Metric A1", "Metric A2", "Metric A3"], value="Metric A1", size="1"
                ),
                align="center",
                justify="between",
                width="100%",
            ),
            rx.box(
                rx.center(
                    rx.text("Placeholder for Chart A", size="3", color="gray"),
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


def create_placeholder_chart_b():
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Chart B", size="4", weight="medium"),
                rx.spacer(),
                rx.select(
                    ["Metric B1", "Metric B2", "Metric B3"], value="Metric B1", size="1"
                ),
                align="center",
                justify="between",
                width="100%",
            ),
            rx.box(
                rx.center(
                    rx.text("Placeholder for Chart B", size="3", color="gray"),
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


def create_placeholder_chart_c():
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Chart C", size="4", weight="medium"),
                rx.spacer(),
                rx.select(
                    ["Metric C1", "Metric C2", "Metric C3"], value="Metric C1", size="1"
                ),
                align="center",
                justify="between",
                width="100%",
            ),
            rx.box(
                rx.center(
                    rx.text("Placeholder for Chart C", size="3", color="gray"),
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


def create_dividend_chart():
    return graph_card(
        title="Dividend (VND)",
        metric_options=State.dividend_display_options,
        selected_metric=State.selected_dividend_display,
        set_metric_event=State.set_dividend_metric,
        chart_data=State.dividend_data_single,
        data_key=State.selected_dividend_metric,
        x_axis_key="quarter_index",
    )


def performance_cards():
    return rx.vstack(
        rx.hstack(
            create_dividend_chart(),
            create_placeholder_chart_a(),
            create_profitability_chart(),
            spacing="4",
            width="100%",
            align="stretch",
            justify="between",
        ),
        rx.hstack(
            create_valuation_chart(),
            create_placeholder_chart_b(),
            create_placeholder_chart_c(),
            spacing="4",
            width="100%",
            align="stretch",
            justify="between",
        ),
        spacing="3",
        width="100%",
        align="stretch",
    )


def name_card():
    technical_metrics = State.technical_metrics
    return (
        card_wrapper(
            rx.vstack(
                rx.hstack(
                    rx.heading(technical_metrics["ticker"], size="9"),
                    rx.button(
                        rx.icon("plus", size=16),
                        size="2",
                        variant="soft",
                        on_click=lambda: CartState.add_item(
                            technical_metrics["ticker"]
                        ),
                    ),
                    justify="center",
                    align="center",
                ),
                rx.hstack(
                    rx.badge(f"{technical_metrics['exchange']}", variant="surface"),
                    rx.badge(f"{technical_metrics['industry']}"),
                ),
            ),
            style={"width": "100%", "padding": "1em"},
        ),
    )


def general_info_card():
    technical_metrics = State.technical_metrics
    info = State.overview
    website = info.get("website", "")
    return rx.vstack(
        card_wrapper(
            rx.text(f"Market cap: {technical_metrics['market_cap']}"),
            rx.text(f"{info['short_name']} (Est. {info['established_year']})"),
            rx.link(website, href=f"https://{website}", is_external=True),
            style={"width": "100%", "padding": "1em"},
        ),
    )


def key_metrics_card():
    return rx.card(
        rx.vstack(
            rx.tabs.root(
                rx.tabs.list(
                    rx.tabs.trigger("Performance", value="performance"),
                    rx.tabs.trigger("Growth & Technical", value="growth"),
                    rx.tabs.trigger("Financial Statements", value="statement"),
                ),
                rx.tabs.content(
                    performance_cards(),
                    value="performance",
                    padding_top="1em",
                ),
                rx.tabs.content(
                    rx.box(
                        rx.text("Something"),
                    ),
                    value="growth",
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
                                            (news["price_change_ratio"] != None)
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


@rx.page(
    route="/analyze/[ticker]",
    on_load=[
        State.load_technical_metrics,
        State.load_company_data,
        State.load_financial_ratios,
        PriceChartState.load_chart_data,
        PriceChartState.load_chart_options,
    ],
)
def index():
    return rx.fragment(
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
                        render_price_chart(),
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
