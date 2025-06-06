import reflex as rx
import sqlite3
import pandas as pd
from ..components.navbar import navbar
from ..components.drawer import drawer_button, CartState
from ..components.page_roller import card_roller, card_link
from ..components.graph import mini_price_graph
from ..utils.load_data import fetch_data_for_symbols

class State(rx.State):
    control: str = "home"
    show_arrow: bool = True
    data: list[dict] = []
    offset: int = 0
    limit: int = 8  # Number of ticker cards to show per page
    
    # Filter section configuration
    selected_category: str = "All"
    selected_filter: str = "All"
    selected_platform: str = 'All'
    
    categories: list[str] = ["All", "Stock", "Warrant", "Cryptocurrency", "Commodities"]
    filters: list[str] = ['All', 'Market Cap', 'Appreciation', 'Deppreciation', '% Increase']
    platforms: list[str] = ['All', 'HSX', 'HNX', 'UPCOM']

    def update_arrow(self, scroll_position: int, max_scroll: int):
        self.show_arrow = scroll_position < max_scroll - 10

    @rx.var
    def get_all_tickers(self) -> list[dict]:
        conn = sqlite3.connect("ourportfolios/data/data_vni.db")
        
        # Isolate query & clause for dynamic filters and sorting criteria 
        query = ["SELECT ticker, organ_name, current_price, accumulated_volume, price_change, pct_price_change FROM data_vni WHERE 1=1"]
        order_by_clause = ""
        
        # Filter by exchange platform
        if self.selected_platform == 'HSX': query.append(f"AND exchange = 'HSX'")
        if self.selected_platform == 'HNX': query.append(f"AND exchange = 'HNX'")
        if self.selected_platform == 'UPCOM': query.append(f"AND exchange = 'UPCOM'")
        
        # Order by condition
        if self.selected_filter == "Market Cap": order_by_clause = "ORDER BY market_cap DESC"
        if self.selected_filter == '% Increase': order_by_clause = "ORDER BY pct_price_change DESC"
        
        full_query = " ".join(query) + f" {order_by_clause}" if order_by_clause else " ".join(query)
        
        df = pd.read_sql(full_query, conn)
        conn.close()

        return df[['ticker', 'organ_name', 'current_price', 'accumulated_volume', 'price_change', 'pct_price_change']].to_dict('records')

    @rx.var
    def paged_tickers(self) -> list[dict]:
        tickers = self.get_all_tickers
        return tickers[self.offset: self.offset + self.limit]

    @rx.var
    def get_all_tickers_length(self) -> int:
        return len(self.get_all_tickers)

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
    def set_category(self, category):
        self.selected_category = category
        
    @rx.event
    def set_filter(self, filter):
        self.selected_filter = filter
        
    @rx.event
    def set_platform(self, platform):
        self.selected_platform = platform
        

# Filter section
@rx.page(route="/select", on_load=State.get_graph(['VNINDEX', 'UPCOMINDEX', "HNXINDEX"]))
def index():
    return rx.vstack(
        navbar(),
        page_selection(),
        rx.box(
            rx.hstack(
                rx.vstack(
                    rx.text("asdjfkhsdjf"),
                    industry_roller(),
                    rx.hstack(
                        # Left side: Options.. 
                        rx.foreach(State.categories,
                                   lambda category: rx.button(category,
                                        variant=rx.cond(category == State.selected_category, 'solid', 'outline'),
                                        on_click=State.set_category(category))
                                   ),
                        
                        rx.spacer(), # Push the following components to the right
                        
                        # Right side: 
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
                        width="100%",  
                        padding_top="1em",
                        padding_x="1em", 
                        border_radius="8px" 
                    ),
                    rx.card(
                        rx.foreach(
                            State.paged_tickers,
                            lambda value : ticker_card(
                                ticker=value.ticker,
                                organ_name=value.organ_name,
                                current_price=value.current_price,
                                accumulated_volume=value.accumulated_volume,
                                price_change=value.price_change,
                                pct_price_change=value.pct_price_change
                            )
                        ),
                        style={
                            "width": "100%",
                            "marginTop": "1em"
                        }
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


def ticker_card(ticker: str, organ_name: str, current_price: float, accumulated_volume: int, price_change: float, pct_price_change: float):
    
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.link(
                    rx.text(ticker, weight="bold", size="4"),
                    href=f"/analyze/{ticker}",
                    style={
                        "textDecoration": "none",
                        "color": "inherit",
                        "flex": 1,
                    },
                ),  
                rx.text(organ_name, color="var(--gray-7)", size="2"),
            ),
            rx.spacer(),
            rx.button(
                rx.icon("shopping-cart", size=16),
                size="1",
                variant="soft",
                on_click=lambda: CartState.add_item(ticker),
            ),
            align_items="center",
            width="100%"
        ),
        padding="1em",
        style={"marginBottom": "0.75em", "width": "100%"}
    )
    
# ─────────────────────────────────── In construction ───────────────────────────────────

#     #color = rx.cond(price_change > 0, "var(--green-500)", rx.cond(price_change < 0, "var(--red-500)", "var(--gray-7)"))
#     return rx.card(
#         rx.hstack(
#             # ───────────────────────────────────
#             # COLUMN 1: Ticker + Company Name (left‐aligned)
#             rx.vstack(
#                 rx.link(
#                     rx.text(ticker, weight="bold", size="4"),
#                     href=f"/analyze/{ticker}",
#                     style={
#                         "textDecoration": "none",
#                         "color": "inherit",
#                     },
#                 ),
#                 rx.text(organ_name, color="var(--gray-7)", size="2"),
#                 spacing="1",
#                 align_items="flex-start",
#                 width="20%",   # adjust column width as needed
#             ),

#             # ───────────────────────────────────
#             # COLUMN 2: Current Price (right‐aligned)
#             rx.vstack(
#                 rx.text(current_price, weight="bold", size="3"),
#                 spacing="0",
#                 align_items="flex-end",
#                 width="15%",
#             ),

#             # ───────────────────────────────────
#             # COLUMN 3: ± Change / % Change (right‐aligned, colored)
#             rx.vstack(
#                 rx.hstack(
#                     rx.text(price_change, size="2"), #,color=change_color)
#                     rx.text(
#                         pct_price_change,
#                         size="2",
#                         #color=change_color,
#                         style={"marginLeft": "0.5em"},
#                     ),
#                     spacing="1",
#                 ),
#                 spacing="0",
#                 align_items="flex-end",
#                 width="15%",
#             ),

#             # ───────────────────────────────────
#             # COLUMN 4: Total Volume & Add to Cart (right‐aligned)
#             rx.vstack(
#                 rx.text(accumulated_volume, size="2", weight="medium"),
#                 rx.button(
#                     rx.icon("shopping-cart", size=16),
#                     size="1",
#                     variant="soft",
#                     on_click=lambda: CartState.add_item(ticker),
#                 ),
#                 spacing="1",
#                 align_items="flex-end",
#                 width="15%",
#             ),
#             align_items="center",
#             spacing="2",
#             width="100%",
#         ),
#         padding="1em",
#         style={
#             "marginBottom": "0.75em",
#             "width": "100%",
#         },
#     )
    
    
# def ticker_list_header():
#     """
#     Renders a header row with six columns:
#       1) Mã CK        (width 20%)
#       2) Giá          (width 15%)
#       3) +/-          (width 15%)
#       4) %            (width 10%)
#       5) Tổng KL      (width 15%)
#       6) Biểu đồ      (width 25%)
#     """
#     return rx.box(

#         rx.hstack(
#             # Column 1: Mã CK
#             rx.box(rx.text("Mã CK", weight="bold", color="white", size="2"), width="30%"),
#             # Column 2: Giá
#             rx.box(rx.text("Giá", weight="bold", color="white", size="2"), width="20%"),
#             # Column 3: +/-
#             rx.box(rx.text("+/-", weight="bold", color="white", size="2"), width="20%"),
#             # Column 4: %
#             rx.box(rx.text("%", weight="bold", color="white", size="2"), width="15%"),
#             # Column 5: Tổng KL
#             rx.box(rx.text("Tổng KL", weight="bold", color="white", size="2"), width="15%"),
#             spacing="0",
#             width="100%",
#         ),
#         padding="0.75em",
#         style={
#             "backgroundColor": "var(--gray-9)",  
#             "borderRadius": "4px",
#         },
#     )