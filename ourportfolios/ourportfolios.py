import reflex as rx

from .utils.load_data import populate_db

from .pages import landing, select, landing_ticker, analyze  # MUST BE IMPORTED!!!

populate_db()

app = rx.App(
    theme=rx.theme(
        accent_color="violet"
    )
)
