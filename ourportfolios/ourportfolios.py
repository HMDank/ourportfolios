import reflex as rx
from .utils.load_data import populate_db

# MUST BE IMPORTED!!!
from .pages import landing, select, landing_ticker, landing_industry, analyze, compare  # noqa: F401


populate_db()


app = rx.App(
    style={"font_family": "Outfit"},
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&display=swap"
    ],
    theme=rx.theme(accent_color="violet"),
)
