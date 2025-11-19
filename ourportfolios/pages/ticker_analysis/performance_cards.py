"""Performance and metrics cards for the ticker landing page."""

import reflex as rx

from ...state.framework_state import GlobalFrameworkState
from .state import State


def create_dynamic_chart(category: str):
    """Create a dynamic chart for a specific category"""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading(category, size="4", weight="medium"),
                rx.spacer(),
                rx.cond(
                    State.available_metrics_by_category.contains(category),
                    rx.select(
                        State.available_metrics_by_category[category],
                        value=State.selected_metrics.get(category, ""),
                        on_change=lambda value: State.set_metric_for_category(
                            category, value
                        ),
                        size="1",
                    ),
                    rx.text("No metrics", size="1", color="gray"),
                ),
                align="center",
                justify="between",
                width="100%",
            ),
            rx.box(
                rx.cond(
                    (State.get_chart_data_for_category[category].length() > 0),
                    rx.recharts.line_chart(
                        rx.recharts.line(
                            data_key="value",
                            stroke=rx.color("accent", 9),
                            stroke_width=3,
                            type_="monotone",
                            dot=False,
                        ),
                        rx.recharts.x_axis(
                            data_key="year",
                            angle=-45,
                            text_anchor="end",
                            height=60,
                            tick={"fontSize": 14},
                        ),
                        rx.recharts.y_axis(
                            tick={"fontSize": 14},
                        ),
                        rx.recharts.tooltip(),
                        data=State.get_chart_data_for_category[category],
                        width="100%",
                        height=250,
                        margin={"top": 15, "right": 30, "left": 10, "bottom": 5},
                    ),
                    rx.center(
                        rx.text("No data available", color="gray", size="2"),
                        height="250px",
                    ),
                ),
                width="100%",
                height="250px",
                style={"overflow": "hidden"},
            ),
            spacing="2",
            align="stretch",
            height="100%",
        ),
        width="100%",
        height="100%",
        style={"padding": "0.75em"},
    )


def framework_indicator():
    """Show which framework is currently selected."""
    return rx.cond(
        GlobalFrameworkState.has_selected_framework,
        rx.link(
            rx.hstack(
                rx.icon("target", size=16),
                rx.text(
                    f"Framework: {GlobalFrameworkState.framework_display_name}",
                    size="2",
                    weight="medium",
                ),
                rx.icon("external-link", size=14),
                spacing="2",
                align="center",
                padding="0.5em",
                style={
                    "backgroundColor": rx.color("violet", 2),
                    "border": f"1px solid {rx.color('violet', 4)}",
                    "borderRadius": "6px",
                    "transition": "all 0.2s ease",
                    "_hover": {
                        "backgroundColor": rx.color("violet", 3),
                        "borderColor": rx.color("violet", 5),
                        "transform": "translateY(-1px)",
                    },
                },
            ),
            href="/recommend",
            underline="none",
        ),
        None,
    )


def performance_cards():
    """Create performance cards with dynamic charts that adapt to any number of categories"""
    categories = State.get_categories_list

    return rx.cond(
        categories.length() > 0,
        rx.vstack(
            # Show framework selection prompt if no framework is selected
            rx.cond(
                ~GlobalFrameworkState.has_selected_framework,
                rx.callout.root(
                    rx.callout.icon(
                        rx.icon("target", size=20),
                    ),
                    rx.callout.text(
                        rx.hstack(
                            rx.text(
                                "No investment framework selected. ",
                                size="2",
                                weight="medium",
                            ),
                            rx.link(
                                rx.button(
                                    rx.icon("arrow-right", size=16),
                                    "Select a Framework",
                                    size="2",
                                    variant="soft",
                                    color_scheme="violet",
                                ),
                                href="/recommend",
                                underline="none",
                            ),
                            spacing="3",
                            align="center",
                        )
                    ),
                    color_scheme="violet",
                    variant="surface",
                    size="1",
                    style={"marginBottom": "1em"},
                ),
                None,
            ),
            # Dynamic 3-column grid that adapts to number of categories (3 per row)
            rx.box(
                rx.foreach(
                    categories,
                    lambda category: create_dynamic_chart(category),
                ),
                display="grid",
                grid_template_columns="repeat(3, 1fr)",
                gap="1rem",
                width="100%",
                max_height="70vh",
                overflow="visible",
            ),
            spacing="3",
            width="100%",
        ),
        rx.center(
            rx.spinner(size="3"),
        ),
    )
