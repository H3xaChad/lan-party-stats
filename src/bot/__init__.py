"""
LAN Party Stats Bot - Package initialization.
"""

from .bot import create_bot, run_bot
from .database import Database
from .tracker import ActivityTracker
from .stats import StatsManager

__version__ = "2.0.0"
__all__ = [
    "create_bot",
    "run_bot",
    "Database",
    "ActivityTracker",
    "StatsManager",
]
