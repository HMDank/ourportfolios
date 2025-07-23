import reflex as rx
from contextlib import asynccontextmanager
from .utils.load_data import background_scheduler, initialize_database

# MUST BE IMPORTED!!!
from .pages import landing, select, landing_ticker, landing_industry, analyze, compare

initialize_database()


@asynccontextmanager
async def periodically_fetch_data(app):
    # Load data on initialize & keep fetching each 5 minutes
    background_scheduler.start()

    # Shut down the fetch on page shut down
    yield
    background_scheduler.shutdown()


app = rx.App(
    style={"font_family": "Outfit"},
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&display=swap"
    ],
    theme=rx.theme(accent_color="violet"),
    lifespan_tasks={periodically_fetch_data},
)
