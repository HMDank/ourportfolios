import reflex as rx


def side_card(content, style):
    return rx.card(
        rx.center(
            content,
            width="100%",
            height="100%",
        ),
        padding="1.2em 1.5em",
        width="16em",
        background_color="transparent",
        style=style,
        align_items="center",
    )


def main_card(content, style):
    return rx.card(
        rx.center(
            content,
            width="100%",
            height="100%",
        ),
        padding="2em 2.5em",
        width="22em",
        border="none",
        background_color="transparent",
        style=style,
        spacing="4",
        align_items="center",
    )


def card_roller(left_content, center_content, right_content):
    side_card_style = {
        "backdropFilter": "blur(14px)",
        "background": "rgba(30, 27, 46, 0.5)",
        "zIndex": 1,
        "border": "none",
        "boxShadow": "0 4px 24px rgba(0,0,0,0.10)",
        "position": "absolute",
        "top": "50%",
        "transform": "translateY(-50%)",
    }
    main_card_style = {
        "backdropFilter": "blur(14px)",
        "zIndex": 2,
        "position": "relative",
    }
    left = side_card(left_content, {**side_card_style, "left": "-2em"})
    right = side_card(right_content, {**side_card_style, "right": "-2em"})
    center = main_card(center_content, main_card_style)
    return rx.box(
        left,
        right,
        center,
        position="relative",
        width="38em",
        height="15em",
        display="flex",
        align_items="center",
        justify_content="center",
    )
