import reflex as rx

from .utils.load_data import run_scheduler

# MUST BE IMPORTED!!!
from .pages import landing, select, landing_ticker, landing_industry, analyze, compare

run_scheduler()


app = rx.App(
    style={"font_family": "Outfit"},
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&display=swap"
    ],
    theme=rx.theme(accent_color="violet"),
)
