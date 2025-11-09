"""
Gomu News Monitor Package
A production-grade news monitoring system for gomuhouchi.com

Modules:
    - config: Configuration management
    - database: SQLite database operations
    - auth: Authentication and session management
    - scraper: Web scraping and content extraction
    - notifier: Email and notification services
"""

__version__ = "1.0.0"
__author__ = "Gomu Monitor Team"

# Package-level imports for convenience
from .config import Config
from .database import Database
from .auth import Authenticator
from .scraper import NewsScraper
from .notifier import Notifier

__all__ = [
    "Config",
    "Database",
    "Authenticator",
    "NewsScraper",
    "Notifier"
]
