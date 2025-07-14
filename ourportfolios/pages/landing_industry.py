import reflex as rx
from ..components.navbar import navbar
from ..components.drawer import drawer_button
from ..components.loading import loading_screen


@rx.page(route="/select/[industry]")
def landing_industry():
    return rx.fragment(
        loading_screen(),
        navbar(),
        rx.box(
            rx.link(
                rx.hstack(
                    rx.icon("chevron_left", size=22),
                    rx.text("select", margin_top="-2px"),
                    spacing="0",
                ),
                href="/select",
                underline="none",
            ),
            position="fixed",
            justify="center",
            style={"paddingTop": "1em", "paddingLeft": "0.5em"},
            z_index="1",
        ),
        rx.center(
            rx.box(
                rx.text("Industry landing page content goes here."),
                width="100%",
                style={"maxWidth": "90vw", "margin": "0 auto"},
            ),
            width="100%",
            padding="2em",
            padding_top="5em",
            style={"maxWidth": "90vw", "margin": "0 auto"},
            position="relative",
        ),
        drawer_button(),
    )
