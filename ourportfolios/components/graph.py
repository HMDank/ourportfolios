import reflex as rx


class VniState(rx.State):
    users_for_graph = [
        {"name": "A", "value": 10},
        {"name": "B", "value": 25},
        {"name": "C", "value": 15},
        {"name": "D", "value": 30},
    ]


def VniGraph():
    return rx.hstack(
        rx.vstack(
            rx.recharts.area_chart(
                rx.recharts.area(
                    data_key="value",
                    stroke=rx.color("accent", 9),
                    fill=rx.color("accent", 8),
                ),
                rx.recharts.x_axis(data_key="name", hide=True),
                rx.recharts.y_axis(hide=True),
                data=VniState.users_for_graph,
                width=80,
                height=40,
            ),
            rx.hstack(
                rx.text("VNINDEX", size="1", font_size="0.75rem"),
                rx.badge(
                    rx.flex(
                        rx.icon(tag="arrow_up", size=10),
                        rx.text("8.8%", font_size="0.6rem"),
                        spacing="1",
                    ),
                    color_scheme="grass",
                    size="1",
                    style={
                        "padding": "0.1em 0.3em"
                    },
                )
            ),
            spacing="1",
            align_items="center",
            width="100%",
        ),
        width="100%",
    )
