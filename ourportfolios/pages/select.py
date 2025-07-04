import reflex as rx
import sqlite3
import pandas as pd
import itertools
from typing import List, Dict, Any, Optional

from ..components.navbar import navbar
from ..components.drawer import drawer_button, CartState
from ..components.page_roller import card_roller, card_link
from ..components.graph import mini_price_graph, pct_change_badge
from ..utils.load_data import fetch_data_for_symbols


class State(rx.State):
    control: str = "home"
    show_arrow: bool = True
    data: List[Dict] = []
    offset: int = 0
    limit: int = 8  # Number of ticker cards to show per page

    # Search bar
    search_query = ""

    # Metrics
    fundamental_metrics: List[str] = ["pe", "pb", "roe", "alpha", "beta",
                                      "eps", "gross_margin", "net_margin", "ev_ebitda", "dividend_yield"]
    technical_metrics: List[str] = ["rsi14"]

    # Sorts
    selected_sort_order: str = 'ASC'
    selected_sort_option: str = "A-Z"

    sort_orders: List[str] = ['ASC', 'DESC']
    sort_options: List[str] = ['A-Z', 'Market Cap', '% Change', "Volume"]

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
        if (self.selected_industry or self.selected_exchange or self.selected_fundamental_metric or self.selected_technical_metric):
            return True
        return False

    @rx.var(cache=True)
    def get_all_tickers(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect("ourportfolios/data/data_vni.db")

        query = [
            """SELECT ticker, organ_name, current_price, accumulated_volume, pct_price_change 
            FROM data_vni 
            WHERE """]

        if self.search_query != "":
            match_conditions, params = self.fetch_ticker()
            query.append(match_conditions)
        else:
            query.append("1=1")
            params = None

        query = [' '.join(query)]

        # Order and filter
        order_by_clause = ""

        # Filter by industry
        if self.selected_industry:
            query.append(
                f"AND industry IN ({', '.join(f"'{industry}'" for industry in self.selected_industry)})")

        # Filter by exchange
        if self.selected_exchange:
            query.append(
                f"AND exchange IN ({', '.join(f"'{exchange}'" for exchange in self.selected_exchange)})")

        # Order by condition
        if self.selected_sort_option == "A-Z":
            order_by_clause = f"ORDER BY ticker {self.selected_sort_order}"
        if self.selected_sort_option == "Market Cap":
            order_by_clause = f"ORDER BY market_cap {self.selected_sort_order}"
        if self.selected_sort_option == '% Change':
            order_by_clause = f"ORDER BY pct_price_change {self.selected_sort_order}"
        if self.selected_sort_option == 'Volume':
            order_by_clause = f"ORDER BY accumulated_volume {self.selected_sort_order}"

        # Filter by metrics
        if self.selected_fundamental_metric:  # Fundamental
            query.append(
                ' '.join([f"AND {metric} BETWEEN {self.fundamental_metric_filter.get(metric, [0.00, 0.00])[0]} AND {self.fundamental_metric_filter.get(metric, [0.00, 0.00])[1]}" for metric in self.selected_fundamental_metric]))

        if self.selected_technical_metric:  # Technical
            query.append(
                ' '.join([f"AND {metric} BETWEEN {self.technical_metric_filter.get(metric, [0.00, 0.00])[0]} AND {self.technical_metric_filter.get(metric, [0.00, 0.00])[1]}" for metric in self.selected_technical_metric]))

        full_query = " ".join(
            query) + f" {order_by_clause}" if order_by_clause else " ".join(query)

        df = pd.read_sql(full_query, conn, params=params)
        conn.close()

        return df[['ticker', 'organ_name', 'current_price', 'accumulated_volume', 'pct_price_change']].to_dict('records')

    @rx.var(cache=True)
    def get_all_tickers_length(self) -> int:
        return len(self.get_all_tickers)

    # Set all metrics/options to their default setting
    @rx.event
    def get_all_industries(self):
        conn = sqlite3.connect("ourportfolios/data/data_vni.db")
        industries: pd.DataFrame = pd.read_sql(
            "SELECT DISTINCT industry FROM data_vni", con=conn)

        self.industry_filter: Dict[str, bool] = {
            item: False for item in industries['industry'].tolist()}

    @rx.event
    def get_all_exchanges(self):
        conn = sqlite3.connect("ourportfolios/data/data_vni.db")
        exchanges: pd.DataFrame = pd.read_sql(
            "SELECT DISTINCT exchange FROM data_vni", con=conn)

        self.exchange_filter: Dict[str, bool] = {
            item: False for item in exchanges['exchange'].tolist()}

    @rx.event
    def get_fundamental_metrics(self):
        self.fundamental_metric_filter: Dict[str, List[float]] = {
            item: [0.00, 0.00] for item in self.fundamental_metrics}

    @rx.event
    def get_technical_metrics(self):
        self.technical_metric_filter: Dict[str, List[float]] = {
            item: [0.00, 0.00] for item in self.technical_metrics}

    # Page navigation

    @rx.var
    def paged_tickers(self) -> List[Dict]:
        tickers = self.get_all_tickers
        return tickers[self.offset: self.offset + self.limit]

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
    def set_exchange(self, value: bool, exchange: str):
        self.exchange_filter[exchange] = value
        self.selected_exchange = [item[0]
                                  for item in self.exchange_filter.items() if item[1]]

    @rx.event
    def set_industry(self, value: bool, industry: str):
        self.industry_filter[industry] = value
        self.selected_industry = [item[0]
                                  for item in self.industry_filter.items() if item[1]]

    @rx.event
    def set_fundamental_metric(self, metric: str,  value: List[float]):
        self.fundamental_metric_filter[metric] = value
        self.selected_fundamental_metric = [
            item[0] for item in self.fundamental_metric_filter.items() if sum(item[1]) > 0.00]

    @rx.event
    def set_technical_metric(self, metric: str,  value: List[float]):
        self.technical_metric_filter[metric] = value
        self.selected_technical_metric = [
            item[0] for item in self.technical_metric_filter.items() if sum(item[1]) > 0.00]

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
        self.search_query = value

    def fetch_ticker(self) -> tuple[str, Any]:
        # At first, try to fetch exact ticker
        match_conditions = "ticker LIKE ?"
        params = (f"{self.search_query}%", )
        result: bool = self.validate_search_query(
            match_conditions=match_conditions, params=params)

        # In-case of mistype or no ticker returned, calculate all possible permutation of provided search_query with fixed length
        if not result:
            # All possible combination of ticker's letter
            combos = list(itertools.permutations(
                list(self.search_query), len(self.search_query)))
            params = [f"{''.join(combo)}%" for combo in combos]

            match_conditions = " OR ".join(["ticker LIKE ?"] * len(combos))
            result: bool = self.validate_search_query(
                match_conditions=match_conditions, params=params)

        # Suggest base of the first letter if still no ticker matched
        if not result:
            match_conditions = "ticker LIKE ?"
            params = (f"{self.search_query[0]}%", )
            result: bool = self.validate_search_query(
                match_conditions=match_conditions, params=params)

        return match_conditions, params

    def validate_search_query(self, match_conditions: str, params: Any) -> bool:
        """ Attempt to fetch data 
        """
        conn = sqlite3.connect("ourportfolios/data/data_vni.db")
        query: str = f"""
                        SELECT ticker
                        FROM data_vni 
                        WHERE {match_conditions}
                    """
        if pd.read_sql(query, conn, params=params).empty:
            return False
        return True


# Filter section


@rx.page(route="/select", on_load=[
    State.get_graph(['VNINDEX', 'UPCOMINDEX', "HNXINDEX"]),
    State.get_all_industries,
    State.get_all_exchanges,
    State.get_fundamental_metrics,
    State.get_technical_metrics,
    State.set_search_query(""),
])
def index():

    return rx.vstack(
        navbar(),
        page_selection(),
        rx.box(
            rx.hstack(
                rx.vstack(
                    rx.text("asdjfkhsdjf"),
                    industry_roller(),
                    # Filters
                    ticker_filter(),
                    # Tickers info
                    ticker_list(),

                    rx.hstack(
                        rx.button("Previous", on_click=State.prev_page,
                                  disabled=State.offset == 0),
                        rx.button(
                            "Next",
                            on_click=State.next_page,
                            disabled=State.offset + State.limit >= State.get_all_tickers_length,
                        ),
                        spacing="2",
                    ),
                ),
                card_with_scrollable_area(),
                width="100%",
                justify="center",
                spacing="6",
            ),
            width="100%",
            padding="2em",
            padding_top="5em"
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
                        rx.heading("Recommend", weight="bold", size="5"),
                        rx.text("caijdo", size="1"),
                        align="center",
                        justify="center",
                        height="100%",
                        spacing="1"
                    ),
                    align="center",
                    justify="center",
                ),
                href="/recommend",
            ),
            card_link(
                rx.vstack(
                    rx.heading("Select", weight="bold", size="7"),
                    rx.text("caijdo", size="3"),
                    align="center",
                    justify="center",
                    height="100%",
                    spacing="1"
                ),
                href="/select",
            ),
            card_link(
                rx.hstack(
                    rx.vstack(
                        rx.heading("Analyze", weight="bold", size="5"),
                        rx.text("caijdo", size="1"),
                        align="center",
                        justify="center",
                        height="100%",
                        spacing="1"
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
            style={"height": "2em"}
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
    State.get_all_industries()
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
                                href=f'/select/{item[0].lower()}',
                                underline='none',
                            )
                        )
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
    pct_price_change: float
):
    color = rx.cond(pct_price_change.to(int) > 0, rx.color('green', 11), rx.cond(
        pct_price_change.to(int) < 0, rx.color('red', 9), rx.color('gray', 7)))
    return rx.card(
        rx.flex(
            # Column 1: Ticker and organ_name
            rx.box(
                rx.vstack(
                    rx.link(
                        rx.text(ticker, weight="bold", size="4"),
                        href=f"/analyze/{ticker}",
                        style={"textDecoration": "none", "color": "inherit"},
                    ),
                    rx.text(organ_name, color=rx.color('gray', 7), size="2"),
                ),
                width="40%",
            ),
            rx.grid(
                # Column 2: Current price
                rx.box(
                    rx.text(f"{current_price}", weight="medium",
                            size="3", color=color),
                ),
                # Column 3: Percentage change
                rx.box(
                    pct_change_badge(diff=pct_price_change),
                ),
                # Column 4: Accumulated volume
                rx.box(
                    rx.text(f"{accumulated_volume:,.3f}",
                            size="3", weight="medium"),
                ),
                rows="1",
                columns="3",
                width="50%",
                flow="row-dense",
            ),
            # Column 5: Cart button
            rx.box(
                rx.button(
                    rx.icon("shopping-cart", size=16),
                    size="1",
                    variant="soft",
                    on_click=lambda: CartState.add_item(ticker),
                ),
            ),
            width="100%",
            justify="between",
            align="center",
            direction="row",
            wrap="wrap"
        ),
        padding="1em",
        width="100%",
        marginBottom="1em"
    )


def ticker_list():
    return rx.box(
        rx.card(
            rx.flex(
                rx.box(
                    rx.text("Symbol", weight="bold", color="white", size="5"),
                    width="40%",
                    paddingLeft="1em"
                ),
                rx.grid(
                    rx.box(
                        rx.text("Price", weight="bold",
                                color="white", size="5")
                    ),
                    rx.box(
                        rx.text("%", weight="bold", 
                                color="white", size="5")
                    ),
                    rx.box(
                        rx.text("Volume", weight="bold",
                                color="white", size="5")
                    ),
                    rows="1",
                    columns="3",
                    width="50%",
                    flow="row-dense",
                ),
                rx.box(
                ),

                width="100%",
                justify="between",
                align="center",
                direction="row",
                wrap="wrap",
                paddingBottom="1em",
            ),
            rx.foreach(
                State.paged_tickers,
                lambda value: ticker_card(
                    ticker=value.ticker,
                    organ_name=value.organ_name,
                    current_price=value.current_price,
                    accumulated_volume=value.accumulated_volume,
                    pct_price_change=value.pct_price_change
                )
            ),
        ),
        style={
            "backgroundColor": "#000000",
            "borderRadius": "4px",
            "width": "100%",
        },
    ),


def ticker_filter():
    return rx.flex(
        rx.container(
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
            width="40%"
        ),
        rx.spacer(),  # Push filter button far right
        rx.scroll_area(
            selected_filter_tags(),
            scrollbars="horizontal",
            width="40vw",
            type="hover",
            height="2vw",
        ),
        rx.menu.root(
            rx.menu.trigger(
                rx.button(
                    rx.hstack(
                        rx.icon("filter", size=12),
                        rx.text("Filter"),
                        align="center",
                        justify="between"
                    ),
                    variant=rx.cond(
                        State.has_filter,
                        "solid",
                        'outline'
                    ),
                )
            ),
            rx.menu.content(
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger(
                            "Fundamental", value="fundamental"),
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
                                variant='outline',
                                on_click=[State.clear_category_filter,
                                          State.clear_sort_option,
                                          State.clear_fundamental_metric_filter,
                                          State.clear_technical_metric_filter]
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
                avoid_collisions=True
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
            rx.text("Category", size="6", font_weight="bold"),
            rx.spacer(),
            rx.button(
                rx.icon("filter-x", size=15),
                variant='outline',
                on_click=State.clear_category_filter,
            ),
            spacing="2",
            width="100%",
            paddingTop="1em",
            paddingLeft="1em"
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
                            value=value, exchange=item[0])
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
                            value=value, industry=item[0]),
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
    """ Reusable slider section for both fundamentals & technicals
        option(str): {"F": for Fundamental-metrics, 
                       "T" for Technical-metrics}
    """
    return rx.fragment(
        rx.hstack(
            rx.text(rx.cond(option == "F", "Fundamentals:",
                    "Technicals:"), size="6", font_weight="bold"),
            rx.spacer(),
            rx.button(
                rx.icon("filter-x", size=15),
                variant='outline',
                on_click=rx.cond(
                    option == "F", State.clear_fundamental_metric_filter, State.clear_technical_metric_filter),
            ),
            spacing="3",
            width="100%",
            paddingTop="1em",
            paddingLeft="1em"
        ),
        rx.scroll_area(
            rx.flex(
                rx.foreach(
                    rx.cond(option == "F", State.fundamental_metrics,
                            State.technical_metrics),
                    lambda metric_tag: metric_slider(metric_tag, option)
                ),
                direction="row",
                wrap="wrap",
                align="center",
            ),
            height="23vw",
            scrollbars="vertical",
            type="always",
        )
    )


def metric_slider(metric_tag: str, option: str):
    return rx.vstack(
        # Metric
        rx.badge(
            rx.text(metric_tag.capitalize(),
                    font_size="lg",
                    font_weight="bold",
                    size="2"
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
                    State.technical_metric_filter[metric_tag]
                ),
                min_=0,
                max=100,
                on_change=lambda val: rx.cond(
                    option == "F",
                    State.set_fundamental_metric(
                        metric_tag, value=val).throttle(100),
                    State.set_technical_metric(
                        metric_tag, value=val).throttle(100)
                ),
                variant='surface',
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
                                "arrow-down-z-a"
                            ),
                            size=12
                        ),
                        rx.text(State.selected_sort_option),
                        align="center",
                        justify="between"
                    ),
                    variant='outline',
                )
            ),
            rx.menu.content(
                rx.foreach(
                    State.sort_options,
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
                                                "arrow-down-z-a"
                                            ),
                                            size=13
                                        ),
                                        rx.text(order),
                                        align="center",
                                        justify="between"
                                    ),
                                    on_click=[State.set_sort_option(
                                        option), State.set_sort_order(order)]
                                )
                            )
                        )
                    )
                )
            )
        )
    )


def selected_filter_tags():
    return rx.hstack(
        # Industry
        rx.foreach(
            State.selected_industry,
            lambda item: rx.badge(
                rx.hstack(
                    item,
                    rx.button(
                        rx.icon("x", size=12),
                        variant="ghost",
                        size="1",
                        on_click=State.set_industry(False, item)
                    ),
                    spacing="1",
                    align="center"
                ),
                color_scheme="violet",
                radius="large",
                align="center",
                variant="solid",
            ),
        ),

        # Exchange
        rx.foreach(
            State.selected_exchange,
            lambda item: rx.badge(
                rx.hstack(
                    item,
                    rx.button(
                        rx.icon("x", size=12),
                        variant="ghost",
                        size="1",
                        on_click=State.set_exchange(False, item)
                    ),
                    spacing="1",
                    align="center"
                ),
                color_scheme="violet",
                radius="large",
                align="center",
                variant="solid",
            ),
        ),

        # Fundamental metrics
        rx.foreach(
            State.selected_fundamental_metric,
            lambda item: rx.badge(
                rx.hstack(
                    f"{item.upper()}: {State.fundamental_metric_filter.get(item, [0.00, 0.00])[0]} - {State.fundamental_metric_filter.get(item, [0.00, 0.00])[1]}",
                    rx.button(
                        rx.icon("x", size=12),
                        variant="ghost",
                        size="1",
                        on_click=State.set_fundamental_metric(
                            item, [0.00, 0.00])
                    ),
                    spacing="1",
                    align="center"
                ),
                color_scheme="violet",
                radius="large",
                align="center",
                variant="solid",
            ),
        ),

        # Technical metrics
        rx.foreach(
            State.selected_technical_metric,
            lambda item: rx.badge(
                rx.hstack(
                    f"{item.upper()}: {State.technical_metric_filter.get(item, [0.00, 0.00])[0]} - {State.technical_metric_filter.get(item, [0.00, 0.00])[1]}",
                    rx.button(
                        rx.icon("x", size=12),
                        variant="ghost",
                        size="1",
                        on_click=State.set_technical_metric(
                            item, [0.00, 0.00])
                    ),
                    spacing="1",
                    align="center"
                ),
                color_scheme="violet",
                radius="large",
                align="center",
                variant="solid",
            ),
        ),
        width="100%",
        spacing="2",
        direction="row-reverse"
    ),
