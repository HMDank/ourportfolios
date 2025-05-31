import reflex as rx
from ..components.navbar import navbar
from ..components.drawer import drawer_button


@rx.page(route="/select")
def index():
    return rx.vstack(
        navbar(),
        rx.center(
            rx.card(
                rx.heading(
                    "Select",
                    size="7",
                    weight="bold",
                ),
                rx.text(
                    "Manually select your tickers here!",
                    size="3",
                    margin_bottom="0.2em"
                ),
                padding="2em 2.5em",
                width="28em",
                min_width="18em",
                border="none",
                background_color="transparent",
                style={
                    "backdropFilter": "blur(14px)",
                },
                spacing="4",
            ),
            min_height="60vh"
        ),
        drawer_button(),
    )
