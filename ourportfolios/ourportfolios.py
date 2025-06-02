import reflex as rx
from .pages import landing, select, landing_ticker  # MUST BE IMPORTED!!!
from .utils.populate_db import load_data_vni


app = rx.App(
    theme=rx.theme(
        accent_color="violet"
    )
)
