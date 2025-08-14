import reflex as rx
# from contextlib import asynccontextmanager
# from .utils.scheduler import db_scheduler
from .utils.load_data import populate_db

# MUST BE IMPORTED!!!
from .pages import landing, select, landing_ticker, landing_industry, analyze, compare  # noqa: F401


populate_db()


# @asynccontextmanager
# async def periodically_fetch_data(app):
#     # Load data on initialize & keep fetching each 5 minutes
#     db_scheduler.start()

#     # Shut down the fetch on page shut down
#     yield
#     db_scheduler.shutdown(wait=True)


app = rx.App(
    style={"font_family": "Outfit"},
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&display=swap"
    ],
    theme=rx.theme(accent_color="violet"),
    #lifespan_tasks={periodically_fetch_data},
)
