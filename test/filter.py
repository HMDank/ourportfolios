import reflex as rx
import sqlite3
import pandas as pd
from typing import List, Dict

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
    
    # Metrics
    all_metrics: List[str] = ['PE <', 'PB <', 'ROE >', 'ALPHA >']
    pe_threshold: float = 0.00
    pb_threshold: float = 0.00
    roe_threshold: float = 0.00
    alpha_threshold: float = 0.00
    
    # Other filter
    selected_category: str = "All"
    selected_filter: str = "All"
    selected_platform: str = 'All'
    selected_industries: str = 'All'
    
    filters: List[str] = ['All', 'Market Cap', '% Increase']
    platforms: List[str] = ['All', 'HSX', 'HNX']
    industries: List[str] = []
    
    def update_arrow(self, scroll_position: int, max_scroll: int):
        self.show_arrow = scroll_position < max_scroll - 10

    @rx.var
    def get_all_tickers(self) -> List[Dict]:
        conn = sqlite3.connect("ourportfolios/data/data_vni.db")
        
        # Isolate query & clause for dynamic filters and sorting criteria 
        query = ["SELECT ticker, organ_name, current_price, accumulated_volume, pct_price_change FROM data_vni WHERE 1=1"]
        order_by_clause = ""
        
        # Filter by industry
        if not self.selected_industries == 'All': query.append(f"AND industry = {self.selected_industries}")
        
        # Filter by exchange platform
        if self.selected_platform != 'All': query.append(f"AND exchange = {self.selected_platform}")
        
        # Order by condition
        if self.selected_filter == "Market Cap": order_by_clause = "ORDER BY market_cap DESC"
        if self.selected_filter == '% Increase': order_by_clause = "ORDER BY pct_price_change DESC"
        
        # Filter by metrics
        if self.pe_threshold > 0: query.append(f"AND pe < {self.pe_threshold}")
        if self.pb_threshold > 0: query.append(f"AND pb < {self.pb_threshold}")
        if self.roe_threshold > 0: query.append(f"AND roe > {self.roe_threshold}")
        if self.alpha_threshold > 0: query.append(f"AND alpha < {self.alpha_threshold}")
                       
        full_query = " ".join(query) + f" {order_by_clause}" if order_by_clause else " ".join(query)
        
        df = pd.read_sql(full_query, conn)
        conn.close()

        return df[['ticker', 'organ_name', 'current_price', 'accumulated_volume', 'pct_price_change']].to_dict('records')

    @rx.var
    def paged_tickers(self) -> List[Dict]:
        tickers = self.get_all_tickers
        return tickers[self.offset: self.offset + self.limit]

    @rx.var
    def get_all_tickers_length(self) -> int:
        return len(self.get_all_tickers)
    
    @rx.event
    def get_current_metric_value(self, metric_tag: str):
        if metric_tag == 'pe': return self.pe_threshold
        if metric_tag == 'pb': return self.pb_threshold
        if metric_tag == 'roe': return self.roe_threshold
        if metric_tag == 'alpha': return self.alpha_threshold
    
    @rx.event
    def get_industries(self) -> List[str]:
        conn = sqlite3.connect("ourportfolios/data/data_vni.db")
        industries: pd.DataFrame = pd.read_sql("SELECT DISTINCT industry FROM data_vni", con=conn)
        return industries['industry'].tolist()

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
        self.selected_filter = filter
        
    @rx.event
    def set_platform(self, platform):
        self.selected_platform = platform
        
    @rx.event 
    def add_industry(self, target_industry: str):
        self.selected_industries = target_industry
    
    @rx.event 
    def set_metric(self, metric: str,  value: float):
        if not value: value = 0.00
        if metric == "pe": self.pe_threshold = value
        if metric == "pb": self.pb_threshold = value
        if metric == "roe": self.roe_threshold = value
        if metric == "alpha": self.alpha_threshold = value
        
# Filter section
@rx.page(route="/select", on_load=[
    State.get_graph(['VNINDEX', 'UPCOMINDEX', "HNXINDEX"]),
    State.get_industries
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
                    
                    rx.box(
                        ticker_filter(),
                        ticker_list(),
                        style={
                            "width":"100%",
                        },
                    ),
                    
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
    return rx.center(
        card_roller(
            card_link(
                rx.hstack(
                    rx.icon("chevron_left", size=32),
                    rx.vstack(
                        rx.heading("Recommend", weight="bold", size="6"),
                        rx.text("caijdo", size="1"),
                        align="center",
                        justify="center",
                        height="100%",
                    ),
                    align="center",
                    justify="center",
                ),
                href="/recommend",
            ),
            card_link(
                rx.vstack(
                    rx.heading("Select", weight="bold", size="8"),
                    rx.text("caijdo", size="3"),
                    align="center",
                    justify="center",
                    height="100%",
                ),
                href="/select",
            ),
            card_link(
                rx.hstack(
                    rx.vstack(
                        rx.heading("Analyze", weight="bold", size="6"),
                        rx.text("caijdo", size="1"),
                        align="center",
                        justify="center",
                        height="100%",
                    ),
                    rx.icon("chevron_right", size=32),
                    align="center",
                    justify="center",
                ),
                href="/simulate",
            ),
        ),
        min_height="0vh",
        width="100%",
        align_items="center",
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
    industries = [
        {"name": "Technology", "desc": "Software, hardware, and IT services", "img": ""},
        {"name": "Finance", "desc": "Banking, investment, and insurance", "img": ""},
        {"name": "Healthcare", "desc": "Pharmaceuticals, hospitals, and biotech", "img": ""},
        {"name": "Energy", "desc": "Oil, gas, and renewables", "img": ""},
        {"name": "Consumer Goods", "desc": "Food, beverages, and retail", "img": ""},
        {"name": "Industrials", "desc": "Manufacturing and infrastructure", "img": ""},
        {"name": "Utilities", "desc": "Electric, water, and gas utilities", "img": ""},
        {"name": "Telecommunications",
            "desc": "Mobile, broadband, and satellite", "img": ""},
        {"name": "Real Estate", "desc": "Commercial and residential properties", "img": ""},
        {"name": "Materials", "desc": "Mining, chemicals, and forestry", "img": ""},
    ]

    return rx.box(
        rx.box(
            rx.scroll_area(
                rx.hstack(
                    rx.foreach(
                        industries,
                        lambda item: rx.card(
                            rx.inset(
                                rx.image(
                                    src=item["img"],
                                    width="40px",
                                    height="40px",
                                    style={"marginBottom": "0.5em"},
                                ),
                                item["name"],
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
    color = rx.cond(pct_price_change.to(int) > 0, rx.color('green', 11), rx.cond(pct_price_change.to(int) < 0, rx.color('red', 9), rx.color('gray', 7)))
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
                rx.text(f"{current_price.to(int)*1e-3:.2f}", weight="medium", size="3", color=color),
                width="15%",
                align="center",
                justify="center",
            ),
            # Column 3: Percentage change
            rx.box(
                rx.text(f"{pct_price_change:.2f}%", weight="medium", size="2", color=color),
                font_style="italic",
                width="20%",
                align="center",
                justify="center",
            ),
            # Column 4: Accumulated volume
            rx.box(
                rx.text(f"{accumulated_volume:,.3f}", size="3", weight="medium"),
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
            spacing="1",
        ),
        padding="1em",
        style={"marginBottom": "0.75em", "width": "100%"}
    )
    
def ticker_list():
    return rx.box(
            rx.card(
                rx.hstack(
                    rx.box(rx.text("Mã CK", weight="bold", color="white", size="3"), width="50%", align="center", justify="center"),
                    rx.box(rx.text("Giá", weight="bold", color="white", size="3"), width="15%", align="center", justify="center"),
                    rx.box(rx.text("%", weight="bold", color="white", size="3"), width="17%", align="center", justify="center"),
                    rx.box(rx.text("Tổng KL", weight="bold", color="white", size="3"), width="18%", align="center", justify="center"),
                    width="100%",
                    padding="1em",
                    align_items="center",
                ),
                rx.foreach(
                    State.paged_tickers,
                    lambda value : ticker_card(
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
    return rx.box(
        rx.hstack(
            # Industry filter
            rx.dropdown_menu.root(
                rx.dropdown_menu.trigger(
                    rx.button(
                        rx.cond(State.selected_industries != 'All', State.selected_industries, 'Industry'),
                        variant=rx.cond(State.selected_industries != 'All', 'solid', 'outline')
                    )
                ),
                rx.dropdown_menu.content(
                    rx.text("Fundamentals:", size="6", font_weight="bold"),
                    rx.hstack(
                        rx.foreach(
                            State.all_metrics,
                            lambda metric: metric_button(metric=metric)
                        ),
                        spacing='2',
                        align='center',
                        width='100%',
                        justify='between',
                        paddingTop='1em',
                    ),
                    justify='center',
                )
            ),
            rx.spacer(), # Push the following components to the right
            
            # Platform selector
            rx.dropdown_menu.root(
                rx.dropdown_menu.trigger(
                    rx.button(
                        rx.cond(State.selected_platform != 'All', State.selected_platform, "Exchange Platform"), 
                        variant=rx.cond(State.selected_platform != 'All', 'solid', 'outline')
                    )  
                ),
                    
                rx.dropdown_menu.content(
                    rx.foreach(
                        State.platforms,
                        lambda platform: rx.dropdown_menu.item(
                            rx.hstack(
                                rx.cond(
                                    platform == State.selected_platform, 
                                    rx.icon('check', size=16),
                                    rx.box(width='16px')
                                ),
                                rx.text(platform, weight=rx.cond(platform == State.selected_platform, "bold", "normal")),
                                spacing="2",
                                align="center",
                            ),
                            on_select=State.set_platform(platform)
                        )
                    )
                )
            ),
            # Filter
            rx.dropdown_menu.root(
                rx.dropdown_menu.trigger(
                    rx.button(
                        rx.cond(State.selected_filter != 'All', State.selected_filter, "Filter"),
                        variant=rx.cond(State.selected_filter != 'All', 'solid', 'outline')
                    )
                ),
                rx.dropdown_menu.content(
                    rx.foreach(
                        State.filters,
                        lambda filter: rx.dropdown_menu.item(
                            rx.hstack(
                                rx.cond(
                                    filter == State.selected_filter,
                                    rx.icon("check", size=16),
                                    rx.box(width="16px")
                                ),
                                rx.text(filter, weight=rx.cond(filter == State.selected_filter, "bold", "normal")),
                                spacing="2",
                                align="center",
                            ),
                            on_select=State.set_filter(filter)
                        )
                    )
                )
            ),
            padding_bottom="1em",
            padding_x="1em", 
            border_radius="8px" 
        ),
        width='100%'
    )
    
def metric_button(metric: str):
    # a tag to assign button -> metric
    metric_tag: str = ''.join([x for x in metric if x.isalnum()]).lower()
    return rx.box(
        rx.badge(
            rx.text(metric, font_size="lg", font_weight="bold", size="3"),
            variant="soft",
            border_radius="full",
            box_shadow="md",
            color_scheme="violet"
        ),
        rx.input(
            title=metric,
            type="number",
            min=0,
            value=State.get_current_metric_value(metric_tag=metric_tag),
            placeholder="e.g 1.0",
            on_change=lambda val: State.set_metric(metric=metric_tag, value=rx.cond(val, val.to(float), None)),
            style={"width": "5rem", "marginRight": "1rem"},
        ),
    )