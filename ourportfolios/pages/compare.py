"""Stock comparison page - compare multiple stocks side by side."""

import reflex as rx
from typing import List, Dict, Any

from ..components.navbar import navbar
from ..components.drawer import drawer_button
from ..components.loading import loading_screen
from ..state import StockComparisonState


def metric_selector_popover() -> rx.Component:
    """Popover component for selecting metrics to compare"""
    return rx.popover.root(
        rx.popover.trigger(
            rx.button(
                rx.hstack(rx.icon("settings", size=16), spacing="2"),
                variant="outline",
                size="2",
            )
        ),
        rx.popover.content(
            rx.vstack(
                rx.hstack(
                    rx.heading("Select metrics"),
                    rx.spacer(),
                    rx.popover.close(
                        rx.button(rx.icon("x", size=16), variant="ghost", size="1")
                    ),
                    width="100%",
                    align="center",
                ),
                rx.scroll_area(
                    rx.vstack(
                        rx.foreach(
                            StockComparisonState.available_metrics,
                            lambda metric: rx.hstack(
                                rx.checkbox(
                                    checked=StockComparisonState.selected_metrics.contains(
                                        metric
                                    ),
                                    on_change=lambda: StockComparisonState.toggle_metric(
                                        metric
                                    ),
                                    size="2",
                                ),
                                rx.text(
                                    StockComparisonState.metric_labels[metric], size="2"
                                ),
                                spacing="2",
                                align="center",
                                width="100%",
                            ),
                        ),
                        spacing="2",
                        align="start",
                        width="100%",
                    ),
                    height="300px",
                    width="100%",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.spacer(),
                    rx.button(
                        "Select All",
                        on_click=StockComparisonState.select_all_metrics,
                        size="1",
                        variant="soft",
                    ),
                    rx.button(
                        "Clear All",
                        on_click=StockComparisonState.clear_all_metrics,
                        size="1",
                        variant="soft",
                    ),
                    spacing="2",
                    width="100%",
                ),
                spacing="3",
                width="300px",
                padding="0.7em",
            ),
            side="bottom",
            align="start",
        ),
    )


def stock_column_card(stock: Dict[str, Any], industry: str) -> rx.Component:
    """Create a column with separate header card and metrics card for each stock"""
    market_cap = stock.get("market_cap", "")
    ticker = stock.get("symbol", "")

    return rx.vstack(
        # Header card - separate from metrics
        rx.card(
            rx.box(
                rx.button(
                    rx.icon("x", size=12),
                    on_click=lambda: StockComparisonState.remove_stock_from_compare(
                        ticker
                    ),
                    variant="ghost",
                    size="2",
                    style={
                        "position": "absolute",
                        "top": "0.5em",
                        "right": "0.5em",
                        "min_width": "auto",
                        "height": "auto",
                        "opacity": "0.7",
                    },
                ),
                rx.link(
                    rx.vstack(
                        rx.text(
                            ticker,
                            weight="medium",
                            size="8",
                            color=rx.color("gray", 12),
                            letter_spacing="0.05em",
                        ),
                        rx.badge(
                            stock.get("industry", ""),
                            size="1",
                            variant="soft",
                            style={"font_size": "0.7em"},
                        ),
                        rx.text(
                            f"{market_cap} B. VND",
                            size="1",
                            color=rx.color("gray", 10),
                            weight="medium",
                        ),
                        spacing="2",
                        justify="center",
                        width="100%",
                        padding_bottom="0.2em",
                    ),
                    href=f"/analyze/{ticker}",
                    text_decoration="none",
                    _hover={
                        "text_decoration": "none",
                    },
                    width="100%",
                ),
                position="relative",
                width="100%",
            ),
            width="12em",
            style={
                "flex_shrink": "0",
                "transition": "transform 0.2s ease",
            },
            _hover={
                "transform": "translateY(-0.4em)",
            },
        ),
        # Metrics card
        rx.card(
            rx.vstack(
                rx.foreach(
                    StockComparisonState.selected_metrics,
                    lambda metric_key: rx.box(
                        rx.text(
                            stock[metric_key],
                            size="2",
                            weight=rx.cond(
                                StockComparisonState.industry_best_performers[industry][
                                    metric_key
                                ]
                                == ticker,
                                "medium",
                                "regular",
                            ),
                            color=rx.cond(
                                StockComparisonState.industry_best_performers[industry][
                                    metric_key
                                ]
                                == ticker,
                                rx.color("green", 11),
                                rx.color("gray", 11),
                            ),
                        ),
                        width="100%",
                        min_height="2.5em",
                        text_align="center",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        border_bottom=f"1px solid {rx.color('gray', 4)}",
                    ),
                ),
                spacing="0",
                width="100%",
            ),
            width="11.5em",
            style={"flex_shrink": "0"},
        ),
        spacing="5",
        align="center",
        width="12em",
        min_width="12em",
        style={"flex_shrink": "0"},
    )


def metric_labels_column() -> rx.Component:
    """Fixed column showing metric labels"""
    return rx.vstack(
        rx.card(
            rx.box(
                width="12em",
                min_width="12em",
                min_height="7.5em",
            ),
            width="12em",
            min_width="12em",
            style={
                "flex_shrink": "0",
                "visibility": "hidden",
            },
        ),
        # Metrics labels card
        rx.card(
            rx.vstack(
                rx.foreach(
                    StockComparisonState.selected_metrics,
                    lambda metric_key: rx.box(
                        rx.text(
                            StockComparisonState.metric_labels[metric_key],
                            size="2",
                            weight="medium",
                            color=rx.color("gray", 12),
                        ),
                        width="100%",
                        min_height="2.5em",
                        display="flex",
                        align_items="center",
                        justify_content="start",
                        border_bottom=f"1px solid {rx.color('gray', 4)}",
                    ),
                ),
                spacing="0",
                width="100%",
            ),
            width="12em",
            min_width="12em",
            style={"flex_shrink": "0"},
        ),
        spacing="2",
        align="start",
        style={"flex_shrink": "0"},
    )


def comparison_controls() -> rx.Component:
    """Controls section with metric selector and load button"""
    return rx.hstack(
        rx.spacer(),
        rx.hstack(
            rx.button(
                rx.hstack(rx.icon("import", size=16), spacing="2"),
                on_click=StockComparisonState.import_and_fetch_compare,
                size="2",
            ),
            metric_selector_popover(),
            spacing="3",
            align="center",
        ),
        spacing="0",
        align="center",
        width="100%",
        margin_bottom="2em",
    )


def industry_group_section(industry: str, stocks: List[Dict[str, Any]]) -> rx.Component:
    """Create a section for each industry group"""
    return rx.hstack(
        rx.foreach(
            stocks,
            lambda stock: stock_column_card(stock, industry),
        ),
        spacing="3",
        align="start",
        style={"flex_wrap": "nowrap"},
    )


def comparison_section() -> rx.Component:
    """Main comparison section with industry-grouped layout"""
    return rx.cond(
        StockComparisonState.compare_list,
        rx.box(
            rx.vstack(
                comparison_controls(),
                # Main comparison table
                rx.hstack(
                    # Fixed metric labels column
                    metric_labels_column(),
                    # Scrollable grouped stock columns area
                    rx.box(
                        rx.scroll_area(
                            rx.box(
                                rx.hstack(
                                    # Industry groups
                                    rx.foreach(
                                        StockComparisonState.grouped_stocks.items(),
                                        lambda item: industry_group_section(
                                            item[0],
                                            item[1],
                                        ),
                                    ),
                                    spacing="7",  # Space between industry groups
                                    align="start",
                                    style={"flex_wrap": "nowrap"},
                                ),
                                padding_top="0.5em",
                                padding_bottom="0.5em",
                            ),
                            direction="horizontal",
                            scrollbars="horizontal",
                            style={
                                "width": "100%",
                                "maxWidth": "90vw",
                                "overflowX": "auto",
                                "overflowY": "hidden",
                            },
                        ),
                        width="100%",
                        margin_left="1.8em",
                        style={
                            "maxWidth": "90vw",
                            "overflowX": "auto",
                            "overflowY": "hidden",
                            "position": "relative",
                        },
                    ),
                    spacing="0",
                    align="start",
                    width="100%",
                    style={"flex_wrap": "nowrap"},
                ),
                spacing="0",
                width="100%",
            ),
            width="100%",
            style={
                "max_width": "100vw",
                "margin": "0 auto",
                "padding": "1.5em",
                "overflowX": "hidden",
            },
        ),
        rx.center(
            rx.vstack(
                rx.text(
                    "Your compare list is empty. ",
                    size="3",
                    weight="medium",
                    align="center",
                ),
                rx.button(
                    rx.hstack(
                        rx.icon("shopping_cart", size=16),
                        rx.text("Import from Cart"),
                        spacing="2",
                    ),
                    on_click=StockComparisonState.import_and_fetch_compare,
                    size="3",
                ),
                spacing="3",
                align="center",
            ),
            min_height="40vh",
            width="100%",
        ),
    )


@rx.page(route="/analyze/compare")
def index() -> rx.Component:
    """Main page component"""
    return rx.fragment(
        loading_screen(),
        navbar(),
        rx.box(
            rx.link(
                rx.hstack(
                    rx.icon("chevron_left", size=22),
                    rx.text("analyze", margin_top="-2px"),
                    spacing="0",
                ),
                href="/analyze",
                underline="none",
            ),
            position="fixed",
            justify="center",
            style={"paddingTop": "1em", "paddingLeft": "0.5em"},
            z_index="1",
        ),
        rx.box(
            comparison_section(),
            width="100%",
            style={
                "max_width": "90vw",
                "margin": "0 auto",
            },
        ),
        drawer_button(),
        spacing="0",
    )
