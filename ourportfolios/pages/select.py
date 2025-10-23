import reflex as rx
import pandas as pd

from typing import List, Dict, Any
from sqlalchemy import text, TextClause

from ..components.navbar import navbar
from ..components.drawer import drawer_button, CartState
from ..components.page_roller import card_roller, card_link
from ..components.graph import mini_price_graph, pct_change_badge
from ..utils.load_data import fetch_data_for_symbols
from ..utils.generate_query import get_suggest_ticker
from ..utils.scheduler import db_settings


class State(rx.State):
    control: str = "home"
    show_arrow: bool = True
    data: List[Dict] = []

    # Search bar
    search_query = ""

    # Metrics
    fundamental_metrics: List[str] = [
        "pe",
        "pb",
        "roe",
        "alpha",
        "beta",
        "eps",
        "gross_margin",
        "net_margin",
        "ev_ebitda",
        "dividend_yield",
    ]
    technical_metrics: List[str] = ["rsi14"]

    # Sorts
    selected_sort_order: str = "ASC"
    selected_sort_option: str = "A-Z"

    sort_orders: List[str] = ["ASC", "DESC"]
    sort_options: Dict[str, str] = {
        "A-Z": "ticker",
        "Market Cap": "market_cap",
        "% Change": "pct_price_change",
        "Volume": "accumulated_volume",
    }

    # Filters
    selected_exchange: List[str] = []
    selected_industry: List[str] = []
    selected_technical_metric: List[str] = []
    selected_fundamental_metric: List[str] = []

    exchange_filter: Dict[str, bool] = {}
    industry_filter: Dict[str, bool] = {}
    technical_metric_filter: Dict[str, List[float]] = {}
    fundamental_metric_filter: Dict[str, List[float]] = {}

    def update_arrow(self, scroll_position: int, max_scroll: int):
        self.show_arrow = scroll_position < max_scroll - 10

    @rx.var
    def has_filter(self) -> bool:
        if (
            self.selected_industry
            or self.selected_exchange
            or self.selected_fundamental_metric
            or self.selected_technical_metric
        ):
            return True
        return False

    @rx.var(cache=True)
    def get_all_tickers(self) -> List[Dict[str, Any]]:
        query: List[str] = [
            """SELECT ticker, organ_name, current_price, accumulated_volume, pct_price_change 
            FROM comparison.comparison_df 
            WHERE """
        ]

        if self.search_query != "":
            match_query, params = get_suggest_ticker(
                search_query=self.search_query, return_type="query"
            )
            query.append(match_query)
        else:
            query.append("1=1")
            params = None

        query: List[str] = [" ".join(query)]

        # Order and filter

        # Filter by industry
        if self.selected_industry:
            query.append(
                f"AND industry IN ({', '.join(f"'{industry}'" for industry in self.selected_industry)})"
            )

        # Filter by exchange
        if self.selected_exchange:
            query.append(
                f"AND exchange IN ({', '.join(f"'{exchange}'" for exchange in self.selected_exchange)})"
            )

        # Filter by metrics
        if self.selected_fundamental_metric:  # Fundamental
            query.append(
                " ".join(
                    [
                        f"AND {metric} BETWEEN {self.fundamental_metric_filter.get(metric, [0.00, 0.00])[0]} AND {self.fundamental_metric_filter.get(metric, [0.00, 0.00])[1]}"
                        for metric in self.selected_fundamental_metric
                    ]
                )
            )

        if self.selected_technical_metric:  # Technical
            query.append(
                " ".join(
                    [
                        f"AND {metric} BETWEEN {self.technical_metric_filter.get(metric, [0.00, 0.00])[0]} AND {self.technical_metric_filter.get(metric, [0.00, 0.00])[1]}"
                        for metric in self.selected_technical_metric
                    ]
                )
            )

        # Order by condition
        if self.selected_sort_option:
            query.append(
                f"ORDER BY {self.sort_options[self.selected_sort_option]} {self.selected_sort_order}"
            )

        full_query: TextClause = text(" ".join(query))
        with db_settings.conn.connect() as connection:
            try:
                df: pd.DataFrame = pd.read_sql(full_query, connection, params=params)
                return df.to_dict("records")

            except Exception:
                return []

    @rx.var(cache=True)
    def get_all_tickers_length(self) -> int:
        return len(self.get_all_tickers)

    # Set all metrics/options to their default setting
    @rx.event
    def get_all_industries(self):
        industries: pd.DataFrame = pd.read_sql(
            "SELECT DISTINCT industry FROM comparison.comparison_df",
            con=db_settings.conn,
        )

        self.industry_filter: Dict[str, bool] = {
            item: False for item in industries["industry"].tolist()
        }

    @rx.event
    def get_all_exchanges(self):
        exchanges: pd.DataFrame = pd.read_sql(
            "SELECT DISTINCT exchange FROM comparison.comparison_df",
            con=db_settings.conn,
        )

        self.exchange_filter: Dict[str, bool] = {
            item: False for item in exchanges["exchange"].tolist()
        }

    @rx.event
    def get_fundamental_metrics(self):
        self.fundamental_metric_filter: Dict[str, List[float]] = {
            item: [0.00, 0.00] for item in self.fundamental_metrics
        }

    @rx.event
    def get_technical_metrics(self):
        self.technical_metric_filter: Dict[str, List[float]] = {
            item: [0.00, 0.00] for item in self.technical_metrics
        }

    @rx.event
    def get_graph(self, ticker_list):
        self.data = fetch_data_for_symbols(ticker_list)

    # Filter event handlers

    @rx.event
    def set_sort_option(self, option: str):
        self.selected_sort_option = option

    @rx.event
    def set_sort_order(self, order: str):
        self.selected_sort_order = order

    @rx.event
    def set_exchange(self, exchange: str, value: bool):
        self.exchange_filter[exchange] = value
        self.selected_exchange = [
            item[0] for item in self.exchange_filter.items() if item[1]
        ]

    @rx.event
    def set_industry(self, industry: str, value: bool):
        self.industry_filter[industry] = value
        self.selected_industry = [
            item[0] for item in self.industry_filter.items() if item[1]
        ]

    @rx.event
    def set_fundamental_metric(self, metric: str, value: List[float]):
        self.fundamental_metric_filter[metric] = value
        self.selected_fundamental_metric = [
            metric
            for metric, value_range in self.fundamental_metric_filter.items()
            if sum(value_range) > 0.00
        ]

    @rx.event
    def set_technical_metric(self, metric: str, value: List[float]):
        self.technical_metric_filter[metric] = value
        self.selected_technical_metric = [
            metric
            for metric, value_range in self.technical_metric_filter.items()
            if sum(value_range) > 0.00
        ]

    # Clear filters

    @rx.event
    def clear_technical_metric_filter(self):
        self.get_technical_metrics()
        self.selected_technical_metric = []

    @rx.event
    def clear_fundamental_metric_filter(self):
        self.get_fundamental_metrics()
        self.selected_fundamental_metric = []

    @rx.event
    def clear_sort_option(self):
        self.selected_sort_order = "ASC"  # Default
        self.selected_sort_option = "A-Z"  # Default

    @rx.event
    def clear_category_filter(self):
        self.get_all_industries()
        self.selected_industry = []  # Default

        self.get_all_exchanges()
        self.selected_exchange = []  # Default

    # Search bar

    @rx.event
    def set_search_query(self, value: str):
        self.search_query = value.upper()


# Filter section


@rx.page(
    route="/select",
    on_load=[
        State.get_graph(["VNINDEX", "UPCOMINDEX", "HNXINDEX"]),
        State.get_all_industries,
        State.get_all_exchanges,
        State.get_fundamental_metrics,
        State.get_technical_metrics,
        State.set_search_query(""),
    ],
)
def index():
    return rx.vstack(
        navbar(),
        page_selection(),
        rx.hstack(
            rx.vstack(
                rx.text("asdjfkhsdjf"),
                industry_roller(),
                # Filters
                ticker_filter(),
                # Tickers info
                ticker_basic_info(),
                spacing="1",
                width="62em",
            ),
            card_with_scrollable_area(),
            width="100%",
            justify="center",
            spacing="6",
            padding="2em",
            padding_top="5em",
        ),
        drawer_button(),
    )


def page_selection():
    return rx.box(
        card_roller(
            card_link(
                rx.hstack(
                    rx.icon("chevron_left", size=32),
                    rx.vstack(
                        rx.heading("Recommend", weight="regular", size="5"),
                        rx.text("caijdo", size="1"),
                        align="center",
                        justify="center",
                        height="100%",
                        spacing="1",
                    ),
                    align="center",
                    justify="center",
                ),
                href="/recommend",
            ),
            card_link(
                rx.vstack(
                    rx.heading("Select", weight="regular", size="7"),
                    rx.text("caijdo", size="3"),
                    align="center",
                    justify="center",
                    height="100%",
                    spacing="1",
                ),
                href="/select",
            ),
            card_link(
                rx.hstack(
                    rx.vstack(
                        rx.heading("Analyze", weight="regular", size="5"),
                        rx.text("caijdo", size="1"),
                        align="center",
                        justify="center",
                        height="100%",
                        spacing="1",
                    ),
                    rx.icon("chevron_right", size=32),
                    align="center",
                    justify="center",
                ),
                href="/analyze",
            ),
        ),
        width="100%",
        display="flex",
        justify_content="center",
        align_items="center",
        margin="0",
        padding="0",
    )


def card_with_scrollable_area():
    return rx.card(
        rx.segmented_control.root(
            rx.segmented_control.item("Markets", value="markets"),
            rx.segmented_control.item("Coin", value="coin"),
            rx.segmented_control.item("qqjdos", value="test"),
            on_change=State.setvar("control"),
            value=State.control,
            size="1",
            style={"height": "2em"},
        ),
        rx.scroll_area(
            rx.vstack(
                rx.foreach(
                    State.data,
                    lambda data: mini_price_graph(
                        label=data["label"],
                        data=data["data"],
                        diff=data["percent_diff"],
                        size=(120, 80),
                    ),
                ),
                spacing="2",
                height="100%",
                width="100%",
                align_items="flex-start",
            ),
            scrollbars="vertical",
            type="auto",
        ),
        style={
            "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            "justifyContent": "center",
        },
    )


def industry_roller():
    return rx.box(
        rx.box(
            rx.scroll_area(
                rx.hstack(
                    rx.foreach(
                        State.industry_filter.items(),
                        lambda item: rx.card(
                            rx.link(
                                rx.inset(
                                    rx.image(
                                        src="/placeholder-industry.png",  # ✅ Use placeholder or map industries to images
                                        width="40px",
                                        height="40px",
                                        style={"marginBottom": "0.5em"},
                                    ),
                                    item[0],
                                    style={
                                        "height": "120px",
                                        "minWidth": "200px",
                                        "padding": "1em",
                                        "display": "flex",
                                        "flexDirection": "column",
                                        "justifyContent": "center",
                                        "alignItems": "flex-start",
                                        "whiteSpace": "normal",
                                        "overflow": "visible",
                                    },
                                    side="right",
                                ),
                                href=f"/select/{item[0].lower()}",
                                underline="none",
                            )
                        ),
                    ),
                    spacing="2",
                    height="100%",
                    align_items="flex-start",
                ),
                style={"height": 140, "width": 1000, "position": "relative"},
                scrollbars="horizontal",
                type="scroll",
            ),
            rx.cond(
                State.show_arrow,
                rx.box(
                    rx.icon("chevron_right", size=36, color="white"),
                    style={
                        "position": "absolute",
                        "top": "46%",
                        "right": "0",
                        "transform": "translateY(-50%)",
                        "height": "100%",
                        "width": "60px",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "pointerEvents": "none",
                        "zIndex": 2,
                    },
                ),
            ),
            style={"position": "relative"},
        ),
    )


def ticker_card(
    ticker: str,
    organ_name: str,
    current_price: float,
    accumulated_volume: int,
    pct_price_change: float,
    **kwargs,
):
    color = rx.cond(
        pct_price_change.to(int) > 0,
        rx.color("green", 11),
        rx.cond(pct_price_change.to(int) < 0, rx.color("red", 9), rx.color("gray", 7)),
    )
    instrument_text_props = {
        "weight": "regular",
        "size":"5",
        "color": color
    }
    return rx.card(
        rx.flex(
            # Ticker and organ_name
            rx.box(
                rx.link(
                    rx.text(ticker, weight="medium", size="7"),
                    href=f"/analyze/{ticker}",
                    style={"textDecoration": "none", "color": "inherit"},
                ),
                rx.text(organ_name, color=rx.color("gray", 7), size="2"),
                **kwargs["layout_segments"]["symbol"],
            ),
            rx.text(
                current_price,
                **instrument_text_props,
                **kwargs["layout_segments"]["instrument"],
            ),
            rx.text(
                pct_change_badge(diff=pct_price_change),
                **instrument_text_props,
                **kwargs["layout_segments"]["instrument"],
            ),
            rx.text(
                f"{accumulated_volume:,.3f}",
                **instrument_text_props,
                **kwargs["layout_segments"]["instrument"],
            ),
            # Cart button
            rx.spacer(),
            rx.button(
                rx.icon("shopping-cart", size=16),
                size="2",
                variant="soft",
                on_click=lambda: CartState.add_item(ticker),
            ),
            align="center",
            direction="row",
            width="100%",
        ),
        width="100%",
        **kwargs["layout_spacing"],
    )


def ticker_basic_info_header(**kwargs) -> rx.Component:
    heading_text_props = {
        "weight": "medium",
        "color": "white",
        "size": "3",
    }
    return rx.card(
        rx.flex(
            rx.heading(
                "Symbol",
                **heading_text_props,
                **kwargs["layout_segments"]["symbol"],
            ),
            rx.heading(
                "Price",
                **heading_text_props,
                **kwargs["layout_segments"]["instrument"],
            ),
            rx.heading(
                "% Change",
                **heading_text_props,
                **kwargs["layout_segments"]["instrument"],
            ),
            rx.heading(
                "Volume",
                **heading_text_props,
                **kwargs["layout_segments"]["instrument"],
            ),
            direction="row",
            width="100%",
            **kwargs["layout_spacing"],
        ),
        variant="ghost",
    )


def ticker_basic_info():
    # Predefine card layout, use for both ticker info card's header and content
    card_layout = {
        "layout_spacing": {
            "paddingRight": "2em",
            "paddingLeft": "2em",
            "marginTop":"0.25em",
            "marginBottom": "0.55em",
        },
        "layout_segments": {
            "symbol": {"width": "30%", "align": "left"},
            "instrument": {"width": "20%", "align": "center"},
            "cart": {"width": "10%", "align": "center"},
        },
    }

    return (
        rx.card(
            # Header
            ticker_basic_info_header(**card_layout),
            # Ticker
            rx.scroll_area(
                rx.foreach(
                    State.get_all_tickers,
                    lambda value: ticker_card(
                        ticker=value.ticker,
                        organ_name=value.organ_name,
                        current_price=value.current_price,
                        accumulated_volume=value.accumulated_volume,
                        pct_price_change=value.pct_price_change,
                        **card_layout,
                    ),
                ),
                paddingRight="0.5em",
                type="hover",
                scrollbars="vertical",
                width="61em",
                height="30em",
            ),
            background_color=rx.color("gray", 1),
            border_radius=6,
            width="100%",
        ),
    )


def ticker_filter():
    return rx.flex(
        # Search box
        rx.box(
            rx.input(
                rx.input.slot(rx.icon(tag="search", size=16)),
                placeholder="Search for a ticker here!",
                type="search",
                size="2",
                width="100%",
                color_scheme="violet",
                radius="large",
                value=State.search_query,
                on_change=State.set_search_query,
            ),
            width="20%",
            height="100%",
            align="center",
            marginRight="0.5em",
        ),
        # Selected filter option
        rx.scroll_area(
            display_selected_filter(),
            scrollbars="horizontal",
            type="hover",
            width="45vw",
            height="5vh",
            align="end",
        ),
        rx.spacer(),  # Push filter button far right
        # Sort
        display_sort_options(),
        # Filter
        rx.menu.root(
            rx.menu.trigger(
                rx.button(
                    rx.hstack(
                        rx.icon("filter", size=12),
                        rx.text("Filter"),
                        align="center",
                        justify="between",
                    ),
                    variant=rx.cond(State.has_filter, "solid", "outline"),
                )
            ),
            rx.menu.content(
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger("Fundamental", value="fundamental"),
                        rx.tabs.trigger("Category", value="category"),
                        rx.tabs.trigger("Technical", value="technical"),
                        rx.spacer(),
                        rx.flex(
                            # Clear filter
                            rx.button(
                                rx.hstack(
                                    rx.icon("filter-x", size=12),
                                    rx.text("Clear all"),
                                    align="center",
                                ),
                                variant="outline",
                                on_click=[
                                    State.clear_category_filter,
                                    State.clear_sort_option,
                                    State.clear_fundamental_metric_filter,
                                    State.clear_technical_metric_filter,
                                ],
                            ),
                            align="center",
                            direction="row",
                            spacing="2",
                        ),
                    ),
                    rx.tabs.content(
                        metrics_filter(option="F"),
                        value="fundamental",
                    ),
                    rx.tabs.content(
                        category_filter(),
                        value="category",
                    ),
                    rx.tabs.content(
                        metrics_filter(option="T"),
                        value="technical",
                    ),
                    default_value="fundamental",
                ),
                width="50vw",
                height="28vw",
                side="left",
            ),
            modal=False,
        ),
        paddingTop="0.75em",
        paddingBottom="0.5em",
        width="100%",
        align="start",
        direction="row",
        spacing="2",
        height="3vw",
    )


def category_filter():
    return rx.vstack(
        # Exchange
        rx.vstack(
            rx.heading("Exchange", size="6", paddingLeft="1em"),
            rx.grid(
                rx.foreach(
                    State.exchange_filter.items(),
                    lambda item: rx.checkbox(
                        rx.badge(item[0]),
                        checked=item[1],
                        on_change=lambda value: State.set_exchange(
                            exchange=item[0], value=value
                        ),
                    ),
                ),
                rows=f"{State.exchange_filter.length() // 4}",
                columns="4",
                spacing="4",
                flow="row",
                align="center",
                paddingLeft="1em",
                justify="center",
            ),
        ),
        rx.spacer(),
        # Industry
        rx.vstack(
            rx.heading("Industry", size="6", paddingLeft="1em"),
            rx.grid(
                rx.foreach(
                    State.industry_filter.items(),
                    lambda item: rx.checkbox(
                        # item = {'<industry_tag>': bool=False}
                        rx.badge(item[0]),
                        checked=item[1],
                        on_change=lambda value: State.set_industry(
                            industry=item[0], value=value
                        ),
                        size="2",
                    ),
                ),
                rows=f"{State.industry_filter.length() // 4}",
                columns="4",
                spacing="4",
                flow="row",
                align="center",
                paddingLeft="1em",
                justify="between",
            ),
        ),
        paddingTop="2em",
        spacing="5",
        width="100%",
    )


def metrics_filter(option: str = "F") -> rx.Component:
    """Reusable slider section for both fundamentals & technicals
    option(str): {"F": for Fundamental-metrics,
                   "T" for Technical-metrics}
    """
    return rx.fragment(
        rx.scroll_area(
            rx.flex(
                rx.foreach(
                    rx.cond(
                        option == "F",
                        State.fundamental_metrics,
                        State.technical_metrics,
                    ),
                    lambda metric_tag: metric_slider(metric_tag, option),
                ),
                direction="row",
                wrap="wrap",
                align="center",
            ),
            paddingTop="0.5em",
            height="23vw",
            scrollbars="vertical",
            type="always",
        ),
    )


def metric_slider(metric_tag: str, option: str):
    return rx.vstack(
        # Metric
        rx.badge(
            rx.text(
                metric_tag.capitalize(), font_size="lg", font_weight="medium", size="2"
            ),
            variant="soft",
            radius="small",
            box_shadow="md",
            color_scheme="violet",
        ),
        rx.hstack(
            # Slider
            rx.slider(
                default_value=[0.00, 0.00],
                value=rx.cond(
                    option == "F",
                    State.fundamental_metric_filter[metric_tag],
                    State.technical_metric_filter[metric_tag],
                ),
                min_=0,
                max=100,
                on_change=lambda val: rx.cond(
                    option == "F",
                    State.set_fundamental_metric(metric_tag, value=val).throttle(100),
                    State.set_technical_metric(metric_tag, value=val).throttle(100),
                ),
                variant="surface",
                size="1",
                radius="small",
                orientation="horizontal",
            ),
            # Current value range
            rx.badge(
                rx.cond(
                    option == "F",
                    f"{State.fundamental_metric_filter.get(metric_tag, [0.00, 0.00])[0]} - {State.fundamental_metric_filter.get(metric_tag, [0.00, 0.00])[1]}",
                    f"{State.technical_metric_filter.get(metric_tag, [0.00, 0.00])[0]} - {State.technical_metric_filter.get(metric_tag, [0.00, 0.00])[1]}",
                ),
                radius="small",
                variant="solid",
                color_scheme="violet",
            ),
            width="100%",
            align="center",
        ),
        width="33%",
        align="start",
        padding="2.5em",
    )


def display_sort_options():
    return rx.fragment(
        rx.menu.root(
            rx.menu.trigger(
                rx.button(
                    rx.hstack(
                        rx.icon(
                            rx.cond(
                                State.selected_sort_order == "ASC",
                                "arrow-down-a-z",
                                "arrow-down-z-a",
                            ),
                            size=18,
                        ),
                        rx.text(State.selected_sort_option),
                        align="center",
                        justify="between",
                    ),
                    variant="outline",
                )
            ),
            rx.menu.content(
                rx.foreach(
                    State.sort_options.keys(),
                    lambda option: rx.menu.sub(
                        rx.menu.sub_trigger(option),
                        rx.menu.sub_content(
                            rx.foreach(
                                State.sort_orders,
                                lambda order: rx.menu.item(
                                    rx.hstack(
                                        rx.icon(
                                            rx.cond(
                                                order.to(str) == "ASC",
                                                "arrow-down-a-z",
                                                "arrow-down-z-a",
                                            ),
                                            size=13,
                                        ),
                                        rx.text(order),
                                        align="center",
                                        justify="between",
                                    ),
                                    on_click=[
                                        State.set_sort_option(option),
                                        State.set_sort_order(order),
                                    ],
                                ),
                            )
                        ),
                    ),
                )
            ),
        )
    )


def selected_filter_chip(item: str, filter: str) -> rx.Component:
    return rx.badge(
        rx.text(
            rx.cond(
                filter == "fundamental",
                f"{item}: {State.fundamental_metric_filter.get(item, [0.00, 0.00])[0]}-{State.fundamental_metric_filter.get(item, [0.00, 0.00])[1]}",
                rx.cond(
                    filter == "technical",
                    f"{item}: {State.technical_metric_filter.get(item, [0.00, 0.00])[0]}-{State.technical_metric_filter.get(item, [0.00, 0.00])[1]}",
                    item,
                ),
            ),
            size="2",
            weight="medium",
        ),
        rx.button(
            rx.icon("circle-x", size=11),
            variant="ghost",
            on_click=rx.cond(
                filter == "industry",
                State.set_industry(item, False),
                rx.cond(
                    filter == "exchange",
                    State.set_exchange(item, False),
                    rx.cond(
                        filter == "fundamental",
                        State.set_fundamental_metric(item, [0.00, 0.00]),
                        State.set_technical_metric(item, [0.00, 0.00]),
                    ),
                ),
            ),
        ),
        color_scheme="violet",
        radius="large",
        variant="outline",
        _hover={"opacity": 0.75},
        size="2",
    )


def display_selected_filter() -> rx.Component:
    return rx.flex(
        rx.foreach(
            State.selected_industry, lambda item: selected_filter_chip(item, "industry")
        ),
        rx.foreach(
            State.selected_exchange, lambda item: selected_filter_chip(item, "exchange")
        ),
        rx.foreach(
            State.selected_fundamental_metric,
            lambda item: selected_filter_chip(item, "fundamental"),
        ),
        rx.foreach(
            State.selected_technical_metric,
            lambda item: selected_filter_chip(item, "technical"),
        ),
        direction="row",
        spacing="2",
        align="center",
        justify="start",
    )
