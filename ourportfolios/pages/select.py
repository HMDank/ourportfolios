import reflex as rx
import pandas as pd
import asyncio

from typing import List, Dict, Any, Set

from ..components.navbar import navbar
from ..components.drawer import drawer_button
from ..components.page_roller import card_roller, card_link
from ..components.ticker_board import TickerBoardState, ticker_board
from ..utils.scheduler import db_settings


class State(rx.State):
    control: str = "home"
    show_arrow: bool = True
    data: List[Dict] = []

    # Search bar
    search_query = ""

    # Metrics
    fundamentals_default_value: Dict[str, List[float]] = {
        "pe": [0.00, 100.00],
        "pb": [0.00, 10.00],
        "roe": [0.00, 100.00],
        "roa": [0.00, 100.00],
        "doe": [0.00, 10.00],
        "eps": [100.00, 10000.00],
        "ps": [0.00, 100.00],
        "gross_margin": [0.00, 200.00],
        "net_margin": [0.00, 200.00],
        "ev": [0.00, 100.00],
        "ev_ebitda": [0.00, 200.00],
        "dividend_yield": [0.00, 100.00],
    }
    technicals_default_value: Dict[str, List[float]] = {
        "rsi14": [0.00, 100.00],
        "alpha": [0.00, 5.00],
        "beta": [0.00, 5.00],
    }

    # Sorts
    selected_sort_order: str = "ASC"
    selected_sort_option: str = "A-Z"

    sort_orders: List[str] = ["ASC", "DESC"]
    sort_options: Dict[str, str] = {
        "A-Z": "symbol",
        "Market Cap": "market_cap",
        "% Change": "pct_price_change",
        "Volume": "accumulated_volume",
    }

    # Filters
    selected_exchange: Set[str] = set()
    selected_industry: Set[str] = set()
    selected_technical_metric: Set[str] = set()
    selected_fundamental_metric: Set[str] = set()

    exchange_filter: Dict[str, bool] = {}
    industry_filter: Dict[str, bool] = {}
    technicals_current_value: Dict[str, List[float]] = {}
    fundamentals_current_value: Dict[str, List[float]] = {}

    def update_arrow(self, scroll_position: int, max_scroll: int):
        self.show_arrow = scroll_position < max_scroll - 10

    @rx.var
    def has_filter(self) -> bool:
        if (
            len(self.selected_industry) > 0
            or len(self.selected_exchange) > 0
            or len(self.selected_fundamental_metric) > 0
            or len(self.selected_technical_metric) > 0
        ):
            return True
        return False

    @rx.event(background=True)
    async def apply_filters(self):
        async with self:
            ticker_board_state = await self.get_state(TickerBoardState)
            ticker_board_state.apply_filters(
                filters={
                    "industry": self.selected_industry,
                    "exchange": self.selected_exchange,
                    "fundamental": {
                        metric: self.fundamentals_current_value[metric]
                        for metric in self.selected_fundamental_metric
                    },
                    "technical": {
                        metric: self.technicals_current_value[metric]
                        for metric in self.selected_technical_metric
                    },
                }
            )

    # Set all metrics/options to their default setting
    @rx.event
    def get_all_industries(self):
        try:
            with db_settings.conn.connect() as connection:
                industries = pd.read_sql(
                    "SELECT DISTINCT industry FROM tickers.overview_df;",
                    connection,
                )
                self.industry_filter: Dict[str, bool] = {
                    item: False for item in industries["industry"].tolist()
                }
        except Exception as e:
            print(f"Database error: {e}")
            self.industry_filter: Dict[str, bool] = {}

    @rx.event
    def get_all_exchanges(self):
        try:
            with db_settings.conn.connect() as connection:
                exchanges: pd.DataFrame = pd.read_sql(
                    "SELECT DISTINCT exchange FROM tickers.overview_df;",
                    connection,
                )

                self.exchange_filter: Dict[str, bool] = {
                    item: False for item in exchanges["exchange"].tolist()
                }
        except Exception as e:
            print(f"Database error: {e}")
            self.exchange_filter: Dict[str, bool] = {}

    @rx.event
    def get_fundamentals_default_value(self):
        self.fundamentals_current_value: Dict[str, List[float]] = dict.fromkeys(
            self.fundamentals_default_value, [0.00, 0.00]
        )

    @rx.event
    def get_technicals_default_value(self):
        self.technicals_current_value: Dict[str, List[float]] = dict.fromkeys(
            self.technicals_default_value, [0.00, 0.00]
        )

    # Search bar
    @rx.event(background=True)
    async def set_search_query(self, value: str):
        async with self:
            self.search_query = value

        yield

        async with self:
            ticker_board_state = await self.get_state(TickerBoardState)
            ticker_board_state.set_search_query(self.search_query)

    # Filter event handlers

    @rx.event(background=True)
    async def set_sort_option(self, option: str):
        async with self:
            self.selected_sort_option = option

        yield

        async with self:
            ticker_board_state = await self.get_state(TickerBoardState)
            ticker_board_state.set_sort_option(self.sort_options[option])

    @rx.event(background=True)
    async def set_sort_order(self, order: str):
        async with self:
            self.selected_sort_order = order
        yield

        async with self:
            ticker_board_state = await self.get_state(TickerBoardState)
            ticker_board_state.set_sort_order(order)

    @rx.event(background=True)
    async def set_exchange(self, exchange: str, value: bool):
        async with self:
            self.exchange_filter[exchange] = value

        yield

        async with self:
            if value is True:
                self.selected_exchange.add(exchange)
            else:
                self.selected_exchange.discard(exchange)

    @rx.event(background=True)
    async def set_industry(self, industry: str, value: bool):
        async with self:
            self.industry_filter[industry] = value

        yield

        async with self:
            if value is True:
                self.selected_industry.add(industry)
            else:
                self.selected_industry.discard(industry)

    @rx.event(background=True)
    async def set_fundamental_metric(self, metric: str, value: List[float]):
        async with self:
            self.fundamentals_current_value[metric] = value

        yield

        async with self:
            if (
                sum(value) > 0
                and sum(value) < self.fundamentals_default_value[metric][1]
            ):
                self.selected_fundamental_metric.add(metric)
            else:
                self.selected_fundamental_metric.discard(metric)

    @rx.event(background=True)
    async def set_technical_metric(self, metric: str, value: List[float]):
        async with self:
            self.technicals_current_value[metric] = value

        yield

        async with self:
            if sum(value) > 0 and sum(value) < self.technicals_default_value[metric][1]:
                self.selected_technical_metric.add(metric)
            else:
                self.selected_technical_metric.discard(metric)

    # Clear filters

    @rx.event(background=True)
    async def clear_all_filters(self):
        async with self:
            self.selected_technical_metric = set()
            self.selected_fundamental_metric = set()
            self.selected_industry = set()  # Default
            self.selected_exchange = set()  # Default

        yield

        async with self:
            ticker_board_state = await self.get_state(TickerBoardState)
            tasks = [
                rx.run_in_thread(ticker_board_state.clear_all_filters),
                rx.run_in_thread(self.get_technicals_default_value),
                rx.run_in_thread(self.get_fundamentals_default_value),
                rx.run_in_thread(self.get_all_industries),
                rx.run_in_thread(self.get_all_exchanges),
            ]
            await asyncio.gather(*tasks)


# Filter section


@rx.page(
    route="/select",
    on_load=[
        State.get_all_industries,
        State.get_all_exchanges,
        State.get_fundamentals_default_value,
        State.get_technicals_default_value,
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
                ticker_board(),
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


def ticker_filter():
    return rx.flex(
        # Search box
        rx.box(
            rx.input(
                rx.input.slot(rx.icon(tag="search", size=16)),
                placeholder="Search for a ticker",
                type="search",
                size="2",
                width="100%",
                color_scheme="violet",
                radius="large",
                value=State.search_query,
                on_change=State.set_search_query,
            ),
            width="30%",
            height="100%",
            align="center",
            marginRight="0.5em",
        ),
        # Selected filter option
        rx.scroll_area(
            display_selected_filter(),
            scrollbars="horizontal",
            paddingTop="0.1em",
            type="hover",
            width="48em",
            height="2.6em",
        ),
        rx.spacer(),  # Push filter button far right
        # Sort
        display_sort_options(),
        # Filter
        filter_button(),
        paddingTop="0.75em",
        paddingBottom="0.5em",
        width="100%",
        direction="row",
        spacing="2",
        height="3em",
    )


def filter_button() -> rx.Component:
    return (
        rx.menu.root(
            rx.menu.trigger(
                rx.button(
                    rx.hstack(
                        rx.icon("filter", size=12),
                        rx.text("Filter"),
                        align="center",
                    ),
                    variant=rx.cond(State.has_filter, "solid", "outline"),
                )
            ),
            rx.menu.content(
                filter_tabs(),
                rx.flex(
                    rx.spacer(),
                    apply_filter_button(),
                    direction="row",
                    width="100%",
                    paddingRight="1em",
                ),
                width=rx.breakpoints(
                    initial="27em", xs="30em", sm="40em", md="40em", lg="52em"
                ),
                height="28em",
                side="left",
            ),
            modal=False,
        ),
    )


def apply_filter_button() -> rx.Component:
    return rx.button(
        rx.text("Apply", weight="medium", color="white", size="2"),
        variant="solid",
        on_click=State.apply_filters,
    )


def filter_tabs() -> rx.Component:
    return (
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger("Fundamental", value="fundamental"),
                rx.tabs.trigger("Categorical", value="categorical"),
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
                        on_click=State.clear_all_filters,
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
                categorical_filter(),
                value="categorical",
            ),
            rx.tabs.content(
                metrics_filter(option="T"),
                value="technical",
            ),
            default_value="fundamental",
        ),
    )


def categorical_filter():
    grid_layout = {
        "columns": rx.breakpoints(
            initial="1",
            xs="2",
            sm="3",
            md="3",
            lg="4",
        ),
        "spacing": "4",
        "flow": "row",
        "align": "center",
        "paddingLeft": "0.5em",
        "paddingRight": "1em",
        "justify": "between",
        "wrap": "wrap",
    }

    return rx.vstack(
        # Exchange
        rx.vstack(
            rx.heading("Exchange", size="6"),
            rx.center(
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
                    **grid_layout,
                ),
                width="100%",
            ),
            spacing="2",
        ),
        # Industry
        rx.vstack(
            rx.heading("Industry", size="6"),
            rx.scroll_area(
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
                            size="1",
                        ),
                    ),
                    **grid_layout,
                ),
                scrollbar="vertical",
                type="hover",
                width="100%",
                height="12em",
            ),
            spacing="2",
        ),
        paddingTop="2em",
        paddingLeft="0.5em",
        spacing="4",
        width="100%",
    )


def metrics_filter(option: str = "F") -> rx.Component:
    """Reusable slider section for both fundamentals & technicals
    option(str): {"F": for Fundamental-metrics,
                   "T" for Technical-metrics}
    """
    return rx.scroll_area(
        rx.grid(
            rx.foreach(
                rx.cond(
                    option == "F",
                    State.fundamentals_default_value.keys(),
                    State.technicals_default_value.keys(),
                ),
                lambda metric_tag: metric_slider(metric_tag, option),
            ),
            columns=rx.breakpoints(
                xs="1",
                sm="2",
                md="2",
                lg="3",
            ),
            flow="row",
            wrap="wrap",
            align="center",
        ),
        paddingTop="0.5em",
        paddingRight="0.5em",
        height="22em",
        scrollbars="vertical",
        type="always",
    )


def metric_slider(metric_tag: str, option: str):
    return rx.vstack(
        # Metric
        rx.hstack(
            rx.badge(
                rx.text(
                    metric_tag.capitalize(),
                    font_size="lg",
                    font_weight="medium",
                    size="2",
                ),
                variant="soft",
                radius="small",
                color_scheme="violet",
            ),
            # Current value range
            rx.badge(
                rx.cond(
                    option == "F",
                    f"{State.fundamentals_current_value[metric_tag][0]} - {State.fundamentals_current_value[metric_tag][1]}",
                    f"{State.technicals_current_value[metric_tag][0]} - {State.technicals_current_value[metric_tag][1]}",
                ),
                radius="small",
                variant="solid",
                color_scheme="violet",
            ),
        ),
        rx.slider(
            value=rx.cond(
                option == "F",
                State.fundamentals_current_value[metric_tag],
                State.technicals_current_value[metric_tag],
            ),
            on_change=lambda value_range: rx.cond(
                option == "F",
                State.set_fundamental_metric(
                    metric=metric_tag, value=value_range
                ).throttle(50),
                State.set_technical_metric(
                    metric=metric_tag, value=value_range
                ).throttle(50),
            ),
            min_=0.00,
            max=rx.cond(
                option == "F",
                State.fundamentals_default_value[metric_tag][1],
                State.technicals_default_value[metric_tag][1],
            ),
            step=rx.cond(
                option == "F",
                State.fundamentals_default_value[metric_tag][1] / 100,
                State.technicals_default_value[metric_tag][1] / 100,
            ),
            variant="surface",
            size="2",
            radius="full",
            orientation="horizontal",
        ),
        width="100%",
        align="start",
        padding="1.8em",
    )


def display_sort_options() -> rx.Component:
    asc_icon: rx.Component = rx.icon("arrow-down-a-z", size=13)
    desc_icon: rx.Component = rx.icon("arrow-down-z-a", size=13)

    return rx.fragment(
        rx.menu.root(
            rx.menu.trigger(
                rx.button(
                    rx.hstack(
                        rx.cond(
                            State.selected_sort_order == "ASC", asc_icon, desc_icon
                        ),
                        rx.text("Sort"),
                        align="center",
                    ),
                    variant="outline",
                ),
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
                                        rx.cond(
                                            order == "ASC",
                                            asc_icon,
                                            desc_icon,
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
                f"{item}: {State.fundamentals_current_value.get(item, [0.00, 0.00])[0]}-{State.fundamentals_current_value.get(item, [0.00, 0.00])[1]}",
                rx.cond(
                    filter == "technical",
                    f"{item}: {State.technicals_current_value.get(item, [0.00, 0.00])[0]}-{State.technicals_current_value.get(item, [0.00, 0.00])[1]}",
                    item,
                ),
            ),
            size="2",
            weight="medium",
        ),
        rx.button(
            rx.icon("circle-x", size=11),
            variant="ghost",
            on_click=[
                rx.cond(
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
                State.apply_filters,
            ],
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
