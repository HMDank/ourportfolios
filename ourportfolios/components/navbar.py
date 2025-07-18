import reflex as rx
from .search_bar import search_bar


def navbar(*children) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.hstack(
                rx.box(
                    rx.heading("OurPortfolios", size="5", weight="medium"),
                    rx.link(
                        "",
                        href="/",
                        style={
                            "position": "absolute",
                            "top": 0,
                            "left": 0,
                            "right": 0,
                            "bottom": 0,
                            "width": "100%",
                            "height": "100%",
                            "zIndex": 1,
                            "textDecoration": "none",
                            "color": "inherit",
                            "background": "transparent",
                            "pointerEvents": "auto",
                            "_hover": {
                                "textDecoration": "none",
                                "color": "inherit",
                                "background": "transparent",
                            },
                        },
                    ),
                    position="relative",
                ),
                *children,
                align_items="center",
                spacing="7",
            ),
            rx.hstack(
                rx.color_mode.button(),
                search_bar(),
                rx.button(
                    "Sign Up",
                    size="2",
                    variant="outline",
                ),
                rx.button("Log In", size="2"),
                spacing="4",
                justify="end",
                align_items="center",
            ),
            justify="between",
            align_items="center",
            height="4.1em",
        ),
        bg=rx.color("accent", 3),
        padding="0.4em 1em",
        width="100%",
    )
