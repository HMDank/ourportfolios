import reflex as rx
import time
import asyncio

from ..utils.generate_query import get_suggest_ticker, fetch_ticker
from typing import List, Dict, Any
from .graph import pct_change_badge
from ..utils.scheduler import db_settings


class SearchBarState(rx.State):
    search_query: str = ""
    display_suggestion: bool = False
    outstanding_tickers: Dict[str, Any] = {}
    ticker_list: List[Dict[str, Any]] = []

    @rx.event
    def set_query(self, text: str = ""):
        self.search_query = text if text != "" else text

    @rx.event
    def set_display_suggestions(self, state: bool):
        yield time.sleep(0.2)  # Delay the set action
        self.display_suggestion = state

    @rx.var
    def get_suggest_ticker(self) -> List[Dict[str, Any]]:
        """Recommends tickers on user's keystroke"""
        if not self.display_suggestion:
            return []
        if self.search_query == "":
            return self.ticker_list

        return get_suggest_ticker(search_query=self.search_query.upper(), return_type="df")

    @rx.event(background=True)
    async def load_state(self):
        """Preload tickers & assign top 3 tickers, called periodically with local_scheduler"""
        while True:
            async with self:
                # Preload all tickers
                self.ticker_list = fetch_ticker(match_query="all").to_dict("records")

                # Fetch and store the top 3 trending tickers in memory
                self.outstanding_tickers: Dict[str, Any] = {
                    item["symbol"]: 1 for item in self.ticker_list[:3]
                }

            await asyncio.sleep(db_settings.interval)


def search_bar():
    return rx.box(
        rx.vstack(
            rx.input(
                rx.input.slot(rx.icon(tag="search", size=16)),
                placeholder="Search for a ticker here!",
                type="search",
                size="2",
                value=SearchBarState.search_query,
                on_change=SearchBarState.set_query,
                on_blur=SearchBarState.set_display_suggestions(False),
                on_mount=SearchBarState.set_display_suggestions(False),
                on_focus=SearchBarState.set_display_suggestions(True),
                width="100%",
            ),
            rx.cond(
                SearchBarState.display_suggestion,
                # Scrollable suggestion dropdown
                rx.fragment(
                    rx.flex(
                        rx.scroll_area(
                            rx.foreach(
                                SearchBarState.get_suggest_ticker,
                                lambda ticker_value: suggestion_card(
                                    value=ticker_value
                                ),
                            ),
                            scrollbars="vertical",
                            type="scroll",
                        ),
                        width="100%",
                        max_height=250,
                        overflow_y="auto",
                        z_index="100",
                        background_color=rx.color("gray", 2),
                        position="absolute",
                        top="calc(100% + 5px)",
                        border_radius=4,
                        direction="column",
                    ),
                    as_child=True,
                ),
                rx.fragment(),
            ),
            position="relative",
            width="20vw",
            on_mount=SearchBarState.load_state,
        ),
    )


def suggestion_card(value: Dict[str, Any]) -> rx.Component:
    ticker = value["symbol"].to(str)
    industry = value["industry"].to(str)
    pct_price_change: float = value["pct_price_change"].to(float)

    return rx.box(
        rx.hstack(
            rx.vstack(
                # ticker tag
                rx.text(
                    ticker,
                    size="5",
                    weight="medium",
                ),
                # industry tag
                rx.badge(
                    industry,
                    size="2",
                    weight="regular",
                    variant="surface",
                    color_scheme="violet",
                    radius="medium",
                ),
                spacing="1",
            ),
            rx.spacer(),
            # pct badge
            rx.flex(
                rx.cond(
                    SearchBarState.outstanding_tickers.get(ticker, None),
                    rx.icon("flame", size=20, color=rx.color("tomato", 9)),
                    rx.fragment(),
                ),
                pct_change_badge(diff=pct_price_change),
                align="end",
                direction="column",
                spacing="3",
            ),
            align="center",
            spacing="1",
        ),
        on_click=[rx.redirect(f"/analyze/{ticker}"), SearchBarState.set_query("")],
        width="100%",
        padding="10px",
        cursor="pointer",
        _hover={"background_color": rx.color("gray", 3)},
    )
