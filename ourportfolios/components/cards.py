import reflex as rx

cards = [
    {"title": "Recommend", "details": "Card 1 details", "link": "/recommend"},
    {"title": "Select", "details": "Card 2 details", "link": "/select"},
    {"title": "Analyze", "details": "Card 3 details", "link": "/analyze"},
    {"title": "Simulate", "details": "Card 4 details", "link": "/simulate"},
]


def portfolio_card(card, idx, total):
    def get_card_position_size(idx, total):
        spread_x = 65  # percent of parent width; lower for more overlap
        spread_y = 15  # vertical spread
        width = 23  # percent of parent width; adjust for desired overlap
        height = 48  # percent of parent height

        if total > 1:
            center = (idx / (total - 1)) * spread_x + (50 - spread_x / 2)
            left = center - width / 2
            left = max(0, min(left, 100 - width))
            top = (idx / (total - 1)) * spread_y
        else:
            left = 50 - width / 2
            top = 20

        return f"{top}%", f"{left}%", f"{width}%", f"{height}%"

    top, left, width, height = get_card_position_size(idx, total)
    return rx.link(
        rx.card(
            rx.vstack(
                rx.icon(tag=card["icon"], size=48, color_scheme="teal"),
                rx.heading(card["title"], size="5", weight="medium"),
                rx.text(card["details"], align="center", color_scheme="gray"),
                width="100%",
                align="center",
            ),
            height=height,
            width=width,
            position="absolute",
            top=top,
            left=left,
            transition="transform 0.15s, box-shadow 0.2s, z-index 0.2s",
            _hover={
                "transform": "scale(1.05)",
                "z_index": "10",
                "box_shadow": "0 8px 32px rgba(0,0,0,0.25)",
            },
            padding="1.2rem",
        ),
        href=card["link"],
        style={"textDecoration": "none"},
    )


def stats_card(complexity: str, name: str, description: str, link: str) -> rx.Component:
    return rx.link(
        rx.card(
            rx.vstack(
                rx.text(
                    complexity,
                    font_size="1.5em",
                    weight="medium",
                    color_scheme="violet",
                ),
                rx.heading(name, font_size="2.5em", weight="bold", color="white"),
                rx.text(
                    description,
                    font_size="0.9em",
                    color_scheme="gray",
                    word_break="break-all",
                ),
                spacing="3",
                align="start",
            ),
            # background_color=rx.color("gray", 2),
            transition="transform 0.15s, box-shadow 0.2s, z-index 0.2s",
            _hover={
                "transform": "scale(1.05)",
                "z_index": "10",
                "box_shadow": "0 8px 32px rgba(0,0,0,0.25)",
            },
            padding="2em",
            min_height="30vh",
            max_height="50vh",
        ),
        href=link,
    )


def card_wrapper(*content, style=None):
    style = style or {}
    return rx.card(
        *content,
        border="none",
        background_color="transparent",
        style=style,
        spacing="4",
    )
