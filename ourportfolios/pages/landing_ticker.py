from turtle import width
import pandas as pd
import reflex as rx
import sqlite3
from typing import Any, List, Dict
from vnstock import Vnstock, Finance


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

    # Financial ratio data
    financial_df: pd.DataFrame = pd.DataFrame()
    selected_metric: str = "P/E"
    available_metrics: List[str] = ["P/E", "P/B", "P/S",
                                    "P/Cash Flow", "ROE (%)", "ROA (%)", "Debt/Equity"]
    selected_valuation_metric: str = "P/E"
    selected_profitability_metric: str = "ROE (%)"
    selected_margin_metric: str = "gross_margin"
    selected_dividend_metric: str = "dividend_vnd"

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
            ticker)
        self.officers = load_officers_info(ticker)
        self.price_data = load_historical_data(ticker)
        self.income_statement, self.balance_sheet, self.cash_flow = load_financial_statements(
            ticker)

    @rx.event
    def load_financial_ratios(self):
        """Load financial ratios data dynamically"""
        params = self.router.page.params
        ticker = params.get("ticker", "")

        financial_df = Finance(symbol=ticker, source='VCI').ratio(
            report_range='quarterly', is_all=True)
        financial_df.columns = financial_df.columns.droplevel(0)

        self.financial_df = financial_df

    @rx.var
    def transformed_financial_data(self) -> List[Dict[str, Any]]:
        """Transform financial data by creating quarter index"""
        if self.financial_df.empty:
            return []

        df = self.financial_df.copy()
        transformed = []

        # Check if we have year and lengthReport columns
        if 'yearReport' in df.columns and 'lengthReport' in df.columns:
            for _, row in df.head(8).iterrows():  # Take first 8 rows
                quarter_index = f"Q{row['lengthReport']} {row['yearReport']}"
                row_dict = row.to_dict()
                row_dict['quarter_index'] = quarter_index
                transformed.append(row_dict)
        else:
            # Fallback: use index as quarter indicator
            for i, (_, row) in enumerate(df.head(8).iterrows()):
                quarter_index = f"Q{i+1} 2024"  # Generic quarter naming
                row_dict = row.to_dict()
                row_dict['quarter_index'] = quarter_index
                transformed.append(row_dict)

        return transformed

    @rx.var
    def margin_data(self) -> List[Dict[str, Any]]:
        """Calculate gross and net margins from income statement"""
        if not self.income_statement:
            return []

        margin_data = []
        for statement in self.income_statement[:8]:  # Take first 8 quarters

            revenue = float(statement.get('revenue', 0)
                            ) if statement.get('revenue') else 0
            post_tax_profit = float(statement.get('post_tax_profit', 0)) if statement.get(
                'post_tax_profit') else 0

            # Calculate margins
            gross_margin = (post_tax_profit / revenue *
                            100) if revenue != 0 else 0
            net_margin = gross_margin  # Assuming post_tax_profit is net profit

            # Create quarter label from year and quarter info
            year = statement.get('yearReport', 2024)
            quarter = statement.get('lengthReport', 1)
            quarter_index = f"Q{quarter} {year}"

            margin_data.append({
                'quarter_index': quarter_index,
                'gross_margin': round(gross_margin, 2),
                'net_margin': round(net_margin, 2)
            })

        return margin_data

    @rx.var
    def dividend_data(self) -> List[Dict[str, Any]]:
        """Calculate dividend data using dividend_yield * P/B * BVPS"""
        if not self.transformed_financial_data:
            return []

        dividend_data = []
        for row in self.transformed_financial_data:
            dividend_yield = float(row.get('Dividend yield (%)', 0))
            pb_ratio = float(row.get('P/B', 0)) if row.get('P/B') else 0
            bvps = float(row.get('BVPS (VND)', 10000)) if row.get(
                'BVPS') else 10000  # Default BVPS

            dividend_vnd = dividend_yield * pb_ratio * bvps

            dividend_data.append({
                'quarter_index': row['quarter_index'],
                'dividend_vnd': round(dividend_vnd, 0)
            })

        return dividend_data

    @rx.var
    def valuation_chart_data(self) -> List[Dict[str, Any]]:
        """Get chart data for valuation metrics"""
        if not self.transformed_financial_data:
            return []

        chart_data = []
        metrics = ["P/E", "P/B", "P/S", "P/Cash Flow"]
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
        """Get chart data for profitability metrics"""
        if not self.transformed_financial_data:
            return []

        chart_data = []
        metrics = ["ROE (%)", "ROA (%)", "EPS (VND)"]
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

    @rx.event
    def set_valuation_metric(self, value: str):
        self.selected_valuation_metric = value

    @rx.event
    def set_profitability_metric(self, value: str):
        self.selected_profitability_metric = value

    @rx.event
    def set_margin_metric(self, value: str):
        self.selected_margin_metric = value

    @rx.event
    def set_dividend_metric(self, value: str):
        self.selected_dividend_metric = value

    @rx.var
    def valuation_chart_data_single(self) -> list[dict]:
        if not self.transformed_financial_data:
            return []
        metric = self.selected_valuation_metric
        # Reverse so newest is rightmost
        return [
            {"quarter": row["quarter_index"], metric: row.get(metric, 0) or 0}
            for row in reversed(self.transformed_financial_data)
        ]

    @rx.var
    def profitability_chart_data_single(self) -> list[dict]:
        if not self.transformed_financial_data:
            return []
        metric = self.selected_profitability_metric
        # Reverse so newest is rightmost
        return [
            {"quarter": row["quarter_index"], metric: row.get(metric, 0) or 0}
            for row in reversed(self.transformed_financial_data)
        ]

    @rx.var
    def margin_data_single(self) -> list[dict]:
        if not self.margin_data:
            return []
        metric = self.selected_margin_metric
        # Reverse so newest is rightmost
        return [
            {"quarter_index": row["quarter_index"],
                metric: row.get(metric, 0) or 0}
            for row in reversed(self.margin_data)
        ]

    @rx.var
    def dividend_data_single(self) -> list[dict]:
        if not self.dividend_data:
            return []
        metric = self.selected_dividend_metric
        # Reverse so newest is rightmost
        return [
            {"quarter_index": row["quarter_index"],
                metric: row.get(metric, 0) or 0}
            for row in reversed(self.dividend_data)
        ]


def create_valuation_chart():
    """Create valuation metrics chart with dropdown selector"""
    valuation_metrics = ["P/E", "P/B", "P/S", "P/Cash Flow"]
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Valuation Metrics", size="4", weight="bold"),
                rx.spacer(),
                rx.select(
                    valuation_metrics,
                    value=State.selected_valuation_metric,
                    on_change=State.set_valuation_metric,
                    size="1"
                ),
                align="center",
                justify="between",
                width="100%"
            ),
            rx.recharts.line_chart(
                rx.recharts.line(
                    data_key=State.selected_valuation_metric,
                    stroke_width=2,
                    type_="monotone"
                ),
                rx.recharts.x_axis(data_key="quarter",
                                   angle=-45, text_anchor="end"),
                rx.recharts.y_axis(),
                rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                rx.recharts.tooltip(),
                data=State.valuation_chart_data_single,
                width="100%",
                height=250,
                margin={"top": 10, "right": 10, "left": 5, "bottom": 35}
            ),
            spacing="3",
            align="stretch"
        ),
        width="100%",
        flex="1",
        min_width="0",
        max_width="100%",
    )


def create_profitability_chart():
    """Create profitability metrics chart with dropdown selector"""
    profitability_metrics = ["ROE (%)", "ROA (%)", "EPS"]
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Profitability Metrics", size="4", weight="bold"),
                rx.spacer(),
                rx.select(
                    profitability_metrics,
                    value=State.selected_profitability_metric,
                    on_change=State.set_profitability_metric,
                    size="1"
                ),
                align="center",
                justify="between",
                width="100%"
            ),
            rx.recharts.line_chart(
                rx.recharts.line(
                    data_key=State.selected_profitability_metric,
                    stroke_width=2,
                    type_="monotone"
                ),
                rx.recharts.x_axis(data_key="quarter",
                                   angle=-45, text_anchor="end"),
                rx.recharts.y_axis(),
                rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                rx.recharts.tooltip(),
                data=State.profitability_chart_data_single,
                width="100%",
                height=250,
                margin={"top": 10, "right": 10, "left": 5, "bottom": 35}
            ),
            spacing="3",
            align="stretch"
        ),
        width="100%",
        flex="1",
        min_width="0",
        max_width="100%",
    )


def create_margin_chart():
    """Create margin chart with dropdown selector"""
    margin_metrics = ["gross_margin", "net_margin"]
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Profit Margins", size="4", weight="bold"),
                rx.spacer(),
                rx.select(
                    margin_metrics,
                    value=State.selected_margin_metric,
                    on_change=State.set_margin_metric,
                    size="1"
                ),
                align="center",
                justify="between",
                width="100%"
            ),
            rx.recharts.line_chart(
                rx.recharts.line(
                    data_key=State.selected_margin_metric,
                    stroke_width=2,
                    type_="monotone"
                ),
                rx.recharts.x_axis(data_key="quarter_index",
                                   angle=-45, text_anchor="end"),
                rx.recharts.y_axis(),
                rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                rx.recharts.tooltip(),
                data=State.margin_data_single,
                width="100%",
                height=250,
                margin={"top": 10, "right": 10, "left": 5, "bottom": 35}
            ),
            spacing="3",
            align="stretch"
        ),
        width="100%",
        flex="1",
        min_width="0",
        max_width="100%",
    )


def create_dividend_chart():
    """Create dividend chart with dropdown selector"""
    dividend_metrics = ["dividend_vnd"]
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Dividend (VND)", size="4", weight="bold"),
                rx.spacer(),
                rx.select(
                    dividend_metrics,
                    value=State.selected_dividend_metric,
                    on_change=State.set_dividend_metric,
                    size="1"
                ),
                align="center",
                justify="between",
                width="100%"
            ),
            rx.recharts.line_chart(
                rx.recharts.line(
                    data_key=State.selected_dividend_metric,
                    stroke_width=2,
                    type_="monotone"
                ),
                rx.recharts.x_axis(data_key="quarter_index",
                                   angle=-45, text_anchor="end"),
                rx.recharts.y_axis(),
                rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                rx.recharts.tooltip(),
                data=State.dividend_data_single,
                width="100%",
                height=250,
                margin={"top": 10, "right": 10, "left": 5, "bottom": 35}
            ),
            spacing="3",
            align="stretch"
        ),
        width="100%",
        flex="1",
        min_width="0",
        max_width="100%",
    )


def performance_cards():
    """Performance cards with multiple financial metrics charts"""
    return rx.vstack(
        # First row: Valuation and Profitability metrics
        rx.hstack(
            create_valuation_chart(),
            create_profitability_chart(),
            spacing="4",
            width="100%",
            align="stretch",
            justify="between",
        ),
        # Second row: Margins and Dividend
        rx.hstack(
            create_margin_chart(),
            create_dividend_chart(),
            spacing="4",
            width="100%",
            align="stretch",
            justify="between",
        ),
        spacing="4",
        width="100%",
        align="stretch",
        justify="between",
    )


def name_card():
    technical_metrics = State.technical_metrics
    return card_wrapper(
        rx.vstack(
            rx.hstack(
                rx.heading(technical_metrics['ticker'], size='9'),
                rx.button(
                    rx.icon("plus", size=16),
                    size="2",
                    variant="soft",
                    on_click=lambda: CartState.add_item(
                        technical_metrics['ticker']),
                ),
                justify="center",
                align="center",
            ),
            rx.hstack(
                rx.badge(
                    f"{technical_metrics['exchange']}", variant='surface'),
                rx.badge(f"{technical_metrics['industry']}")
            ),
        ),
        style={"width": "100%", "padding": "1em"}
    ),


def general_info_card():
    technical_metrics = State.technical_metrics
    info = State.overview
    website = info.get('website', '')
    return rx.vstack(
        card_wrapper(
            rx.text(f'Market cap: {technical_metrics['market_cap']}'),
            rx.text(f"{info['short_name']} (Est. {info['established_year']})"),
            rx.link(website, href=f"https://{website}", is_external=True),
            style={"width": "100%", "padding": "1em"}
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
                    rx.box(
                        performance_cards(),
                    ),
                    value="performance",
                    padding_top="1em",
                ),
                rx.tabs.content(
                    rx.box(
                        rx.text('Something'),
                    ),
                    value="growth",
                    padding_top="1em",
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
                    padding_top="1em",
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


@rx.page(route="/analyze/[ticker]", on_load=[State.load_technical_metrics, State.load_company_data, State.load_financial_ratios, PriceChartState.load_data])
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
        rx.center(
            rx.vstack(
                rx.box(
                    rx.hstack(
                        rx.vstack(
                            name_card(),
                            general_info_card(),
                            spacing="4",
                            # width="22em",
                            align="center",
                        ),
                        display_price_plot(),
                        width="100%",
                    ),
                    width="100%"
                ),
                rx.box(
                    rx.hstack(
                        key_metrics_card(),
                        company_card(),
                        width="100%",
                        wrap="wrap",
                    ),
                    width="100%"
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
