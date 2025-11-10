"""Global framework state management for cross-page framework selection."""

import reflex as rx
from typing import Dict, List, Optional
import os
import psycopg2
from psycopg2.extras import RealDictCursor

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


class GlobalFrameworkState(rx.State):
    """Global state for managing selected investment framework across the application."""

    # Currently selected framework
    selected_framework_id: Optional[int] = None
    selected_framework: Dict = {}

    # Framework metrics mapping
    framework_metrics: Dict[str, List[str]] = {}

    @rx.event
    async def select_framework(self, framework_id: int):
        """Select a framework and load its associated metrics."""
        self.selected_framework_id = framework_id

        # Load framework details
        query = "SELECT * FROM frameworks.frameworks_df WHERE id = %s"
        framework_data = execute_query(query, (framework_id,))

        if framework_data:
            self.selected_framework = framework_data[0]
            await self.load_framework_metrics()

    async def load_framework_metrics(self):
        if not self.selected_framework_id:
            return

        query = """
            SELECT category, metrics, display_order
            FROM frameworks.framework_metrics_df
            WHERE framework_id = %s
            ORDER BY display_order
        """
        metrics_data = execute_query(query, (self.selected_framework_id,))

        # Aggregate metrics by category
        self.framework_metrics = {}
        for row in metrics_data:
            category = row["category"]
            metrics = row["metrics"]  # This is already an array from the DB

            # Initialize category if not exists
            if category not in self.framework_metrics:
                self.framework_metrics[category] = []

            # Metrics is an array, so extend our list with it
            if isinstance(metrics, list):
                self.framework_metrics[category].extend(metrics)
            else:
                # Fallback if it's a single value
                self.framework_metrics[category].append(metrics)

    @rx.var
    def has_selected_framework(self) -> bool:
        """Check if a framework is currently selected."""
        return self.selected_framework_id is not None

    @rx.var
    def framework_display_name(self) -> str:
        """Get display name of selected framework."""
        if self.selected_framework:
            return self.selected_framework.get("title", "Unknown Framework")
        return "No Framework Selected"

    @rx.event
    def clear_framework_selection(self):
        """Clear the current framework selection."""
        self.selected_framework_id = None
        self.selected_framework = {}
        self.framework_metrics = {}
