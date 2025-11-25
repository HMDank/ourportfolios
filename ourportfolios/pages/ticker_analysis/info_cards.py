"""Information cards for the ticker landing page."""

import reflex as rx

from ...components.cards import card_wrapper
from ...components.drawer import CartState
from .state import State


def name_card():
    overview = State.overview
    return (
        card_wrapper(
            rx.vstack(
                rx.hstack(
                    rx.heading(overview["symbol"], size="9"),
                    rx.button(
                        rx.icon("plus", size=16),
                        size="2",
                        variant="soft",
                        on_click=lambda: CartState.add_item(overview["symbol"]),
                    ),
                    justify="center",
                    align="center",
                ),
                rx.hstack(
                    rx.badge(f"{overview['exchange']}", variant="surface"),
                    rx.badge(f"{overview['industry']}"),
                ),
            ),
            style={"width": "100%", "padding": "1em"},
        ),
    )


def general_info_card():
    overview = State.overview
    website = overview["website"]
    return rx.vstack(
        card_wrapper(
            rx.text(f"{overview['short_name']} (Est. {overview['established_year']})"),
            rx.link(website, href=f"https://{website}", is_external=True),
            rx.text(f"Market cap: {overview['market_cap']} B. VND"),
            rx.text(f"Issue Shares: {overview['issue_share']}"),
            rx.text(f"Outstanding Shares: {overview['outstanding_share']}"),
            rx.text(
                f"{overview['no_shareholders']} shareholders ({overview['foreign_percent']}% foreign)"
            ),
            style={"width": "100%", "padding": "1em"},
        ),
    )


def company_profile_card():
    profile_data = State.profile
    PROFILE_CONTENT_HEIGHT = "12em"

    def create_profile_tab_content(content_key: str, tab_value: str):
        return rx.tabs.content(
            rx.scroll_area(
                rx.text(
                    profile_data[content_key],
                    size="3",
                    weight="regular",
                    style={
                        "whiteSpace": "pre-wrap",
                        "wordWrap": "break-word",
                        "textAlign": "justify",
                        "lineHeight": "1.6",
                    },
                ),
                height=PROFILE_CONTENT_HEIGHT,
                padding="0.5em",
            ),
            value=tab_value,
            padding_top="0.8em",
        )

    return rx.card(
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger("Company Profile", value="profile"),
                rx.tabs.trigger("History", value="history"),
                rx.tabs.trigger("Promises", value="promises"),
                rx.tabs.trigger("Risks", value="risks"),
                rx.tabs.trigger("Developments", value="developments"),
                rx.tabs.trigger("Strategies", value="strategies"),
                variant="surface",
            ),
            create_profile_tab_content("company_profile", "profile"),
            create_profile_tab_content("history_dev", "history"),
            create_profile_tab_content("company_promise", "promises"),
            create_profile_tab_content("business_risk", "risks"),
            create_profile_tab_content("key_developments", "developments"),
            create_profile_tab_content("business_strategies", "strategies"),
            default_value="profile",
        ),
        width="100%",
        padding="1em",
    )
