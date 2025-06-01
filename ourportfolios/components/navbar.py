import reflex as rx
from .graph import mini_price_graph
from .search_bar import search_bar


class VniState(rx.State):
    users_for_graph = [
        {"name": "A", "value": 10},
        {"name": "B", "value": 25},
        {"name": "C", "value": 15},
        {"name": "D", "value": 30},
    ]


def navbar_link(text: str, url: str) -> rx.Component:
    return rx.link(
        rx.text(text, size="4", weight="medium"), href=url
    )


def navbar() -> rx.Component:
    return rx.box(
        rx.desktop_only(
            rx.hstack(
                rx.hstack(
                    rx.box(
                        rx.heading("OurPortfolios", size="5", weight="bold"),
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
                    mini_price_graph(VniState.users_for_graph),
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
                    align_items="center"
                ),

                justify="between",
                align_items="center",
            ),
        ),
        rx.mobile_and_tablet(
            rx.hstack(
                rx.hstack(
                    rx.link(
                        rx.heading(
                            "OurPortfolios", size="6", weight="bold"
                        ),
                        href="/",
                        style={
                            "pointerEvents": "none",
                            "textDecoration": "none"
                        },
                        _hover={"background": "none"},
                    ),
                    align_items="center",
                ),
                rx.menu.root(
                    rx.menu.trigger(
                        rx.icon("menu", size=30)
                    ),
                    rx.menu.content(
                        rx.menu.item("Home"),
                        rx.menu.item("About"),
                        rx.menu.item("Pricing"),
                        rx.menu.item("Contact"),
                        rx.menu.separator(),
                        rx.menu.item("Log in"),
                        rx.menu.item("Sign up"),
                    ),
                    justify="end",
                ),
                justify="between",
                align_items="center",
            ),
        ),
        bg=rx.color("accent", 3),
        padding="0.4em 1em",
        # position="fixed",
        # top="0px",
        # z_index="5",
        width="100%",
    )
