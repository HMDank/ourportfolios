import reflex as rx
from .cards import card_wrapper


def card_link(content, href):
    style = {
        "color": "inherit",
        "textDecoration": "none",
        "width": "100%",
        "transition": "color 0.2s",
        "cursor": "pointer",
    }
    return rx.link(
        content,
        href=href,
        style=style,
        class_name="card-link",
    )


def card_roller(left_content, center_content, right_content):
    side_card_style = {
        "backdropFilter": "blur(14px)",
        "zIndex": 1,
        "border": "none",
        "boxShadow": "0 4px 24px rgba(0,0,0,0.10)",
        "position": "absolute",
        "top": "50%",
        "transform": "translateY(-50%)",
        "transition": "transform 0.2s, box-shadow 0.2s, z-index 0.2s",
        "width": "17em",
        "height": "7em",
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "center",
        "padding": "1em",
    }
    main_card_style = {
        "backdropFilter": "blur(14px)",
        "zIndex": 2,
        "position": "relative",
        "width": "22em",
        "transition": "transform 0.2s, box-shadow 0.2s, z-index 0.2s",
        "_hover": {
            "transform": "scale(1.05)",
        },
    }
    # Wrap side cards in boxes for horizontal slide on hover only
    left = rx.box(
        card_wrapper(left_content, {**side_card_style, "left": "-4em"}),
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
        card_wrapper(right_content, {**side_card_style, "right": "-4em"}),
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
    center = card_wrapper(center_content, main_card_style)
    return rx.box(
        left,
        right,
        center,
        position="relative",
        width="38em",
        height="11em",
        display="flex",
        align_items="center",
        justify_content="center",
    )
