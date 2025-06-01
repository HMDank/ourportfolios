import reflex as rx
import pandas as pd
from .graph import mini_price_graph
from .search_bar import search_bar
from ..utils.load_data import load_historical_data


class VniState(rx.State):
    def scale_close(data):
        df = pd.DataFrame(data)
        min_val = df['close'].min()
        max_val = df['close'].max()
        range_val = max_val - min_val if max_val != min_val else 1  # avoid division by zero

        df = df.copy()
        df['scaled_close'] = (df['close'] - min_val) / range_val
        return df

    vnindex_data = load_historical_data("VNINDEX").tail(5).to_dict("records")
    scaled_vnindex_data = scale_close(vnindex_data).to_dict(orient="records")


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
                    mini_price_graph(VniState.scaled_vnindex_data),
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
