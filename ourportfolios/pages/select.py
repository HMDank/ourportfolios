import reflex as rx
from ..components.navbar import navbar
from ..components.drawer import drawer_button
from ..components.page_roller import card_roller


@rx.page(route="/select")
def index():
    return rx.vstack(
        navbar(),
        rx.center(
            card_roller(
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
                rx.vstack(
                    rx.heading("Select", weight="bold", size="8"),
                    rx.text("caijdo", size="3"),
                    align="center",
                    justify="center",
                    height="100%",
                ),
                rx.hstack(
                    rx.vstack(
                        rx.heading("Simulate", weight="bold", size="6"),
                        rx.text("caijdo", size="1"),
                        align="center",
                        justify="center",
                        height="100%",
                    ),
                    rx.icon("chevron_right", size=32),
                    align="center",
                    justify="center",
                ),
            ),
            min_height="0vh",
            width="100%",
            align_items="center",
        ),
        drawer_button(),
    )
