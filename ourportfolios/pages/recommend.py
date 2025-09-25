import reflex as rx

from ..components.navbar import navbar
from ..components.page_roller import card_roller, card_link
from ..components.cards import portfolio_card
from ..components.graph import mini_price_graph
from ..components.loading import loading_screen
from ..utils.load_data import fetch_data_for_symbols

cards = [
    {"title": "Recommend", "details": "Card 1 details", "link": "/recommend"},
    {"title": "Select", "details": "Card 2 details", "link": "/select"},
    {"title": "Analyze", "details": "Card 3 details", "link": "/analyze"},
    {"title": "Simulate", "details": "Card 4 details", "link": "/simulate"},
]


class State(rx.State):
    show_cards: bool = False
    data: list[dict] = []

    @rx.event
    def initiate(self):
        self.data = fetch_data_for_symbols(["VNINDEX"])


class Framework(rx.State):
    framework: str = ""


def page_selection():
    return rx.box(
        card_roller(
            card_link(
                rx.hstack(
                    rx.icon("chevron_left", size=32),
                    rx.vstack(
                        rx.heading("Ourportfolios", weight="regular", size="5"),
                        align="center",
                        justify="center",
                        height="100%",
                        spacing="1",
                    ),
                    align="center",
                    justify="center",
                ),
                href="/",
            ),
            card_link(
                rx.vstack(
                    rx.heading("Recommend", weight="regular", size="7"),
                    rx.text("caijdo", size="3"),
                    align="center",
                    justify="center",
                    height="100%",
                    spacing="1",
                ),
                href="/recommend",
            ),
            card_link(
                rx.hstack(
                    rx.vstack(
                        rx.heading("Select", weight="regular", size="5"),
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
                href="/select",
            ),
        ),
        width="100%",
        display="flex",
        justify_content="center",
        align_items="center",
        margin="0",
        padding="0",
    )

@rx.page(route="/recommend")
def index() -> rx.Component:
    return rx.fragment(
        loading_screen(),
        navbar(),
        page_selection(),
        rx.center(
            rx.box(
                rx.hstack(
                    rx.card(
                        "test1",
                        flex=1,
                        min_width=0,
                        max_width="100%",
                        style={"padding": "1em", "minWidth": 0, "overflow": "hidden"},
                    ),
                    rx.card(
                        "test2",
                        flex=4,
                        min_width=0,
                        max_width="100%",
                        style={"padding": "1em", "minWidth": 0, "overflow": "hidden"},
                    ),
                    spacing="4",
                    width="100%",
                    align="stretch",
                    justify="between",
                ),
                width="86vw",
            ),
            width="100%",
            padding="2em",
            padding_top="5em",
            position="relative",
        ),
    )
