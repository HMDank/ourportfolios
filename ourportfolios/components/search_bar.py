import reflex as rx


def search_bar():
    return rx.input(
        rx.input.slot(rx.icon(tag="search", size=16)),
        placeholder="Search for a ticker here!",
        type="search",
        size="2",
        width="16vw",
        justify="end",
    )
