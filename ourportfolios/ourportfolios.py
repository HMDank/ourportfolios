import reflex as rx
from .pages import landing, select, landing_ticker  # MUST BE IMPORTED!!!
from .utils.load_data import populate_db

populate_db()
app = rx.App(
    theme=rx.theme(
        accent_color="violet"
    )
)
