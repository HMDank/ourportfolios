import reflex as rx


class CartState(rx.State):
    cart_items: list[dict] = [
        {"name": "Apple"},
        {"name": "Banana"},
    ]
    is_open: bool = False

    @rx.event
    def toggle_cart(self):
        self.is_open = not self.is_open

    @rx.event
    def remove_item(self, index: int):
        self.cart_items.pop(index)


def cart_drawer_content():
    return rx.drawer.content(
        rx.box(
            rx.vstack(
                rx.box(
                    rx.drawer.close(
                        rx.text(
                            rx.icon("x", size=20),
                            on_click=CartState.toggle_cart,
                            style={
                                "marginLeft": "auto",
                                "cursor": "pointer",
                                "userSelect": "none",
                                "color": rx.color("accent", 10),
                                "_hover": {
                                    "color": rx.color("accent", 7),
                                },
                            },
                        )
                    ),
                    width="100%",
                    display="flex",
                    justify_content="flex-end",
                    margin_bottom="1em",
                ),
                rx.heading(
                    "Tickers Cart",
                    size="6",
                    weight="bold",
                ),
                rx.cond(
                    CartState.cart_items,
                    rx.vstack(
                        rx.foreach(
                            CartState.cart_items,
                            lambda item, i: rx.card(
                                rx.hstack(
                                    rx.text(
                                        item["name"],
                                        size="3",
                                        weight="medium"
                                    ),
                                    rx.button(
                                        rx.icon("list-minus", size=16),
                                        color_scheme="ruby",
                                        size="1",
                                        variant="soft",
                                        style={
                                            "fontWeight": "bold",
                                            "padding": "0.3em 0.7em",
                                            "fontSize": "0.9em"
                                        },
                                        on_click=lambda: CartState.remove_item(
                                            i
                                        ),
                                    ),
                                    justify="between",
                                    align_items="center",
                                    width="100%"
                                ),
                                background_color=rx.color("accent", 2),
                                padding="0.8em 1em",
                                margin_bottom="0.7em",
                                width="60%"
                            ),
                        ),
                        width="100%",
                        spacing="1"
                    ),
                    rx.text(
                        "Your cart is empty.",
                        size="5",
                        weight="medium",
                        margin_top="2em"
                    )
                ),
                spacing="5",
                align_items="start",
            ),
            width="100%",
            padding="2em",
            border_radius="1.2em",
            style={
                "backdropFilter": "blur(14px)",
                "background": "rgba(30, 27, 46, 0.7)",
                "borderRadius": "1.2em",
                "border": f"1px solid {rx.color('accent', 3)}"
            },
        ),
        width="28em",
        padding="2.5em 2em 2em 2em",
        background_color="transparent",
    )


def drawer_button():
    return rx.drawer.root(
        rx.drawer.trigger(
            rx.button(
                rx.icon("shopping-cart", size=16),
                on_click=CartState.toggle_cart,
                style={
                    "position": "fixed",
                    "bottom": "2em",
                    "left": "2em",
                    "z_index": 1000,
                },
            )
        ),
        rx.drawer.overlay(
            on_click=CartState.toggle_cart
        ),
        rx.drawer.portal(cart_drawer_content()),
        open=CartState.is_open,
        direction="left",
        handle_only=True,
    )
