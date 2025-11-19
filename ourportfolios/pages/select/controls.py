"""Sort and search components for the select page."""

import reflex as rx

from .state import State
from .filters import display_selected_filter, filter_button


def display_sort_options() -> rx.Component:
    asc_icon: rx.Component = rx.icon("arrow-down-a-z", size=13)
    desc_icon: rx.Component = rx.icon("arrow-down-z-a", size=13)

    return rx.fragment(
        rx.menu.root(
            rx.menu.trigger(
                rx.button(
                    rx.hstack(
                        rx.cond(
                            State.selected_sort_order == "ASC", asc_icon, desc_icon
                        ),
                        rx.text("Sort"),
                        align="center",
                    ),
                    variant="outline",
                ),
            ),
            rx.menu.content(
                rx.foreach(
                    State.sort_options.keys(),
                    lambda option: rx.menu.sub(
                        rx.menu.sub_trigger(option),
                        rx.menu.sub_content(
                            rx.foreach(
                                State.sort_orders,
                                lambda order: rx.menu.item(
                                    rx.hstack(
                                        rx.cond(
                                            order == "ASC",
                                            asc_icon,
                                            desc_icon,
                                        ),
                                        rx.text(order),
                                        align="center",
                                        justify="between",
                                    ),
                                    on_click=[
                                        State.set_sort_option(option),
                                        State.set_sort_order(order),
                                    ],
                                ),
                            )
                        ),
                    ),
                )
            ),
        )
    )


def ticker_filter():
    return rx.flex(
        # Search box
        rx.box(
            rx.input(
                rx.input.slot(rx.icon(tag="search", size=16)),
                placeholder="Search for a ticker",
                type="search",
                size="2",
                width="100%",
                color_scheme="violet",
                radius="large",
                value=State.search_query,
                on_change=State.set_search_query,
            ),
            width="30%",
            height="100%",
            align="center",
            marginRight="0.5em",
        ),
        # Selected filter option
        rx.scroll_area(
            display_selected_filter(),
            scrollbars="horizontal",
            paddingTop="0.1em",
            type="hover",
            width="48em",
            height="2.6em",
        ),
        rx.spacer(),
        # Sort
        display_sort_options(),
        # Filter
        filter_button(),
        paddingTop="0.75em",
        paddingBottom="0.5em",
        width="100%",
        direction="row",
        spacing="2",
        height="3em",
    )
