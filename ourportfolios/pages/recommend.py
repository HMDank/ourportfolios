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
    sort_by: str = "Sort by Complexity"
    active_category: Optional[str] = None
    categories: List[Dict] = []  # Will contain either complexity levels or authors
    frameworks: List[Dict] = []

    # Form states for adding new items
    show_framework_form: bool = False
    new_framework_title: str = ""
    new_framework_description: str = ""
    new_framework_author: str = ""
    new_framework_complexity: Literal["beginner-friendly", "complex"] = (
        "beginner-friendly"
    )

    # Loading states
    loading_categories: bool = False
    loading_frameworks: bool = False

    async def on_load(self):
        """Load initial data when page loads"""
        await self.load_categories()
        if self.categories:
            await self.set_active_category(self.categories[0]["value"])

    async def change_sort_by(self, sort_by: str):
        """Change the sorting method and reload categories"""
        self.sort_by = sort_by
        await self.load_categories()

    async def load_categories(self):
        """Load all categories based on sort_by selection"""
        self.loading_categories = True
        try:
            if self.sort_by == "Sort by Complexity":
                self.categories = [
                    {"value": "beginner-friendly", "title": "Beginner-Friendly"},
                    {"value": "complex", "title": "Complex"},
                ]
            else:  # "Sort by Author"
                query = "SELECT DISTINCT author FROM frameworks.frameworks WHERE author IS NOT NULL ORDER BY author"
                authors = execute_query(query)
                self.categories = [
                    {"value": author["author"], "title": author["author"]}
                    for author in authors
                ]
        except Exception as e:
            print(f"Error loading categories: {e}")
        finally:
            self.loading_categories = False

    async def load_frameworks(self, category: str):
        """Load frameworks for specific category based on sort_by"""
        self.loading_frameworks = True
        try:
            if self.sort_by == "Sort by Complexity":
                query = """
                    SELECT * FROM frameworks.frameworks 
                    WHERE complexity = %s 
                    ORDER BY title
                """
            else:  # Sort by Author
                query = """
                    SELECT * FROM frameworks.frameworks 
                    WHERE author = %s 
                    ORDER BY title
                """

            frameworks = execute_query(query, (category,))
            self.frameworks = frameworks
        except Exception as e:
            print(f"Error loading frameworks: {e}")
        finally:
            self.loading_frameworks = False

    async def set_active_category(self, category: str):
        """Set active category and load its frameworks"""
        self.active_category = category
        await self.load_frameworks(category)

    async def add_framework(self):
        """Add new framework to database"""
        if not self.new_framework_title.strip():
            return

        try:
            query = """
                INSERT INTO frameworks.frameworks 
                (title, description, author, complexity) 
                VALUES (%s, %s, %s, %s)
            """
            params = (
                self.new_framework_title.strip(),
                self.new_framework_description.strip() or None,
                self.new_framework_author.strip() or None,
                self.new_framework_complexity,
            )

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    conn.commit()

            # Clear form and reload frameworks
            self.new_framework_title = ""
            self.new_framework_description = ""
            self.new_framework_author = ""
            self.show_framework_form = False

            # Reload frameworks if current category matches the new framework
            if (
                self.sort_by == "Sort by Complexity"
                and self.active_category == self.new_framework_complexity
            ) or (
                self.sort_by == "author"
                and self.active_category == self.new_framework_author
            ):
                await self.load_frameworks(self.active_category)

        except Exception as e:
            print(f"Error adding framework: {e}")

    def toggle_framework_form(self):
        self.show_framework_form = not self.show_framework_form


# UI Components
def sorting_selector():
    """Create sorting method selector"""
    return rx.radio_group(
        items=[
            "Sort by Complexity",
            "Sort by Author",
        ],
        value=FrameworkState.sort_by,
        on_change=FrameworkState.change_sort_by,
        direction="row",
        spacing="4",
    )


def category_button(category: Dict):
    """Create a category button"""
    return rx.button(
        rx.hstack(
            rx.text(category["title"], size="2", weight="medium"),
            spacing="2",
            align="center",
            width="100%",
            justify="start",
        ),
        on_click=FrameworkState.set_active_category(category["value"]),
        variant=rx.cond(
            FrameworkState.active_category == category["value"], "solid", "outline"
        ),
        color_scheme=rx.cond(
            FrameworkState.active_category == category["value"], "blue", "gray"
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
                rx.heading(framework["title"], size="3"),
                rx.spacer(),
                rx.badge(framework["complexity"], color_scheme="purple"),
                justify="between",
                align="center",
                width="100%",
            ),
            rx.cond(
                framework["description"],
                rx.text(framework["description"], size="2", color="gray"),
                rx.fragment(),
            ),
            rx.hstack(
                rx.text(f"Author: {framework['author']}", color="gray", size="2"),
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


def add_category_form():
    """Form to add new category"""
    return rx.cond(
        FrameworkState.show_category_form,
        rx.card(
            rx.vstack(
                rx.heading("Add New Category", size="3"),
                rx.input(
                    placeholder="Category Title",
                    value=FrameworkState.new_category_name,
                    on_change=FrameworkState.set_new_category_name,
                ),
                rx.input(
                    placeholder="Description (optional)",
                    value=FrameworkState.new_category_description,
                    on_change=FrameworkState.set_new_category_description,
                ),
                rx.hstack(
                    rx.button(
                        "Cancel",
                        on_click=FrameworkState.toggle_category_form,
                        variant="outline",
                    ),
                    rx.button("Add Category", on_click=FrameworkState.add_category),
                    spacing="2",
                ),
                spacing="3",
                width="100%",
            ),
            margin_bottom="1em",
        ),
        rx.fragment(),
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
                rx.select(
                    ["beginner-friendly", "complex"],
                    value=FrameworkState.new_framework_complexity,
                    placeholder="Select complexity level",
                    on_change=FrameworkState.set_new_framework_complexity,
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
    """Left sidebar with categories"""
    return rx.card(
        rx.vstack(
            rx.vstack(
                rx.heading("Sort By", size="3"),
                sorting_selector(),
                width="100%",
                margin_bottom="1em",
            ),
            rx.vstack(
                rx.heading("Categories", size="3"),
                rx.cond(
                    FrameworkState.loading_categories,
                    rx.spinner(),
                    rx.vstack(
                        rx.foreach(FrameworkState.categories, category_button),
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
