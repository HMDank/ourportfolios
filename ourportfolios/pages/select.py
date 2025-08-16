import reflex as rx
import pandas as pd
import itertools

from typing import List, Dict, Any
from sqlalchemy import text

from ..components.navbar import navbar
from ..components.drawer import drawer_button, CartState
from ..components.page_roller import card_roller, card_link
from ..components.graph import mini_price_graph, pct_change_badge
from ..utils.load_data import fetch_data_for_symbols
from ..utils.scheduler import db_settings


class State(rx.State):
    control: str = "home"
    show_arrow: bool = True
    data: List[Dict] = []
    offset: int = 0
    limit: int = 8  # Number of ticker cards to show per page

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
        query = [
            """SELECT ticker, organ_name, current_price, accumulated_volume, pct_price_change 
            FROM comparison.comparison_df 
            WHERE """
        ]

        if self.search_query != "":
            match_conditions, params = self.get_suggest_ticker()
            query.append(match_conditions)
        else:
            query.append("1=1")
            params = None

        query = [" ".join(query)]

        # Order and filter
        order_by_clause = ""

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

        # Order by condition
        if self.selected_sort_option:
            order_by_clause = f"ORDER BY {self.sort_options[self.selected_sort_option]} {self.selected_sort_order}"

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

        full_query = text(
            " ".join(query) + f" {order_by_clause}"
            if order_by_clause
            else " ".join(query)
        )

        df = pd.read_sql(full_query, db_settings.conn, params=params)

        return df[
            [
                "ticker",
                "organ_name",
                "current_price",
                "accumulated_volume",
                "pct_price_change",
            ]
        ].to_dict("records")

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

    # Page navigation

    @rx.var
    def paged_tickers(self) -> List[Dict]:
        tickers = self.get_all_tickers
        return tickers[self.offset : self.offset + self.limit]

    @rx.event
    def next_page(self):
        if self.offset + self.limit < len(self.get_all_tickers):
            self.offset += self.limit

    @rx.event
    def prev_page(self):
        if self.offset - self.limit >= 0:
            self.offset -= self.limit

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

    def get_suggest_ticker(self) -> tuple[str, Any]:
        # At first, try to fetch exact ticker
        match_query = "ticker LIKE :pattern"
        match_params = {"pattern": f"{self.search_query}%"}
        result: bool = self.fetch_ticker(
            match_conditions=match_query, params=match_params
        )

        # In-case of mistype or no ticker returned, calculate all possible permutation of provided search_query with fixed length
        if not result:
            # All possible combination of ticker's letter
            combos = list(
                itertools.permutations(list(self.search_query), len(self.search_query))
            )

            match_query = (
                " OR ".join(
                    [f"ticker LIKE :pattern_{i}" for i in range(len(match_params))]
                ),
            )
            match_params = {
                f"pattern_{idx}": f"{''.join(combo)}%"
                for idx, combo in enumerate(combos)
            }

            result: pd.DataFrame = self.fetch_ticker(
                match_conditions=match_query,
                params=match_params,
            )

        # Suggest base of the first letter if still no ticker matched
        if not result:
            match_query = "ticker LIKE :pattern"
            match_params = {"pattern": f"{self.search_query[0]}%"}
            result: bool = self.fetch_ticker(
                match_conditions=match_query, params=match_params
            )

        return match_query, match_params

    def fetch_ticker(self, match_conditions: str, params: Any) -> bool:
        """Attempt to fetch data"""
        query: str = text(f"""
                        SELECT ticker
                        FROM comparison.comparison_df 
                        WHERE {match_conditions}
                    """)
        if pd.read_sql(query, db_settings.conn, params=params).empty:
            return False
        return True


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
                rx.hstack(
                    rx.button(
                        "Previous",
                        on_click=State.prev_page,
                        disabled=State.offset == 0,
                    ),
                    rx.button(
                        "Next",
                        on_click=State.next_page,
                        disabled=State.offset + State.limit
                        >= State.get_all_tickers_length,
                    ),
                    spacing="2",
                ),
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
):
    color = rx.cond(
        pct_price_change.to(int) > 0,
        rx.color("green", 11),
        rx.cond(pct_price_change.to(int) < 0, rx.color("red", 9), rx.color("gray", 7)),
    )
    return rx.card(
        rx.flex(
            # Basic info
            rx.flex(
                # Ticker and organ_name
                rx.box(
                    rx.link(
                        rx.text(ticker, weight="medium", size="4"),
                        href=f"/analyze/{ticker}",
                        style={"textDecoration": "none", "color": "inherit"},
                    ),
                    rx.text(organ_name, color=rx.color("gray", 7), size="2"),
                    align="center",
                    justify="start",
                    width="40%",
                ),
                rx.flex(
                    # Current price
                    # Percentage change
                    # Accumulated volume
                    rx.foreach(
                        [
                            rx.text(
                                f"{current_price}",
                                weight="regular",
                                size="3",
                                color=color,
                            ),
                            pct_change_badge(diff=pct_price_change),
                            rx.text(
                                f"{accumulated_volume:,.3f}", size="3", weight="regular"
                            ),
                        ],
                        lambda item: rx.stack(
                            item,
                            width="30%",
                            justify="end",
                            align="center",
                        ),
                    ),
                    direction="row",
                    align="center",
                    justify="between",
                    width="70%",
                    spacing="2",
                ),
                direction="row",
                width="80%",
            ),
            # Cart button
            rx.stack(
                rx.button(
                    rx.icon("shopping-cart", size=16),
                    size="1",
                    variant="soft",
                    on_click=lambda: CartState.add_item(ticker),
                ),
                align="center",
                justify="end",
                width="20%",
            ),
            direction="row",
            width="100%",
        ),
        padding="1em",
        width="100%",
        marginBottom="1em",
    )


def ticker_basic_info():
    return rx.box(
        rx.card(
            rx.flex(
                # Header
                rx.flex(
                    # Ticker and organ_name
                    rx.box(
                        rx.text("Symbol", weight="medium", color="white", size="5"),
                        align="center",
                        justify="start",
                        width="40%",
                    ),
                    rx.flex(
                        rx.foreach(
                            # Current price
                            # Percentage change
                            # Accumulated volume
                            ["Price", "%", "Volume"],
                            lambda label: rx.stack(
                                rx.text(
                                    label, weight="medium", color="white", size="5"
                                ),
                                width="30%",
                                justify="end",
                                align="center",
                            ),
                        ),
                        direction="row",
                        justify="between",
                        align="center",
                        width="70%",
                        spacing="2",
                    ),
                    direction="row",
                    width="80%",
                ),
                # Placeholder for cart
                rx.stack(
                    width="20%",
                    variant="ghost",
                ),
                direction="row",
                width="100%",
                padding="1em",
            ),
            # Ticker
            rx.foreach(
                State.paged_tickers,
                lambda value: ticker_card(
                    ticker=value.ticker,
                    organ_name=value.organ_name,
                    current_price=value.current_price,
                    accumulated_volume=value.accumulated_volume,
                    pct_price_change=value.pct_price_change,
                ),
            ),
        ),
        background_color="#000000F2",  # black A12
        border_radius=6,
        width="100%",
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
            width="40%",
            height="auto",
            align="center",
        ),
        # Selected filter option
        rx.scroll_area(
            display_selected_filter(),
            scrollbars="horizontal",
            type="hover",
            width="40vw",
            height="auto",
            align="center",
        ),
        rx.spacer(),  # Push filter button far right
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
                            # Sort
                            display_sort_options(),
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
                width="60vw",
                height="30vw",
                side="left",
            ),
            modal=False,
        ),
        width="100%",
        align="center",
        direction="row",
        spacing="2",
    )


def category_filter():
    return rx.vstack(
        rx.hstack(
            rx.text("Category", size="6", font_weight="medium"),
            rx.spacer(),
            rx.button(
                rx.icon("filter-x", size=15),
                variant="outline",
                on_click=State.clear_category_filter,
            ),
            spacing="2",
            width="100%",
            paddingTop="1em",
            paddingLeft="1em",
        ),
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
                spacing="3",
                flow="row-dense",
                align="center",
                paddingLeft="2em",
            ),
        ),
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
                    ),
                ),
                rows=f"{State.industry_filter.length() // 4}",
                columns="4",
                spacing="3",
                flow="row-dense",
                align="center",
                paddingLeft="2em",
            ),
        ),
        spacing="5",
        width="100%",
    )


def metrics_filter(option: str = "F") -> rx.Component:
    """Reusable slider section for both fundamentals & technicals
    option(str): {"F": for Fundamental-metrics,
                   "T" for Technical-metrics}
    """
    return rx.fragment(
        rx.hstack(
            rx.text(
                rx.cond(option == "F", "Fundamentals:", "Technicals:"),
                size="6",
                font_weight="medium",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("filter-x", size=15),
                variant="outline",
                on_click=rx.cond(
                    option == "F",
                    State.clear_fundamental_metric_filter,
                    State.clear_technical_metric_filter,
                ),
            ),
            spacing="3",
            width="100%",
            paddingTop="1em",
            paddingLeft="1em",
        ),
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
        padding="3em",
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
                            size=12,
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
