import reflex as rx


def mini_price_graph(data, label="VNINDEX", size=(80, 40)):
    width, height = size
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
                data=data,
                width=width,
                height=height,
            ),
            rx.hstack(
                rx.text(label, size="1", font_size="0.75rem"),
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
            align_items="flex-start",
        ),
    )
