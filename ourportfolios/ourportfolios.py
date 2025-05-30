import reflex as rx
from .components.navbar import navbar
from .components.page_selection import page_selection


class State(rx.State):
    show_cards: bool = False

    @rx.event
    def on_scroll(self, event=None):
        # You may need to extract scrollTop from the event if available.
        # For the sake of this example, we'll just toggle show_cards.
        self.show_cards = True


def index() -> rx.Component:
    return rx.fragment(
        navbar(),
        rx.color_mode.button(position="bottom-right"),
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
                page_selection(),
                width="100vw",
                height="50vh",
            ),
            spacing="0",
            align="center",
            width="100%",
        ),
    )


app = rx.App(
    theme=rx.theme(
        accent_color="violet"
    )
)
app.add_page(index)
