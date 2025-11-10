import reflex as rx
from typing import List, Dict, Any, cast
import os
import psycopg2
from psycopg2.extras import RealDictCursor

from ..components.navbar import navbar
from ..components.page_roller import card_roller, card_link
from ..components.loading import loading_screen
from ..state.framework_state import GlobalFrameworkState

DATABASE_URI = os.getenv("DATABASE_URI")


def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URI, cursor_factory=RealDictCursor)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise


def execute_query(query: str, params: tuple = None) -> List[Dict]:
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                if cur.description:
                    return cur.fetchall()
                return []
    except Exception as e:
        print(f"Error executing query: {e}")
        return []


class FrameworkState(rx.State):
    active_scope: str = "fundamental"
    scopes: List[Dict] = []
    frameworks: List[Dict] = []
    loading_scopes: bool = False
    loading_frameworks: bool = False
    selected_framework: Dict = {}
    show_dialog: bool = False
    show_add_dialog: bool = False

    # Form fields
    form_title: str = ""
    form_description: str = ""
    form_author: str = ""
    form_complexity: str = "beginner-friendly"
    form_scope: str = ""
    form_industry: str = "general"
    form_source_name: str = ""
    form_source_url: str = ""

    # Metrics management
    form_metrics: List[
        Dict
    ] = []  # [{"name": str, "category": str, "enabled": bool, "order": int}]

    # Available metrics by category (matching financial_statements.py structure)
    available_categories: List[str] = [
        "Per Share Value",
        "Growth Rate",
        "Profitability",
        "Valuation",
        "Leverage & Liquidity",
        "Efficiency",
    ]

    # Metrics for each category
    per_share_metrics: List[str] = [
        "Earnings",
        "Book Value",
        "Free Cash Flow",
        "Dividend",
        "Revenues",
    ]
    growth_rate_metrics: List[str] = [
        "Revenues YoY",
        "Earnings YoY",
        "Free Cash Flow YoY",
        "Book Value YoY",
    ]
    profitability_metrics: List[str] = [
        "ROE",
        "ROIC",
        "Net Margin",
        "Gross Margin",
        "Operating Margin",
        "EBITDA Margin",
    ]
    valuation_metrics: List[str] = ["P/E", "P/B", "P/S", "EV/EBITDA"]
    leverage_liquidity_metrics: List[str] = [
        "Debt/Equity",
        "Current Ratio",
        "Quick Ratio",
        "Interest Coverage",
        "Cash Ratio",
    ]
    efficiency_metrics: List[str] = ["ROA", "Asset Turnover", "Dividend Payout %"]

    show_add_metric_dialog: bool = False
    new_metric_name: str = ""
    new_metric_category: str = "Per Share Value"

    @rx.var
    def metrics_count(self) -> int:
        return len(self.form_metrics)

    # Form field setters
    @rx.event
    def set_form_title(self, value: str):
        self.form_title = value

    @rx.event
    def set_form_description(self, value: str):
        self.form_description = value

    @rx.event
    def set_form_author(self, value: str):
        self.form_author = value

    @rx.event
    def set_form_complexity(self, value: str):
        self.form_complexity = value

    @rx.event
    def set_form_scope(self, value: str):
        self.form_scope = value

    @rx.event
    def set_form_industry(self, value: str):
        self.form_industry = value

    @rx.event
    def set_form_source_name(self, value: str):
        self.form_source_name = value

    @rx.event
    def set_form_source_url(self, value: str):
        self.form_source_url = value

    @rx.event
    def set_new_metric_name(self, value: str):
        self.new_metric_name = value

    @rx.event
    def set_new_metric_category(self, value: str):
        self.new_metric_category = value

    @rx.event
    def add_metric_to_form(self):
        """Add a new metric to the framework's metric list"""
        if not self.new_metric_name:
            return

        # Check if metric already exists
        if any(m["name"] == self.new_metric_name for m in self.form_metrics):
            return

        # Add metric with next order
        next_order = len(self.form_metrics)
        self.form_metrics.append(
            {
                "name": self.new_metric_name,
                "category": self.new_metric_category,
                "enabled": True,
                "order": next_order,
            }
        )

        # Reset form
        self.new_metric_name = ""
        self.show_add_metric_dialog = False

    @rx.event
    def remove_metric(self, metric_name: str):
        """Remove a metric from the list"""
        self.form_metrics = [m for m in self.form_metrics if m["name"] != metric_name]
        # Reorder remaining metrics
        for i, metric in enumerate(self.form_metrics):
            metric["order"] = i

    @rx.event
    def toggle_metric_enabled(self, metric_name: str):
        """Toggle whether a metric is enabled"""
        for metric in self.form_metrics:
            if metric["name"] == metric_name:
                metric["enabled"] = not metric["enabled"]
                break

    @rx.event
    def move_metric_up(self, metric_name: str):
        """Move a metric up in the order"""
        for i, metric in enumerate(self.form_metrics):
            if metric["name"] == metric_name and i > 0:
                # Swap with previous
                self.form_metrics[i], self.form_metrics[i - 1] = (
                    self.form_metrics[i - 1],
                    self.form_metrics[i],
                )
                self.form_metrics[i]["order"] = i
                self.form_metrics[i - 1]["order"] = i - 1
                break

    @rx.event
    def move_metric_down(self, metric_name: str):
        """Move a metric down in the order"""
        for i, metric in enumerate(self.form_metrics):
            if metric["name"] == metric_name and i < len(self.form_metrics) - 1:
                # Swap with next
                self.form_metrics[i], self.form_metrics[i + 1] = (
                    self.form_metrics[i + 1],
                    self.form_metrics[i],
                )
                self.form_metrics[i]["order"] = i
                self.form_metrics[i + 1]["order"] = i + 1
                break

    @rx.event
    def open_add_metric_dialog(self):
        self.show_add_metric_dialog = True
        self.new_metric_name = ""

    @rx.event
    def close_add_metric_dialog(self):
        self.show_add_metric_dialog = False

    @rx.event
    def handle_add_metric_dialog_open(self, value: bool):
        if not value:
            self.close_add_metric_dialog()

    async def on_load(self):
        await self.load_scopes()
        if self.scopes:
            await self.change_scope(self.scopes[0]["value"])

    async def load_scopes(self):
        self.loading_scopes = True
        try:
            # Always show all available scopes, regardless of whether they have frameworks
            self.scopes = [
                {"value": "fundamental", "title": "Fundamental"},
                {"value": "technical", "title": "Technical"},
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
            # Load frameworks with their metrics
            query = """
                SELECT 
                    f.*,
                    COALESCE(
                        json_agg(
                            json_build_object(
                                'name', m.metrics,
                                'type', m.category,
                                'order', m.display_order
                            ) ORDER BY m.display_order
                        ) FILTER (WHERE m.id IS NOT NULL),
                        '[]'::json
                    ) as metrics
                FROM frameworks.frameworks_df f
                LEFT JOIN frameworks.framework_metrics_df m ON f.id = m.framework_id
                WHERE f.scope = %s
                GROUP BY f.id
                ORDER BY f.title
            """
            frameworks = execute_query(query, (self.active_scope,))
            self.frameworks = frameworks
        except Exception as e:
            print(f"Error loading frameworks: {e}")
            self.frameworks = []
            # Don't use yield here since this is called from on_load
            # Error will be logged and empty list shown gracefully
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

    @rx.event
    def open_add_dialog(self):
        self.form_scope = self.active_scope
        self.form_title = ""
        self.form_description = ""
        self.form_author = ""
        self.form_complexity = "beginner-friendly"
        self.form_industry = "general"
        self.form_source_name = ""
        self.form_source_url = ""
        self.form_metrics = []  # Reset metrics
        self.show_add_dialog = True

    @rx.event
    def close_add_dialog(self):
        self.show_add_dialog = False

    @rx.event
    def handle_add_dialog_open(self, value: bool):
        if not value:
            self.close_add_dialog()

    async def submit_framework(self):
        if not self.form_title or not self.form_author:
            return

        try:
            # Insert framework first
            framework_query = """
                INSERT INTO frameworks.frameworks_df 
                (title, description, author, complexity, scope, industry, source_name, source_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Insert framework and get its id
                    cur.execute(
                        framework_query,
                        (
                            self.form_title,
                            self.form_description,
                            self.form_author,
                            self.form_complexity,
                            self.form_scope,
                            self.form_industry,
                            self.form_source_name if self.form_source_name else None,
                            self.form_source_url if self.form_source_url else None,
                        ),
                    )
                    result = cast(Dict[str, Any], cur.fetchone())
                    framework_id = result["id"]

                    # Insert metrics if any
                    if self.form_metrics:
                        metrics_query = """
                            INSERT INTO frameworks.framework_metrics_df 
                            (framework_id, category, metrics, display_order)
                            VALUES (%s, %s, ARRAY[%s], %s)
                        """
                        for metric in self.form_metrics:
                            cur.execute(
                                metrics_query,
                                (
                                    framework_id,
                                    metric[
                                        "category"
                                    ],  # Category name (e.g., "Per Share Value", "Profitability")
                                    metric[
                                        "name"
                                    ],  # Actual metric name (e.g., "ROE", "P/E", "Earnings")
                                    metric["order"],  # display order
                                ),
                            )

                    conn.commit()

            self.close_add_dialog()
            await self.load_frameworks()
        except Exception as e:
            print(f"Error adding framework: {e}")

    def select_and_navigate_framework(self):
        """Select the current framework and navigate to ticker selection."""
        if not self.selected_framework:
            return

        # Get framework id - try different possible key names
        framework_id = None
        for key in ["id", "framework_id", "pk"]:
            if key in self.selected_framework:
                framework_id = self.selected_framework[key]
                break

        if framework_id is None:
            print(
                f"Error: Could not find id in framework: {self.selected_framework.keys()}"
            )
            return

        # Set the global framework selection

        # Close dialog
        self.close_dialog()

        return [
            GlobalFrameworkState.select_framework(framework_id),
            rx.redirect("/select"),
        ]


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
        padding="0.75em",
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
                        width="100%",
                        align="start",
                        justify="between",
                        padding_bottom="1rem",
                    ),
                    rx.hstack(
                        rx.cond(
                            FrameworkState.selected_framework.get("source_name"),
                            rx.hstack(
                                rx.icon("book-open", size=16),
                                rx.text("Source:", weight="bold", size="2"),
                                rx.cond(
                                    FrameworkState.selected_framework.get("source_url"),
                                    rx.link(
                                        FrameworkState.selected_framework[
                                            "source_name"
                                        ],
                                        href=FrameworkState.selected_framework[
                                            "source_url"
                                        ],
                                        is_external=True,
                                        size="2",
                                    ),
                                    rx.text(
                                        FrameworkState.selected_framework[
                                            "source_name"
                                        ],
                                        size="2",
                                    ),
                                ),
                                spacing="2",
                                align="center",
                            ),
                            None,
                        ),
                        rx.spacer(),
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
                        ),
                        width="100%",
                        align="center",
                        padding_bottom="1rem",
                    ),
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
                    rx.hstack(
                        rx.spacer(),
                        rx.button(
                            "Cancel",
                            on_click=FrameworkState.close_dialog,
                            variant="soft",
                            color_scheme="gray",
                            size="3",
                        ),
                        rx.button(
                            "Select This Framework",
                            on_click=lambda: FrameworkState.select_and_navigate_framework(),
                            size="3",
                            color_scheme="violet",
                        ),
                        spacing="2",
                        width="100%",
                        justify="end",
                        padding_top="1rem",
                    ),
                    spacing="4",
                    align="start",
                    width="100%",
                    height="100%",
                ),
                style={
                    "width": "60vw",
                    "height": "58vh",
                    "maxWidth": "60vw",
                    "padding": "2rem",
                },
            ),
            open=True,
            on_open_change=FrameworkState.handle_dialog_open,
        ),
        None,
    )


def metric_item(metric: Dict, index: int):
    """Component for a single metric in the list"""
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.text(metric["name"], size="3", weight="medium"),
                rx.badge(metric["category"], size="1", variant="soft"),
                spacing="1",
                align="start",
            ),
            rx.spacer(),
            rx.hstack(
                rx.icon_button(
                    rx.icon("arrow-up", size=16),
                    size="1",
                    variant="ghost",
                    on_click=lambda: FrameworkState.move_metric_up(metric["name"]),
                    disabled=index == 0,
                ),
                rx.icon_button(
                    rx.icon("arrow-down", size=16),
                    size="1",
                    variant="ghost",
                    on_click=lambda: FrameworkState.move_metric_down(metric["name"]),
                    disabled=index >= FrameworkState.metrics_count - 1,
                ),
                rx.icon_button(
                    rx.icon("trash-2", size=16),
                    size="1",
                    variant="ghost",
                    color_scheme="red",
                    on_click=lambda: FrameworkState.remove_metric(metric["name"]),
                ),
                spacing="1",
            ),
            align="center",
            width="100%",
            spacing="3",
        ),
        size="1",
        width="100%",
    )


def add_metric_selector():
    """Dialog for adding a new metric"""

    def get_metrics_for_category(category: str) -> List[str]:
        """Helper to get metrics based on category"""
        category_mapping = {
            "Per Share Value": FrameworkState.per_share_metrics,
            "Growth Rate": FrameworkState.growth_rate_metrics,
            "Profitability": FrameworkState.profitability_metrics,
            "Valuation": FrameworkState.valuation_metrics,
            "Leverage & Liquidity": FrameworkState.leverage_liquidity_metrics,
            "Efficiency": FrameworkState.efficiency_metrics,
        }
        return category_mapping.get(category, [])

    return rx.cond(
        FrameworkState.show_add_metric_dialog,
        rx.dialog.root(
            rx.dialog.trigger(rx.button("hidden", style={"display": "none"})),
            rx.dialog.content(
                rx.vstack(
                    rx.heading("Add Metric", size="5"),
                    rx.vstack(
                        rx.text("Category", size="3", weight="medium"),
                        rx.select(
                            FrameworkState.available_categories,
                            value=FrameworkState.new_metric_category,
                            on_change=FrameworkState.set_new_metric_category,
                            size="3",
                            width="100%",
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Select Metric", size="3", weight="medium"),
                        rx.select(
                            rx.match(
                                FrameworkState.new_metric_category,
                                ("Per Share Value", FrameworkState.per_share_metrics),
                                ("Growth Rate", FrameworkState.growth_rate_metrics),
                                ("Profitability", FrameworkState.profitability_metrics),
                                ("Valuation", FrameworkState.valuation_metrics),
                                (
                                    "Leverage & Liquidity",
                                    FrameworkState.leverage_liquidity_metrics,
                                ),
                                ("Efficiency", FrameworkState.efficiency_metrics),
                                FrameworkState.per_share_metrics,  # default
                            ),
                            placeholder="Choose a metric...",
                            value=FrameworkState.new_metric_name,
                            on_change=FrameworkState.set_new_metric_name,
                            size="3",
                            width="100%",
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.hstack(
                        rx.spacer(),
                        rx.button(
                            "Cancel",
                            on_click=FrameworkState.close_add_metric_dialog,
                            variant="soft",
                            color_scheme="gray",
                            size="2",
                        ),
                        rx.button(
                            "Add Metric",
                            on_click=FrameworkState.add_metric_to_form,
                            size="2",
                            disabled=FrameworkState.new_metric_name == "",
                        ),
                        spacing="2",
                        width="100%",
                        justify="end",
                    ),
                    spacing="4",
                    width="100%",
                ),
                style={
                    "width": "400px",
                    "padding": "1.5rem",
                },
            ),
            open=True,
            on_open_change=FrameworkState.handle_add_metric_dialog_open,
        ),
        None,
    )


def metrics_management_panel():
    """Panel for managing framework metrics"""
    return rx.vstack(
        rx.hstack(
            rx.text("Metrics", size="4", weight="medium"),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=16),
                "Add Metric",
                on_click=FrameworkState.open_add_metric_dialog,
                size="2",
                variant="soft",
            ),
            width="100%",
            align="center",
        ),
        rx.cond(
            FrameworkState.form_metrics,
            rx.scroll_area(
                rx.vstack(
                    rx.foreach(
                        FrameworkState.form_metrics,
                        lambda metric, idx: metric_item(metric, idx),
                    ),
                    spacing="2",
                    width="100%",
                ),
                style={
                    "height": "300px",
                    "width": "100%",
                },
                scrollbars="vertical",
            ),
            rx.center(
                rx.text(
                    "No metrics added yet. Click 'Add Metric' to get started.",
                    size="2",
                    color="gray",
                ),
                padding="2rem",
            ),
        ),
        spacing="3",
        width="100%",
        height="100%",
    )


def add_framework_dialog():
    return rx.cond(
        FrameworkState.show_add_dialog,
        rx.dialog.root(
            rx.dialog.trigger(rx.button("hidden", style={"display": "none"})),
            rx.dialog.content(
                rx.vstack(
                    rx.hstack(
                        rx.spacer(),
                        rx.dialog.close(
                            rx.icon(
                                "x",
                                size=24,
                                on_click=FrameworkState.close_add_dialog,
                                style={
                                    "cursor": "pointer",
                                    "color": rx.color("accent", 10),
                                    "_hover": {"color": rx.color("accent", 7)},
                                },
                            ),
                        ),
                        width="100%",
                        align="center",
                        padding_bottom="0.5em",
                    ),
                    rx.hstack(
                        rx.vstack(
                            rx.hstack(
                                rx.vstack(
                                    rx.text("Title *", size="4", weight="medium"),
                                    rx.input(
                                        placeholder="Framework title",
                                        value=FrameworkState.form_title,
                                        on_change=FrameworkState.set_form_title,
                                        width="100%",
                                        size="3",
                                    ),
                                    spacing="2",
                                    width="66%",
                                ),
                                rx.vstack(
                                    rx.text("Author *", size="4", weight="medium"),
                                    rx.input(
                                        placeholder="Author name",
                                        value=FrameworkState.form_author,
                                        on_change=FrameworkState.set_form_author,
                                        width="100%",
                                        size="3",
                                    ),
                                    spacing="2",
                                    width="33%",
                                ),
                                width="100%",
                            ),
                            rx.hstack(
                                rx.vstack(
                                    rx.text("Industry *", size="4", weight="medium"),
                                    rx.select(
                                        ["general", "bank", "financial_services"],
                                        value=FrameworkState.form_industry,
                                        on_change=FrameworkState.set_form_industry,
                                        width="100%",
                                        size="3",
                                    ),
                                    spacing="2",
                                    width="20%",
                                ),
                                rx.vstack(
                                    rx.text("Scope *", size="4", weight="medium"),
                                    rx.select(
                                        ["fundamental", "technical"],
                                        value=FrameworkState.form_scope,
                                        on_change=FrameworkState.set_form_scope,
                                        width="100%",
                                        size="3",
                                    ),
                                    spacing="2",
                                    width="40%",
                                ),
                                rx.vstack(
                                    rx.text("Complexity *", size="4", weight="medium"),
                                    rx.select(
                                        ["beginner-friendly", "complex"],
                                        value=FrameworkState.form_complexity,
                                        on_change=FrameworkState.set_form_complexity,
                                        width="100%",
                                        size="3",
                                    ),
                                    spacing="2",
                                    width="40%",
                                ),
                                spacing="4",
                                width="100%",
                            ),
                            rx.vstack(
                                rx.text("Description", size="4", weight="medium"),
                                rx.text_area(
                                    placeholder="Framework description...",
                                    value=FrameworkState.form_description,
                                    on_change=FrameworkState.set_form_description,
                                    width="100%",
                                    height="100%",
                                    size="3",
                                    min_height="9em",
                                ),
                                spacing="2",
                                width="100%",
                                height="100%",
                                flex="1",
                            ),
                            spacing="3",
                            width="100%",
                            height="100%",
                            flex="2",
                        ),
                        rx.vstack(
                            metrics_management_panel(),
                            spacing="2",
                            width="100%",
                            height="100%",
                            flex="1",
                        ),
                        spacing="5",
                        width="100%",
                        align="start",
                        height="100%",
                    ),
                    rx.spacer(),
                    rx.hstack(
                        rx.spacer(),
                        rx.button(
                            "Cancel",
                            on_click=FrameworkState.close_add_dialog,
                            variant="soft",
                            color_scheme="gray",
                            size="3",
                        ),
                        rx.button(
                            "Add Framework",
                            on_click=FrameworkState.submit_framework,
                            size="3",
                            disabled=rx.cond(
                                (FrameworkState.form_title == "")
                                | (FrameworkState.form_author == ""),
                                True,
                                False,
                            ),
                        ),
                        spacing="2",
                        width="100%",
                        justify="end",
                    ),
                    spacing="0",
                    width="100%",
                    height="100%",
                    justify="between",
                ),
                style={
                    "width": "75vw",
                    "height": "75vh",
                    "maxWidth": "1800px",
                    "maxHeight": "none",
                    "padding": "1.5rem 2rem 2rem 2rem",
                    "overflow": "visible",
                },
            ),
            open=True,
            on_open_change=FrameworkState.handle_add_dialog_open,
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
        padding="0.75em",
        min_width="15em",
    )


def frameworks_content():
    return rx.fragment(
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.text("Frameworks", size="4"),
                    rx.spacer(),
                    rx.button(
                        rx.icon("plus", size=18),
                        "Add Framework",
                        on_click=FrameworkState.open_add_dialog,
                        size="2",
                        variant="soft",
                    ),
                    width="100%",
                    align="center",
                ),
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
            padding="0.75em",
        ),
        framework_dialog(),
        add_framework_dialog(),
        add_metric_selector(),
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
