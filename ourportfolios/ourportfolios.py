import reflex as rx

from .pages import landing, select, landing_ticker, analyze  # MUST BE IMPORTED!!!


app = rx.App(
    theme=rx.theme(
        accent_color="violet"
    )
)
