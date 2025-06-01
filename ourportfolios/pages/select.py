from turtle import width
import reflex as rx
from ..components.navbar import navbar
from ..components.drawer import drawer_button
from ..components.page_roller import card_roller, card_link
from ..components.graph import mini_price_graph  # <-- import mini_price_graph


class SegmentedState(rx.State):
    control: str = "home"

    # Use a list of dicts with a label and a data field (list of dicts)
    graph_data: list[dict] = [
        {"label": "VNINDEX", "data": [
            {"name": "VNINDEX", "value": v} for v in [10, 12, 14, 13, 15, 18, 17]]},
        {"label": "HSX", "data": [{"name": "HSX", "value": v}
                                  for v in [20, 19, 21, 23, 22, 24, 26]]},
        {"label": "HNX", "data": [{"name": "HNX", "value": v}
                                  for v in [5, 7, 6, 8, 9, 11, 10]]},
        {"label": "UPCOM", "data": [{"name": "UPCOM", "value": v}
                                    for v in [30, 28, 29, 31, 33, 32, 34]]},
        {"label": "VNMID", "data": [{"name": "VNMID", "value": v}
                                    for v in [15, 16, 18, 17, 19, 20, 21]]},
        {"label": "VN30", "data": [{"name": "VN30", "value": v}
                                   for v in [8, 9, 10, 12, 11, 13, 14]]},
        {"label": "VN100", "data": [{"name": "VN100", "value": v}
                                    for v in [25, 27, 26, 28, 29, 30, 32]]},
        {"label": "VNALL", "data": [{"name": "VNALL", "value": v}
                                    for v in [12, 13, 15, 14, 16, 18, 17]]},
        {"label": "VNFIN", "data": [{"name": "VNFIN", "value": v}
                                    for v in [18, 17, 19, 21, 20, 22, 23]]},
        {"label": "VNDIAMOND", "data": [
            {"name": "VNDIAMOND", "value": v} for v in [22, 21, 23, 25, 24, 26, 28]]},
    ]


@rx.page(route="/select")
def index():
    return rx.vstack(
        navbar(),
        page_selection(),
        three_part_layout(),
        drawer_button(),
    )


def page_selection():
    return rx.center(
        card_roller(
            card_link(
                rx.hstack(
                    rx.icon("chevron_left", size=32),
                    rx.vstack(
                        rx.heading("Recommend", weight="bold", size="6"),
                        rx.text("caijdo", size="1"),
                        align="center",
                        justify="center",
                        height="100%",
                    ),
                    align="center",
                    justify="center",
                ),
                href="/recommend",
            ),
            card_link(
                rx.vstack(
                    rx.heading("Select", weight="bold", size="8"),
                    rx.text("caijdo", size="3"),
                    align="center",
                    justify="center",
                    height="100%",
                ),
                href="/select",
            ),
            card_link(
                rx.hstack(
                    rx.vstack(
                        rx.heading("Simulate", weight="bold", size="6"),
                        rx.text("caijdo", size="1"),
                        align="center",
                        justify="center",
                        height="100%",
                    ),
                    rx.icon("chevron_right", size=32),
                    align="center",
                    justify="center",
                ),
                href="/simulate",
            ),
        ),
        min_height="0vh",
        width="100%",
        align_items="center",
    )


def card_with_scrollable_area():
    return rx.card(
        rx.segmented_control.root(
            rx.segmented_control.item("Markets", value="markets"),
            rx.segmented_control.item("Coin", value="coin"),
            rx.segmented_control.item("Test", value="test"),
            on_change=SegmentedState.setvar("control"),
            value=SegmentedState.control,
            size="1",
            style={"height": "2em"}
        ),
        rx.scroll_area(
            rx.vstack(
                rx.foreach(
                    SegmentedState.graph_data,
                    lambda item: mini_price_graph(
                        item["data"],
                        label=item["label"],
                        size=(120, 100)
                    )
                ),
                spacing="2",
                height="100%",
                width="100%",
                align_items="flex-start",
            ),
            style={"height": 400, "width": 250, "display": "flex"},
            scrollbars="vertical",
            type="auto",
        ),
        style={
            "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            "justifyContent": "center",
        },
    )


def three_part_layout():
    return rx.box(
        rx.hstack(
            rx.spacer(),
            rx.spacer(),
            card_with_scrollable_area(),
            width="100%",
        ),
        width="100%",
        padding="2em",
        padding_top="5em"
    )
