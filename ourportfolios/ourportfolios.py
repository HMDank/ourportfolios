import reflex as rx

from .components.navbar import navbar
from .components.news_card import news_card


class State(rx.State):
    cards: list[str] = ["News 1", "News 2", "News 3"]
    show_cards: bool = False

    def load_more(self):
        next_num = len(self.cards) + 1
        self.cards += [f"News {next_num}",
                       f"News {next_num+1}", f"News {next_num+2}"]

    def on_scroll(self, event=None):
        self.show_cards = True


def index() -> rx.Component:
    return rx.fragment(
        navbar(),
        rx.color_mode.button(position="bottom-left"),
        rx.vstack(
            # Header and search bar centered
            rx.vstack(
                rx.heading("OurPortfolios", size="9"),
                rx.text("Build your portfolios. We'll build ours"),
                rx.input(
                    rx.input.slot(rx.icon(tag="search")),
                    placeholder="Try searching for a ticker here!",
                ),
                spacing="5",
                justify="center",
                align="center",
                min_height="85vh",
            ),
            rx.cond(
                State.show_cards,
                rx.hstack(
                    # Changed from vstack to hstack for horizontal layout
                    rx.foreach(State.cards, news_card),
                    spacing="5",
                    align="center",
                ),
            ),
            spacing="0",
            on_scroll=State.on_scroll,
            align="center",
            height="200vh",
            overflow_y="auto",
        ),
    )


app = rx.App(
    theme=rx.theme(
        accent_color="violet"
    )
)
app.add_page(index)
