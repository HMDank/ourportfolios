import reflex as rx
import pandas as pd
import sqlite3
from ..components.navbar import navbar
from ..components.link_cards import portfolio_card
from ..components.graph import mini_price_graph
from ..utils.load_data import fetch_data_for_symbols

cards = [
    {"title": "Recommend", "details": "Card 1 details",
        "link": "/recommend"},
    {"title": "Select", "details": "Card 2 details",
        "link": "/select"},
    {"title": "Analyze", "details": "Card 3 details", "link": "/analyze"},
    {"title": "Simulate", "details": "Card 4 details",
        "link": "/simulate"},
]


class State(rx.State):
    show_cards: bool = False
    data: list[dict] = []

    @rx.var
    def data_vni(self) -> pd.DataFrame:
        conn = sqlite3.connect("ourportfolios/data/data_vni.db")
        df = pd.read_sql("SELECT * FROM data_vni", conn)
        conn.close()
        return df

    @rx.event
    def get_graph(self, ticker_list):
        self.data = fetch_data_for_symbols(ticker_list)


@rx.page(route="/", on_load=State.get_graph(['VNINDEX']))
def landing() -> rx.Component:
    return rx.fragment(
        navbar(
            rx.foreach(
                State.data,
                lambda data: mini_price_graph(
                    label=data["label"],
                    data=data["data"],
                    diff=data["percent_diff"],
                ),
            ),
        ),

        rx.vstack(
            rx.center(
                rx.vstack(
                    rx.heading(
                        "OurPortfolios",
                        size="9",
                        font_size="5rem"
                    ),
                    rx.text("Build your portfolios. We'll build ours"),
                    spacing="5",
                    align="center",
                ),
                height="calc(100vh - 64px)",
                width="100%",
                justify="center",
                align="center",
            ),
            rx.center(
                rx.box(
                    *[portfolio_card(card, idx, len(cards))
                      for idx, card in enumerate(cards)],
                    width="100vw",
                    height="60vh",
                    min_height="40vh",
                    position="relative",
                    overflow="visible",
                    padding_x="7vw",
                ),
                width="100%",
                height="50vh",
            ),
            spacing="0",
            align="center",
            width="100%",
        ),
    )
