import reflex as rx
from typing import List, Dict, Optional, Literal
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

from ..components.navbar import navbar
from ..components.page_roller import card_roller, card_link
from ..components.loading import loading_screen


# Database connection
DATABASE_URI = os.getenv("DATABASE_URI")


def get_db_connection():
    """Create and return a database connection"""
    return psycopg2.connect(DATABASE_URI, cursor_factory=RealDictCursor)


def execute_query(query: str, params: tuple = None) -> List[Dict]:
    """Execute a query and return results as a list of dictionaries"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if cur.description:
                return cur.fetchall()
            return []


# State Management
class FrameworkState(rx.State):
    # UI State
    active_scope: str = "fundamental"
    scopes: List[Dict] = []
    frameworks: List[Dict] = []

    # Form states for adding new items
    show_framework_form: bool = False
    new_framework_title: str = ""
    new_framework_description: str = ""
    new_framework_author: str = ""
    new_framework_complexity: Literal["beginner-friendly", "complex"] = (
        "beginner-friendly"
    )
    new_framework_scope: str = "fundamental"

    # Loading states
    loading_scopes: bool = False
    loading_frameworks: bool = False

    async def on_load(self):
        """Load initial data when page loads"""
        await self.load_scopes()
        if self.scopes:
            await self.change_scope(self.scopes[0]["value"])

    async def load_scopes(self):
        """Load all available scopes from database"""
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

            # Set default active scope if available
            if self.scopes and not self.active_scope:
                self.active_scope = self.scopes[0]["value"]

        except Exception as e:
            print(f"Error loading scopes: {e}")
            # Fallback to default scopes if database fails
            self.scopes = [
                {"value": "fundamental", "title": "Fundamental"},
                {"value": "technical", "title": "Technical"},
            ]
        finally:
            self.loading_scopes = False

    async def change_scope(self, scope: str):
        """Change the active scope and reload frameworks"""
        self.active_scope = scope
        await self.load_frameworks()

    async def load_frameworks(self):
        """Load frameworks for active scope"""
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

    async def add_framework(self):
        """Add new framework to database"""
        if not self.new_framework_title.strip():
            return

        try:
            query = """
                INSERT INTO frameworks.frameworks 
                (title, description, author, complexity, scope) 
                VALUES (%s, %s, %s, %s, %s)
            """
            params = (
                self.new_framework_title.strip(),
                self.new_framework_description.strip() or None,
                self.new_framework_author.strip() or None,
                self.new_framework_complexity,
                self.new_framework_scope,
            )

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    conn.commit()

            # Clear form
            self.new_framework_title = ""
            self.new_framework_description = ""
            self.new_framework_author = ""
            self.new_framework_scope = "fundamental"
            self.show_framework_form = False

            # Reload frameworks if current scope matches
            if self.active_scope == self.new_framework_scope:
                await self.load_frameworks()

            # Reload scopes in case a new scope was added
            await self.load_scopes()

        except Exception as e:
            print(f"Error adding framework: {e}")

    def toggle_framework_form(self):
        """Toggle the framework form visibility"""
        self.show_framework_form = not self.show_framework_form

    def set_new_framework_title(self, value: str):
        """Set new framework title"""
        self.new_framework_title = value

    def set_new_framework_description(self, value: str):
        """Set new framework description"""
        self.new_framework_description = value

    def set_new_framework_author(self, value: str):
        """Set new framework author"""
        self.new_framework_author = value

    def set_new_framework_complexity(self, value: str):
        """Set new framework complexity"""
        self.new_framework_complexity = value

    def set_new_framework_scope(self, value: str):
        """Set new framework scope"""
        self.new_framework_scope = value


# UI Components
def scope_button(scope: Dict):
    """Create a scope button"""
    return rx.button(
        rx.hstack(
            rx.text(scope["title"], size="2", weight="medium"),
            spacing="2",
            align="center",
            width="100%",
            justify="start",
        ),
        on_click=FrameworkState.change_scope(scope["value"]),
        variant=rx.cond(
            FrameworkState.active_scope == scope["value"], "solid", "outline"
        ),
        color_scheme=rx.cond(
            FrameworkState.active_scope == scope["value"], "white", "gray"
        ),
        size="2",
        width="100%",
        justify="start",
    )


def framework_card(framework: Dict):
    """Create a framework card"""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading(framework["title"], size="4"),
                rx.spacer(),
                rx.hstack(
                    rx.badge(framework["scope"], color_scheme="blue", variant="soft"),
                    rx.badge(framework["complexity"], color_scheme="purple"),
                    spacing="2",
                ),
                justify="between",
                align="center",
                width="100%",
            ),
            rx.hstack(
                rx.text(f"{framework['author']}", color="gray", size="2"),
                spacing="3",
                width="100%",
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        width="100%",
        margin_bottom="0.5em",
    )


def add_framework_form():
    """Form to add new framework"""
    return rx.cond(
        FrameworkState.show_framework_form,
        rx.card(
            rx.vstack(
                rx.heading("Add New Framework", size="3"),
                rx.input(
                    placeholder="Framework title",
                    value=FrameworkState.new_framework_title,
                    on_change=FrameworkState.set_new_framework_title,
                ),
                rx.text_area(
                    placeholder="Description (optional)",
                    value=FrameworkState.new_framework_description,
                    on_change=FrameworkState.set_new_framework_description,
                ),
                rx.input(
                    placeholder="Author name",
                    value=FrameworkState.new_framework_author,
                    on_change=FrameworkState.set_new_framework_author,
                ),
                rx.hstack(
                    rx.select(
                        ["fundamental", "technical"],
                        value=FrameworkState.new_framework_scope,
                        placeholder="Select scope",
                        on_change=FrameworkState.set_new_framework_scope,
                    ),
                    rx.select(
                        ["beginner-friendly", "complex"],
                        value=FrameworkState.new_framework_complexity,
                        placeholder="Select complexity",
                        on_change=FrameworkState.set_new_framework_complexity,
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.hstack(
                    rx.button(
                        "Cancel",
                        on_click=FrameworkState.toggle_framework_form,
                        variant="outline",
                    ),
                    rx.button("Add Framework", on_click=FrameworkState.add_framework),
                    spacing="2",
                ),
                spacing="3",
                width="100%",
            ),
            margin_bottom="1em",
        ),
        rx.fragment(),
    )


def categories_sidebar():
    """Left sidebar with scope selection only"""
    return rx.card(
        rx.vstack(
            rx.vstack(
                rx.heading("Scope", size="3"),
                rx.cond(
                    FrameworkState.loading_scopes,
                    rx.spinner(),
                    rx.vstack(
                        rx.foreach(FrameworkState.scopes, scope_button),
                        spacing="2",
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
        min_width=0,
        max_width="100%",
        style={"padding": "1em", "minWidth": 0, "overflow": "hidden"},
    )


def frameworks_content():
    """Right content area with frameworks"""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Frameworks", size="3"),
                rx.button(
                    rx.icon("plus", size=16),
                    on_click=FrameworkState.toggle_framework_form,
                    size="1",
                    variant="outline",
                ),
                justify="between",
                align="center",
                width="100%",
                margin_bottom="1em",
            ),
            add_framework_form(),
            rx.cond(
                FrameworkState.loading_frameworks,
                rx.spinner(),
                rx.cond(
                    FrameworkState.frameworks.length() > 0,
                    rx.vstack(
                        rx.foreach(FrameworkState.frameworks, framework_card),
                        spacing="2",
                        width="100%",
                    ),
                    rx.text(
                        "No frameworks in this category yet. Add one!",
                        color="gray",
                        size="2",
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
        style={"padding": "1em", "minWidth": 0, "overflow": "hidden"},
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
                    spacing="4",
                    width="100%",
                    align="stretch",
                    justify="between",
                ),
                width="86vw",
            ),
            width="100%",
            padding="2em",
            padding_top="5em",
            position="relative",
        ),
    )
