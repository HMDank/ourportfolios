import reflex as rx
from .pages import landing, select, landing_ticker  # MUST BE IMPORTED!!!
from .utils.load_raw_data import load_data_vni


app = rx.App(
    theme=rx.theme(
        accent_color="violet"
    )
)
