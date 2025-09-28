import reflex as rx
from typing import List, Dict
import os
import psycopg2
from psycopg2.extras import RealDictCursor

from ..components.navbar import navbar
from ..components.page_roller import card_roller, card_link
from ..components.loading import loading_screen


DATABASE_URI = os.getenv("DATABASE_URI")


def get_db_connection():
    return psycopg2.connect(DATABASE_URI, cursor_factory=RealDictCursor)


def execute_query(query: str, params: tuple = None) -> List[Dict]:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if cur.description:
                return cur.fetchall()
            return []


class FrameworkState(rx.State):
    active_scope: str = "fundamental"
    scopes: List[Dict] = []
    frameworks: List[Dict] = []
    loading_scopes: bool = False
    loading_frameworks: bool = False
    selected_framework: Dict = {}
    show_dialog: bool = False

    async def on_load(self):
        await self.load_scopes()
        if self.scopes:
            await self.change_scope(self.scopes[0]["value"])

    async def load_scopes(self):
        self.loading_scopes = True
        try:
            query = "SELECT DISTINCT scope FROM frameworks.frameworks WHERE scope IS NOT NULL ORDER BY scope"
            scopes = execute_query(query)
            self.scopes = [
                {
                    "value": scope["scope"],
                    "title": scope["scope"].replace("_", " ").title(),
                }
                for scope in scopes
            ]

            if self.scopes and not self.active_scope:
                self.active_scope = self.scopes[0]["value"]

        except Exception as e:
            print(f"Error loading scopes: {e}")
            self.scopes = [
                {"value": "fundamental", "title": "Fundamental"},
                {"value": "technical", "title": "Technical"},
            ]
        finally:
            self.loading_scopes = False

    async def change_scope(self, scope: str):
        self.active_scope = scope
        await self.load_frameworks()

    async def load_frameworks(self):
        self.loading_frameworks = True
        try:
            query = """
                SELECT * FROM frameworks.frameworks 
                WHERE scope = %s
                ORDER BY title
            """
            frameworks = execute_query(query, (self.active_scope,))
            self.frameworks = frameworks
        except Exception as e:
            print(f"Error loading frameworks: {e}")
        finally:
            self.loading_frameworks = False

    @rx.event
    def show_framework_dialog(self, framework: Dict):
        self.selected_framework = framework
        self.show_dialog = True

    @rx.event
    def close_dialog(self):
        self.show_dialog = False
        self.selected_framework = {}

    @rx.event
    def handle_dialog_open(self, value: bool):
        if not value:
            self.close_dialog()


def scope_button(scope: Dict):
    return rx.button(
        rx.hstack(
            rx.text(scope["title"], size="3", weight="medium"),
            spacing="2",
            align="center",
            width="100%",
            justify="start",
        ),
        on_click=FrameworkState.change_scope(scope["value"]),
        variant="soft",
        color_scheme=rx.cond(
            FrameworkState.active_scope == scope["value"], "white", "gray"
        ),
        size="3",
        width="100%",
        height="3em",
        justify="start",
        style={
            "minHeight": "3em",
            "padding": "0.75em",
        },
    )


def framework_card(framework: Dict):
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading(framework["title"], size="6", weight="bold"),
                rx.spacer(),
                rx.hstack(
                    rx.badge(
                        framework["scope"],
                        color_scheme="plum",
                        variant="soft",
                        size="1",
                    ),
                    rx.badge(
                        framework["complexity"],
                        color_scheme=rx.cond(
                            framework["complexity"] == "complex", "accent", "jade"
                        ),
                        variant="soft",
                        size="1",
                    ),
                    spacing="2",
                ),
                justify="between",
                align="center",
                width="100%",
            ),
            rx.spacer(),
            rx.text(f"{framework['author']}", color="gray", size="2"),
            spacing="1",
            align="start",
            width="100%",
            justify="start",
            height="100%",
        ),
        width="100%",
        on_click=lambda: FrameworkState.show_framework_dialog(framework),
        style={
            "transition": "all 0.2s ease",
            "cursor": "pointer",
        },
        _hover={
            "transform": "translateY(-0.25em)",
            "boxShadow": "0 0.5em 1.5em rgba(0,0,0,0.1)",
        },
    )


def framework_dialog():
    return rx.cond(
        FrameworkState.show_dialog,
        rx.dialog.root(
            rx.dialog.trigger(rx.button("hidden", style={"display": "none"})),
            rx.dialog.content(
                rx.vstack(
                    rx.hstack(
                        rx.dialog.close(
                            rx.text(
                                rx.icon("x"),
                                on_click=FrameworkState.close_dialog,
                                style={
                                    "cursor": "pointer",
                                    "userSelect": "none",
                                    "color": rx.color("accent", 10),
                                    "_hover": {
                                        "color": rx.color("accent", 7),
                                    },
                                },
                            ),
                        ),
                        rx.spacer(),
                        rx.vstack(
                            rx.vstack(
                                rx.heading(
                                    FrameworkState.selected_framework["title"],
                                    size="7",
                                    weight="bold",
                                    text_align="right",
                                ),
                                rx.text(
                                    FrameworkState.selected_framework["author"],
                                    size="2",
                                    color="gray",
                                    text_align="right",
                                ),
                                align="end",
                                spacing="1",
                            ),
                            rx.hstack(
                                rx.badge(
                                    FrameworkState.selected_framework["scope"],
                                    color_scheme="plum",
                                    variant="soft",
                                    size="2",
                                ),
                                rx.badge(
                                    FrameworkState.selected_framework["complexity"],
                                    color_scheme=rx.cond(
                                        FrameworkState.selected_framework["complexity"]
                                        == "complex",
                                        "accent",
                                        "jade",
                                    ),
                                    variant="soft",
                                    size="2",
                                ),
                                spacing="2",
                                justify="end",
                            ),
                            align="end",
                            spacing="2",
                        ),
                        width="100%",
                        align="start",
                        justify="between",
                        padding_bottom="1rem",
                    ),
                    rx.vstack(
                        rx.scroll_area(
                            rx.blockquote(
                                FrameworkState.selected_framework["description"],
                                size="3",
                            ),
                            style={
                                "width": "100%",
                                "height": "100%",
                            },
                            scrollbars="vertical",
                        ),
                        spacing="2",
                        align="start",
                        width="100%",
                        height="100%",
                    ),
                    spacing="4",
                    align="start",
                    width="100%",
                    height="100%",
                ),
                style={
                    "width": "60vw",
                    "height": "52vh",
                    "maxWidth": "60vw",
                    "padding": "2rem",
                },
            ),
            open=True,
            on_open_change=FrameworkState.handle_dialog_open,
        ),
        None,
    )


def categories_sidebar():
    return rx.card(
        rx.vstack(
            rx.vstack(
                rx.text("Scope", size="4"),
                rx.cond(
                    FrameworkState.loading_scopes,
                    rx.center(rx.spinner(size="3"), height="6em"),
                    rx.vstack(
                        rx.foreach(FrameworkState.scopes, scope_button),
                        spacing="3",
                        width="100%",
                        align="stretch",
                    ),
                ),
                width="100%",
            ),
            spacing="4",
            width="100%",
            align="stretch",
        ),
        flex=1,
        style={"padding": "0.75em", "minWidth": "15em", "overflow": "hidden"},
    )


def frameworks_content():
    return rx.fragment(
        rx.card(
            rx.vstack(
                rx.text("Frameworks", size="4"),
                rx.cond(
                    FrameworkState.loading_frameworks,
                    rx.center(rx.spinner(size="3"), height="12em"),
                    rx.cond(
                        FrameworkState.frameworks.length() > 0,
                        rx.vstack(
                            rx.foreach(FrameworkState.frameworks, framework_card),
                            spacing="3",
                            width="100%",
                            padding="0.5em",
                        ),
                        rx.center(
                            rx.text(
                                "No frameworks in this category yet.",
                                color="gray",
                                size="3",
                            ),
                            height="12em",
                        ),
                    ),
                ),
                spacing="2",
                width="100%",
                align="stretch",
            ),
            flex=4,
            min_width=0,
            max_width="100%",
            style={"padding": "0.75em", "minWidth": 0, "overflow": "hidden"},
        ),
        framework_dialog(),
    )


def page_selection():
    return rx.box(
        card_roller(
            card_link(
                rx.hstack(
                    rx.icon("chevron_left", size=32),
                    rx.vstack(
                        rx.heading("Ourportfolios", weight="regular", size="5"),
                        align="center",
                        justify="center",
                        height="100%",
                        spacing="1",
                    ),
                    align="center",
                    justify="center",
                ),
                href="/",
            ),
            card_link(
                rx.vstack(
                    rx.heading("Recommend", weight="regular", size="7"),
                    rx.text("Framework Selection", size="3"),
                    align="center",
                    justify="center",
                    height="100%",
                    spacing="1",
                ),
                href="/recommend",
            ),
            card_link(
                rx.hstack(
                    rx.vstack(
                        rx.heading("Select", weight="regular", size="5"),
                        rx.text("caijdo", size="1"),
                        align="center",
                        justify="center",
                        height="100%",
                        spacing="1",
                    ),
                    rx.icon("chevron_right", size=32),
                    align="center",
                    justify="center",
                ),
                href="/select",
            ),
        ),
        width="100%",
        display="flex",
        justify_content="center",
        align_items="center",
        margin="0",
        padding="0",
    )


@rx.page(route="/recommend", on_load=FrameworkState.on_load)
def index() -> rx.Component:
    return rx.fragment(
        loading_screen(),
        navbar(),
        page_selection(),
        rx.center(
            rx.box(
                rx.hstack(
                    categories_sidebar(),
                    frameworks_content(),
                    spacing="3",
                    width="100%",
                ),
                width="86vw",
            ),
            width="100%",
            padding="2rem",
            padding_top="5rem",
            position="relative",
        ),
    )
