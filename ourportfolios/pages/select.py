import reflex as rx
import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional

from ..components.navbar import navbar
from ..components.drawer import drawer_button, CartState
from ..components.page_roller import card_roller, card_link
from ..components.graph import mini_price_graph
from ..utils.load_data import fetch_data_for_symbols


class State(rx.State):
    control: str = "home"
    show_arrow: bool = True
    data: List[Dict] = []
    offset: int = 0
    limit: int = 8  # Number of ticker cards to show per page

    # Search bar
    search_query = ""

    pe_threshold: List[float] = [0.00, 0.00]
    pb_threshold: List[float] = [0.00, 0.00]
    roe_threshold: List[float] = [0.00, 0.00]
    alpha_threshold: List[float] = [0.00, 0.00]
    beta_threshold: List[float] = [0.00, 0.00]
    eps_threshold: List[float] = [0.00, 0.00]
    gross_margin_threshold: List[float] = [0.00, 0.00]
    net_margin_threshold: List[float] = [0.00, 0.00]
    ev_ebitda_threshold: List[float] = [0.00, 0.00]
    dividend_yield_threshold: List[float] = [0.00, 0.00]

    # Other filter
    selected_category: str = "All"
    selected_technical: str = "All"
    selected_exchange: str = 'All'
    selected_industry: str = 'All'

    filters: List[str] = ['All', 'Market Cap', '% Increase']
    exchanges: List[str] = ['All', 'HSX', 'HNX']
    industries: List[str] = []

    def update_arrow(self, scroll_position: int, max_scroll: int):
        self.show_arrow = scroll_position < max_scroll - 10

    @rx.var(cache=True)
    def get_all_tickers(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect("ourportfolios/data/data_vni.db")

        # Isolate query & clause for dynamic filters and sorting criteria
        query = [
            "SELECT ticker, organ_name, current_price, accumulated_volume, pct_price_change FROM data_vni WHERE 1=1"]
        order_by_clause = ""

        # Filter by industry
        if not self.selected_industry == 'All':
            query.append(f"AND industry = '{self.selected_industry}'")

        # Filter by exchange platform
        if self.selected_exchange != 'All':
            query.append(f"AND exchange = '{self.selected_exchange}'")

        # Order by condition
        if self.selected_technical == "Market Cap":
            order_by_clause = "ORDER BY market_cap DESC"
        if self.selected_technical == '% Increase':
            order_by_clause = "ORDER BY pct_price_change DESC"

        # Filter by metrics
        if self.pe_threshold[1] > 0:
            query.append(
                f"AND pe BETWEEN {self.pe_threshold[0]} AND {self.pe_threshold[1]}")
        if self.pb_threshold[1] > 0:
            query.append(
                f"AND pb BETWEEN {self.pb_threshold[0]} AND {self.pb_threshold[1]}")
        if self.roe_threshold[1] > 0:
            query.append(
                f"AND roe BETWEEN {self.roe_threshold[0]} AND {self.roe_threshold[1]}")
        if self.alpha_threshold[1] > 0:
            query.append(
                f"AND alpha BETWEEN {self.alpha_threshold[0]} AND {self.alpha_threshold[1]}")

        full_query = " ".join(
            query) + f" {order_by_clause}" if order_by_clause else " ".join(query)
        df = pd.read_sql(full_query, conn)
        conn.close()

        return df[['ticker', 'organ_name', 'current_price', 'accumulated_volume', 'pct_price_change']].to_dict('records')

    @rx.var(cache=True)
    def get_all_tickers_length(self) -> int:
        return len(self.get_all_tickers)

    # @rx.var
    # def get_current_screener_filter(self) -> str:
    #     filters: List[str] = []
    #     if self.selected_category != 'All':
    #         filters.append(self.selected_category)
    #     if self.selected_industry != 'All':
    #         filters.append(self.selected_industry)
    #     if self.selected_technical != 'All':
    #         filters.append(self.selected_technical)
    #     if self.selected_exchange != 'All':
    #         filters.append(self.selected_exchange)

    #     return " | ".join(filters)

    # @rx.var
    # def get_current_fundamental_filter(self, metric: str) -> str:
    #     if metric.lower() == "pe":
    #         return f"PE: {self.pe_threshold[0]} <-> {self.pe_threshold[1]}"
    #     if metric.lower() == "pb":
    #         return f"PB: {self.pb_threshold[0]} <-> {self.pb_threshold[1]}"
    #     if metric.lower() == "roe":
    #         return f"ROE: {self.roe_threshold[0]} <-> {self.roe_threshold[1]}"
    #     if metric.lower() == "alpha":
    #         return f"ALPHA: {self.alpha_threshold[0]} <-> {self.alpha_threshold[1]}"

    @rx.event
    def get_all_industries(self):
        conn = sqlite3.connect("ourportfolios/data/data_vni.db")
        industries: pd.DataFrame = pd.read_sql(
            "SELECT DISTINCT industry FROM data_vni", con=conn)
        self.industries = ['All']
        self.industries.extend(industries['industry'].tolist())

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
    def set_filter(self, filter):
        self.selected_technical = filter

    @rx.event
    def set_platform(self, platform):
        self.selected_exchange = platform

    @rx.event
    def set_industry(self, industry: str):
        self.selected_industry = industry

    @rx.event
    def clear_screener_filter(self):
        self.selected_category = self.selected_technical = self.selected_industry = self.selected_exchange = "All"

    @rx.event
    def clear_fundamental_filter(self):
        self.pe_threshold = self.pb_threshold = self.roe_threshold = self.alpha_threshold = [
            0.00, 0.00]

    @rx.event
    def set_metric(self, metric: str,  value: List[float]):
        if metric == "pe":
            self.pe_threshold = value
        if metric == "pb":
            self.pb_threshold = value
        if metric == "roe":
            self.roe_threshold = value
        if metric == "alpha":
            self.alpha_threshold = value
        if metric == "beta":
            self.beta_threshold = value
        if metric == "eps":
            self.eps_threshold = value
        if metric == "gross_margin":
            self.gross_margin_threshold = value
        if metric == "net_margin":
            self.net_margin_threshold = value
        if metric == "ev_ebitda":
            self.ev_ebitda_threshold = value
        if metric == "dividend_yield":
            self.dividend_yield_threshold = value


# Filter section
@rx.page(route="/select", on_load=[
    State.get_graph(['VNINDEX', 'UPCOMINDEX', "HNXINDEX"]),
    State.get_all_industries
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
                        State.industries,
                        lambda item: rx.card(
                            rx.link(
                                rx.inset(
                                    rx.image(
                                        src="/placeholder-industry.png",  # ✅ Use placeholder or map industries to images
                                        width="40px",
                                        height="40px",
                                        style={"marginBottom": "0.5em"},
                                    ),
                                    item,
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
                                href=f'/select/{item.lower()}',
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
        rx.hstack(
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
                width="50%",
                align="end",
                justify="center",
            ),
            # Column 2: Current price
            rx.box(
                rx.text(f"{current_price}", weight="medium",
                        size="3", color=color),
                width="15%",
                align="center",
                justify="center",
            ),
            # Column 3: Percentage change
            rx.box(
                rx.text(f"{pct_price_change}%",
                        weight="medium", size="2", color=color),
                font_style="italic",
                width="20%",
                align="center",
                justify="center",
            ),
            # Column 4: Accumulated volume
            rx.box(
                rx.text(f"{accumulated_volume:,.3f}",
                        size="3", weight="medium"),
                width="15%",
                align="center",
                justify="center",
            ),
            # Column 5: Cart button
            rx.box(
                rx.button(
                    rx.icon("shopping-cart", size=16),
                    size="1",
                    variant="soft",
                    on_click=lambda: CartState.add_item(ticker),
                ),
                width="auto",
                align="center",
                justify="center",
            ),
            width="100%",
            align_items="center",
            spacing="2",
        ),
        padding="1em",
        style={"marginBottom": "0.75em", "width": "100%"}
    )


def ticker_list():
    return rx.box(
        rx.card(
            rx.hstack(
                rx.box(rx.text("Mã CK", weight="bold", color="white",
                               size="3"), width="50%", align="center", justify="center"),
                rx.box(rx.text("Giá", weight="bold", color="white", size="3"),
                       width="15%", align="center", justify="center"),
                rx.box(rx.text("%", weight="bold", color="white", size="3"),
                       width="17%", align="center", justify="center"),
                rx.box(rx.text("Tổng KL", weight="bold", color="white",
                               size="3"), width="18%", align="center", justify="center"),
                width="100%",
                padding="1em",
                align_items="center",
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
    return rx.hstack(
        rx.spacer(),  # Push filter button far right
        rx.menu.root(
            rx.menu.trigger(
                rx.button(
                    rx.hstack(
                        rx.icon("filter", size=12),
                        rx.text("Filter"),
                        align="center",
                        justify="between"
                    ),
                    variant='outline'
                )
            ),
            rx.menu.content(
                rx.fragment(
                    rx.tabs.root(
                        rx.tabs.list(
                            rx.tabs.trigger(
                                "Fundamental", value="fundamental"),
                            rx.tabs.trigger("Industry", value="industry"),
                            rx.tabs.trigger("Technical", value="technical"),
                        ),
                        rx.scroll_area(
                            rx.tabs.content(
                                fundamentals_filter(),
                                value="fundamental",
                            ),
                            rx.tabs.content(
                                screener_filter(),
                                value="industry",
                            ),
                            rx.tabs.content(
                                rx.text("item on tab 2"),
                                value="technical",
                            ),
                        ),
                        default_value="fundamental",
                    )
                ),
                side='left',
                width="50vw",
                height="25vw",
            )
        ),
        width="100%"
    )


def screener_filter():
    return rx.hstack(
        rx.vstack(
            rx.scroll_area(
                rx.foreach(
                    State.industries,
                    lambda industry: rx.text(industry)
                ),
                spacing="3",
            ),
        ),
        rx.vstack(
            rx.scroll_area(
                rx.foreach(
                    State.exchanges,
                    lambda exchange: rx.text(exchange)
                ),
                spacing="3"
            ),
        ),
        width="100%",
        padding="1em",
        justify="between",
        align='start'
    ),


def fundamentals_filter() -> rx.Component:
    return rx.fragment(
        rx.hstack(
            rx.text("Fundamentals:", size="6", font_weight="bold"),
            rx.spacer(),
            rx.button(
                rx.icon("filter-x", size=15),
                variant='outline',
                on_click=[State.clear_fundamental_filter,
                          State.clear_screener_filter]
            ),
            spacing="2",
            width="100%",
            paddingTop="1em",
        ),
        rx.vstack(
            # PE
            rx.hstack(
                metric_badge(
                    tag=f"{State.pe_threshold[0]} < PE < {State.pe_threshold[1]}"),
                rx.slider(
                    default_value=[0.00, 0.00],
                    value=State.pe_threshold,
                    min_=0,
                    max=100,
                    on_change=lambda value: State.set_metric(
                        "pe", rx.cond(value, value.to(float), None)).throttle(10),
                    variant='soft',
                    size="1",
                    radius="small",
                ),
                width="100%",
                align="center",
                justify="between",
                padding="1em",
            ),
            # PB
            rx.hstack(
                metric_badge(
                    tag=f"{State.pb_threshold[0]} < PB < {State.pb_threshold[1]}"),
                rx.slider(
                    default_value=[0, 100],
                    value=State.pb_threshold,
                    min_=0,
                    max=100,
                    on_change=lambda value: State.set_metric(
                        "pb", rx.cond(value, value.to(float), None)).throttle(10),
                    variant='soft',
                    size="1",
                    radius="small",
                ),
                width="100%",
                align="center",
                justify="between",
                padding="1em",
            ),

            # ROE
            rx.hstack(
                metric_badge(
                    tag=f"{State.roe_threshold[0]} < ROE < {State.roe_threshold[1]}"),
                rx.slider(
                    default_value=[0, 100],
                    value=State.roe_threshold,
                    min_=0,
                    max=100,
                    on_change=lambda value: State.set_metric(
                        "roe", rx.cond(value, value.to(float), None)).throttle(10),
                    variant='soft',
                    size="1",
                    radius="small",
                ),
                width="100%",
                align="center",
                padding="1em",
            ),
            # ALPHA
            rx.hstack(
                metric_badge(
                    tag=f"{State.alpha_threshold[0]} < ALPHA < {State.alpha_threshold[1]}"),
                rx.slider(
                    default_value=[0, 100],
                    value=State.alpha_threshold,
                    min_=0,
                    max=100,
                    on_change=lambda value: State.set_metric(
                        "alpha", rx.cond(value, value.to(float), None)).throttle(10),
                    variant='soft',
                    size="1",
                    radius="small",
                ),
                width="100%",
                align="center",
                justify="between",
                padding="1em",
            ),
            spacing='1',
            width='100%',
            justify='end',
        ),
    )


def metric_badge(tag: str):
    return rx.badge(
        rx.text(tag, font_size="lg", font_weight="bold", size="2"),
        variant="soft",
        radius="full",
        box_shadow="md",
        color_scheme="violet",
    )
