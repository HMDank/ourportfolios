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
                rx.vstack(
                    rx.heading("Recommend", weight="bold", size="7"),
                    rx.text("caijdo", size="2"),
                    align="center",
                    justify="center",
                    height="100%",
                ),
                rx.vstack(
                    rx.heading("Select", weight="bold", size="8"),
                    rx.text("caijdo", size="3"),
                    align="center",
                    justify="center",
                    height="100%",
                ),
                rx.vstack(
                    rx.heading("Simulate", weight="bold", size="7"),
                    rx.text("caijdo", size="2"),
                    align="center",
                    justify="center",
                    height="100%",
                ),
            ),
            min_height="0vh",
            width="100%",
            align_items="center",
        ),
        drawer_button(),
    )
