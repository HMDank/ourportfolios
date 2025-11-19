"""Page modules for the application."""

# Import all page modules to register them with Reflex
from . import landing
from . import analyze
from . import landing_ticker
from . import compare
from . import recommend
from . import select
from . import landing_industry

__all__ = [
    "landing",
    "analyze",
    "landing_ticker",
    "compare",
    "recommend",
    "select",
    "landing_industry",
]
