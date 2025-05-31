import reflex as rx

cards = [
    {"title": "Recommend", "details": "Card 1 details",
        "link": "/recommend"},
    {"title": "Select", "details": "Card 2 details",
        "link": "/select"},
    {"title": "Analyze", "details": "Card 3 details", "link": "/analyze"},
    {"title": "Simulate", "details": "Card 4 details",
        "link": "/simulate"},
]


def get_card_position_size(idx, total):
    spread_x = 65  # percent of parent width; lower for more overlap
    spread_y = 15  # vertical spread
    width = 24     # percent of parent width; adjust for desired overlap
    height = 48    # percent of parent height

    if total > 1:
        center = (idx / (total - 1)) * spread_x + (50 - spread_x / 2)
        left = center - width / 2
        left = max(0, min(left, 100 - width))
        top = (idx / (total - 1)) * spread_y
    else:
        left = 50 - width / 2
        top = 20

    return f"{top}%", f"{left}%", f"{width}%", f"{height}%"


def portfolio_card(card, idx, total):
    top, left, width, height = get_card_position_size(idx, total)
    return rx.link(
        rx.card(
            rx.text(card["title"], size="3", weight="bold"),
            rx.text(card["details"], size="2"),
            height=height, width=width,
            position="absolute", top=top, left=left,
            transition="transform 0.15s, box-shadow 0.2s, z-index 0.2s",
            _hover={
                "transform": "scale(1.09)",
                "z_index": "10",
                "box_shadow": "0 8px 32px rgba(0,0,0,0.25)",
            },
            padding="1.2rem",
        ),
        href=card["link"],
        style={"textDecoration": "none"},
    )

