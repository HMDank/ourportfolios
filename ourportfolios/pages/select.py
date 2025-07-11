import reflex as rx
import sqlite3
import pandas as pd

# from ourportfolios.components.loading import loading_wrapper

from ..components.navbar import navbar
from ..components.drawer import drawer_button, CartState
from ..components.page_roller import card_roller, card_link
from ..components.graph import mini_price_graph
from ..utils.load_data import fetch_data_for_symbols


class State(rx.State):
    control: str = "home"
    show_arrow: bool = True
    data: list[dict] = []
    industries: list[str] = []
    offset: int = 0
    limit: int = 8  # Number of ticker cards to show per page

    def update_arrow(self, scroll_position: int, max_scroll: int):
        self.show_arrow = scroll_position < max_scroll - 10

    @rx.var(cache=True)
    def get_all_tickers(self) -> list[dict]:
        conn = sqlite3.connect("ourportfolios/data/data_vni.db")
        df = pd.read_sql("SELECT * FROM data_vni", conn)
        conn.close()
        return df[["ticker", "industry"]].to_dict("records")

    @rx.var(cache=True)
    def paged_tickers(self) -> list[dict]:
        tickers = self.get_all_tickers
        return tickers[self.offset : self.offset + self.limit]

    @rx.var(cache=True)
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

    @rx.event
    def get_all_industries(self):
        conn = sqlite3.connect("ourportfolios/data/data_vni.db")
        industries = pd.read_sql("SELECT DISTINCT industry FROM data_vni;", conn)
        conn.close()
        self.industries = industries["industry"].tolist()


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
                                href=f"/select/{item.lower()}",
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


def ticker_card(df: str):
    ticker = df["ticker"]
    industry = df["industry"]
    return rx.card(
        rx.hstack(
            rx.hstack(
                rx.link(
                    rx.text(ticker, weight="regular", size="4"),
                    href=f"/analyze/{ticker}",
                    style={
                        "textDecoration": "none",
                        "color": "inherit",
                    },
                ),
                rx.badge(
                    f"{industry}",
                    size="2",
                    color_scheme="gray",
                    variant="soft",
                    high_contrast=False,
                ),
                align_items="center",
                spacing="5",
                flex="1",
            ),
            rx.button(
                rx.icon("list-plus", size=16),
                size="1",
                variant="soft",
                on_click=lambda: CartState.add_item(ticker),
            ),
            align_items="center",
            width="100%",
        ),
        padding="1em",
        style={"marginBottom": "0.75em", "width": "100%"},
    )


@rx.page(route="/select", on_load=[State.get_graph([]), State.get_all_industries])
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
                        rx.button("Filter", variant="solid"),
                        width="100%",
                        padding_top="1em",
                    ),
                    rx.card(
                        rx.foreach(
                            State.paged_tickers, lambda ticker: ticker_card(ticker)
                        ),
                        style={"width": "100%", "marginTop": "1em"},
                    ),
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
            ),
            width="100%",
            padding="1em",
            style={"maxWidth": "90vw", "margin": "0 auto"},
        ),
        drawer_button(),
        spacing="0",
    )
