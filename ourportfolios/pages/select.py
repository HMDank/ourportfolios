import reflex as rx


class Domain1State(rx.State):
    # State variables and event handlers for this domain
    pass


@rx.page(route="/select")
def select():
    return rx.text("Select Page")
