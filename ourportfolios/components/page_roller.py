import reflex as rx


def side_card(content, style):
    return rx.card(
        content,
        width="16em",
        height="6.5em",
        background_color="transparent",
        style=style,
        align_items="center",
        display="flex",
        justify_content="center",
    )


def main_card(content, style):
    return rx.card(
        content,
        padding="2em 2.5em",
        width="22em",
        border="none",
        background_color="transparent",
        style=style,
        spacing="4",
        align_items="center",
        _hover={
            "transform": "scale(1.05)",
        },
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
        "transition": "transform 0.2s, box-shadow 0.2s, z-index 0.2s",
    }
    main_card_style = {
        "backdropFilter": "blur(14px)",
        "zIndex": 2,
        "position": "relative",
        "transition": "transform 0.2s, box-shadow 0.2s, z-index 0.2s",
    }
    # Wrap side cards in boxes for horizontal slide on hover only
    left = rx.box(
        side_card(left_content, {**side_card_style, "left": "-4em"}),
        _hover={
            "transform": "translateX(-1em) scale(1.05)",
        },
        transition="transform 0.2s, z-index 0.2s",
        position="absolute",
        left="-2em",
        top="0",
        height="100%",
        width="16em",
        style={"pointerEvents": "auto"},
    )
    right = rx.box(
        side_card(right_content, {**side_card_style, "right": "-4em"}),
        _hover={
            "transform": "translateX(1em) scale(1.05)",
        },
        transition="transform 0.2s, z-index 0.2s",
        position="absolute",
        right="-2em",
        top="0",
        height="100%",
        width="16em",
        style={"pointerEvents": "auto"},
    )
    center = main_card(center_content, main_card_style, )
    return rx.box(
        left,
        right,
        center,
        position="relative",
        width="38em",
        height="10em",
        display="flex",
        align_items="center",
        justify_content="center",
    )
