import reflex as rx

from ..components.navbar import navbar
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


def dot_grid_background():
    """Creates an interactive animated dot grid background with mouse interaction"""
    return rx.fragment(
        # Container for the canvas
        rx.el.div(
            rx.el.canvas(id="dotCanvas"),
            id="dot-grid-container",
            position="fixed",
            top="0",
            left="0",
            width="100vw",
            height="100vh",
            z_index="-1",
            background="#000000",
            overflow="hidden",
        ),
        # Script for dot grid animation
        rx.script(src="/dot-grid.js"),
    )


def dot_grid_overlay():
    """Creates a radial gradient overlay for fade effect"""
    return rx.box(
        position="fixed",
        top="0",
        left="0",
        width="100vw",
        height="100vh",
        z_index="-1",
        background="radial-gradient(circle at 50% 50%, transparent 0%, rgba(0, 0, 0, 0.7) 100%)",
        pointer_events="none",
    )


@rx.page(route="/", on_load=State.initiate)
def index() -> rx.Component:
    return rx.fragment(
        # Add the interactive dot grid background
        dot_grid_background(),
        dot_grid_overlay(),
        loading_screen(),
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
                        font_size="5rem",
                        weight="medium",
                        background="linear-gradient(to right, #ffffff, #888888)",
                        background_clip="text",
                        webkit_background_clip="text",
                        color="transparent",
                    ),
                    rx.text(
                        "Build your portfolios. We'll build ours",
                        size="4",
                        color="rgba(255, 255, 255, 0.7)",
                    ),
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
                    *[
                        portfolio_card(card, idx, len(cards))
                        for idx, card in enumerate(cards)
                    ],
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
