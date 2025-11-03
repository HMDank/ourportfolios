import reflex as rx

from ..components.navbar import navbar
from ..components.cards import portfolio_card, stats_card
from ..components.graph import mini_price_graph
from ..components.loading import loading_screen

cards = [
    {
        "title": "Data-Driven Recommendations",
        "icon": "trending_up",
        "details": "Leverage AI-powered insights to discover promising investment opportunities.",
        "link": "/recommend",
    },
    {
        "title": "Find Your Investments",
        "icon": "filter",
        "details": "Leverage powerful filtering and screening tools to instantly discover the promising companies.",
        "link": "/select",
    },
    {
        "title": "In-Depth Stock Analysis",
        "icon": "brain-circuit",
        "details": "Access comprehensive financial data, charts, and key metrics for any stock.",
        "link": "/analyze",
    },
    {
        "title": "Portfolio Simulation",
        "icon": "chart-no-axes-combined",
        "details": "Test your investment strategies with our powerful backtesting and simulation tools.",
        "link": "/simulate",
    },
]

framework_description = [
    {
        "complexity": "Beginner",
        "name": "Benjamin Graham",
        "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
        "link": "/recommend",
    },
    {
        "complexity": "Intermediate",
        "name": "Peter Lynch",
        "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
        "link": "/recommend",
    },
    {
        "complexity": "Intermediate",
        "name": "Joel Greenblatt",
        "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
        "link": "/recommend",
    },
    {
        "complexity": "Advanced",
        "name": "Customize your own",
        "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
        "link": "/recommend",
    },
]

how_it_works_cards = [
    {
        "title": "1. Choose Your Framework",
        "icon": "brain-circuit",
        "details": "Select a strategy inspired by a legendary investor or customize your own unique analytical model.",
        "link": "/select",
    },
    {
        "title": "2. Discover & Analyze",
        "icon": "search",
        "details": "Use our powerful screening tools to find companies that match your chosen strategy and dive deep into financial data.",
        "link": "/analyze",
    },
    {
        "title": "3. Simulate & Build",
        "icon": "chart-no-axes-combined",
        "details": "Backtest your ideas and construct your portfolio with confidence using our simulation tools.",
        "link": "/simulate",
    },
]


class State(rx.State):
    show_cards: bool = False
    data: list[dict] = []


def hero_section(*args, **kwargs) -> rx.Component:
    return (
        rx.vstack(
            rx.center(
                rx.vstack(
                    rx.heading(
                        "Invest Like the Legends", font_size="5em", weight="medium"
                    ),
                    rx.text(
                        "Unlock the strategies of the world’s most successful investors with a platform that transforms theory into practical insight. Analyze portfolios, trade patterns, and decision models inspired by legendary investors, and learn to invest with the precision and confidence of the market’s best.",
                        text_align="center",
                        color_scheme="gray",
                        size="5",
                        marginTop="1.5em",
                        width="60%",
                    ),
                    rx.hstack(
                        rx.button(
                            "Get Started",
                            size="3",
                            font_size="1em",
                            radius="medium",
                        ),
                        rx.button(
                            rx.hstack(
                                rx.text("Contact us"),
                                rx.icon("move-right", size=15),
                                align="center",
                            ),
                            size="3",
                            font_size="1em",
                            radius="medium",
                            variant="outline",
                        ),
                        padding="1.5em",
                        spacing="4",
                        align="center",
                    ),
                    spacing="4",
                    align="center",
                ),
                height=kwargs.get("height", "auto"),
                justify="center",
                align="baseline",
            ),
            spacing="0",
            align="center",
            width="100%",
        ),
    )


def page_navigation(*args, **kwargs) -> rx.Component:
    return (
        rx.vstack(
            # title
            rx.heading(
                "Explore more",
                size="9",
                text_align="center",
                margin_bottom="0.8em",
            ),
            # Description
            rx.text(
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
                size="4",
                text_align="center",
                color_scheme="gray",
                margin_bottom="3em",
            ),
            # Scroller
            rx.box(
                *[
                    portfolio_card(card, idx, len(cards))
                    for idx, card in enumerate(cards)
                ],
                width="100%",
                height="60vh",
                min_height="40vh",
                position="relative",
                overflow="visible",
                padding_x="7vw",
            ),
            align="center",
            width="100%",
            height=kwargs.get("height", "auto"),
            justify="center",
            marginTop="4em",
        ),
    )


def problem_section(*args, **kwargs) -> rx.Component:
    return (
        rx.vstack(
            rx.heading(
                "Feeling Lost in a Sea of Data?",
                size="8",
                text_align="center",
                margin_bottom="0.5em",
            ),
            rx.text(
                "The path to successful investing is often confusing. You want to invest like the pros, but you're faced with...",
                size="5",
                text_align="center",
                color_scheme="gray",
                max_width="50vw",
            ),
            rx.grid(
                rx.vstack(
                    rx.icon("line-chart", size=40, color_scheme="red"),
                    rx.text(
                        "Overwhelming charts and metrics with no clear direction.",
                        text_align="center",
                    ),
                    spacing="3",
                    align="center",
                    padding="2em",
                ),
                rx.vstack(
                    rx.icon("book-x", size=40, color_scheme="red"),
                    rx.text(
                        "Complex strategies from books that are hard to apply in the real world.",
                        text_align="center",
                    ),
                    spacing="3",
                    align="center",
                    padding="2em",
                ),
                rx.vstack(
                    rx.icon("target", size=40, color_scheme="red"),
                    rx.text(
                        "Uncertainty about where to start or how to build a confident thesis.",
                        text_align="center",
                    ),
                    spacing="3",
                    align="center",
                    padding="2em",
                ),
                columns="3",
                spacing="5",
                width="100%",
                margin_top="3em",
            ),
            align="center",
            spacing="4",
            height=kwargs.get("height", "auto"),
            width="100%",
        ),
    )


def solution_section(*args, **kwargs) -> rx.Component:
    """Introduces OurPortfolios as the answer"""
    return rx.flex(
        rx.vstack(
            rx.heading(
                "A Guided Framework",
                color_scheme="violet",
                font_size="3.7em",
                weight="bold",
                height="50%",
            ),
            rx.text(
                """OurPortfolios bridges the gap between theory and action. We provide a clear analysis roadmap for all levels that translates legendary strategies into actionable steps. Build both your knowledge and your portfolio on one intuitive platform.""",
                weight="light",
                font_size="1.5em",
                paddingRight="0.5em",
            ),
            rx.hstack(
                rx.text(
                    "Start by choosing your investment style",
                    font_size="1.1em",
                    weight="bold",
                    color_scheme="violet",
                ),
                rx.icon("move-right", size=30, color=rx.color("accent", 11)),
                align="center",
                width="100%",
            ),
            spacing="5",
            width="40%",
            marginBottom="2em",
        ),
        rx.grid(
            *[stats_card(**props) for props in framework_description],
            columns="2",
            spacing="5",
            width="60%",
        ),
        spacing="5",
        direction="row",
        width="100%",
        align="center",
        height=kwargs.get("height", "auto"),
        padding="5.5em",
    )


def how_it_works_section(*args, **kwargs) -> rx.Component:
    """Shows the platform's flow"""
    return rx.vstack(
        rx.heading(
            "Your Path to Confident Investing",
            size="9",
            text_align="center",
            marginBottom="0.5em",
        ),
        rx.text(
            "We provide a simple, three-step process to turn legendary theory into your reality.",
            size="5",
            text_align="center",
            color_scheme="gray",
            marginBottom="3em",
        ),
        rx.grid(
            *[
                portfolio_card(card, idx, len(cards))
                for idx, card in enumerate(how_it_works_cards)
            ],
            columns="3",
            spacing="5",
            width="100%",
        ),
        align="center",
        width="100%",
        height="auto",
        justify="center",
    )


@rx.page(route="/")
def index() -> rx.Component:
    layout = {
        "height": "calc(100vh - 64px)",
    }
    return rx.fragment(
        loading_screen(),
        navbar(
            rx.foreach(
                State.data,
                lambda data: mini_price_graph(
                    label=data["label"],
                    data=data["data"],
                    diff=data["percent_diff"],
                ),
            ),
        ),
        # Hero section
        hero_section(**layout),
        # Problem
        problem_section(),
        # Solution
        solution_section(**layout),
        # Explore more
        page_navigation(),
    )
