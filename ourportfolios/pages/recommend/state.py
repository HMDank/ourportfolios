"""State management for framework recommendation page."""

import reflex as rx
from typing import List, Dict, Any, cast
import os
import psycopg2
from psycopg2.extras import RealDictCursor

from ...state import GlobalFrameworkState

DATABASE_URI = os.getenv("DATABASE_URI")


def get_db_connection():
    try:
        if not DATABASE_URI:
            print("WARNING: DATABASE_URI environment variable is not set")
            return None
        return psycopg2.connect(DATABASE_URI, cursor_factory=RealDictCursor)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None


def execute_query(query: str, params: tuple | None = None) -> List[Dict]:
    try:
        conn = get_db_connection()
        if conn is None:
            print("WARNING: Cannot execute query - no database connection")
            return []

        with conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                if cur.description:
                    results = cur.fetchall()
                    return [dict(row) for row in results] if results else []
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
    form_metrics: List[Dict] = []

    # Available metrics by category
    available_categories: List[str] = [
        "Per Share Value",
        "Growth Rate",
        "Profitability",
        "Valuation",
        "Leverage & Liquidity",
        "Efficiency",
    ]

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

        if any(m["name"] == self.new_metric_name for m in self.form_metrics):
            return

        next_order = len(self.form_metrics)
        self.form_metrics.append(
            {
                "name": self.new_metric_name,
                "category": self.new_metric_category,
                "enabled": True,
                "order": next_order,
            }
        )

        self.new_metric_name = ""
        self.show_add_metric_dialog = False

    @rx.event
    def remove_metric(self, metric_name: str):
        """Remove a metric from the list"""
        self.form_metrics = [m for m in self.form_metrics if m["name"] != metric_name]
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

    @rx.event
    async def on_load(self):
        await self.load_scopes()
        if self.scopes:
            await self.change_scope(self.scopes[0]["value"])

    async def load_scopes(self):
        self.loading_scopes = True
        try:
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

    @rx.event
    async def change_scope(self, scope: str):
        self.active_scope = scope
        await self.load_frameworks()

    async def load_frameworks(self):
        self.loading_frameworks = True
        try:
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
        self.form_metrics = []
        self.show_add_dialog = True

    @rx.event
    def close_add_dialog(self):
        self.show_add_dialog = False

    @rx.event
    def handle_add_dialog_open(self, value: bool):
        if not value:
            self.close_add_dialog()

    @rx.event
    async def submit_framework(self):
        if not self.form_title or not self.form_author:
            return

        try:
            framework_query = """
                INSERT INTO frameworks.frameworks_df 
                (title, description, author, complexity, scope, industry, source_name, source_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """

            conn = get_db_connection()
            if conn is None:
                print("ERROR: Cannot submit framework - no database connection")
                return

            with conn:
                with conn.cursor() as cur:
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
                                    metric["category"],
                                    metric["name"],
                                    metric["order"],
                                ),
                            )

                    conn.commit()

            self.close_add_dialog()
            await self.load_frameworks()
        except Exception as e:
            print(f"Error adding framework: {e}")

    @rx.event
    async def select_and_navigate_framework(self):
        """Select the current framework and navigate to ticker selection."""
        if not self.selected_framework:
            print("Error: No framework selected")
            return

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

        self.close_dialog()

        global_state = await self.get_state(GlobalFrameworkState)
        await global_state.select_framework(framework_id)

        return rx.redirect("/select")
