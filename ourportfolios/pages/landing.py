import reflex as rx
from ..components.navbar import navbar
from ..components.page_selection import page_selection


class State(rx.State):
    show_cards: bool = False


@rx.page(route="/")
def landing() -> rx.Component:
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
                width="100%",
                height="50vh",
            ),
            spacing="0",
            align="center",
            width="100%",
        ),
    )
