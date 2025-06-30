import reflex as rx

# MUST BE IMPORTED!!!
from .pages import landing, select, landing_ticker, landing_industry, analyze, compare

app = rx.App(
    theme=rx.theme(
        accent_color="violet"
    )
)
