import reflex as rx


def news_card(text):
    return rx.card(
        rx.inset(
            rx.image(
                src="/reflex_banner.png",
                width="100%",
                height="auto",
            ),
            side="top",
            pb="current",
        ),
        rx.text(
            f"{text}"
        ),
        width="25vw",
    )
