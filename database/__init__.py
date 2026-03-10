"""
Database module for the crypto trading bot.

This module provides database functionality:
- Models: SQLAlchemy ORM models
- Database Manager: Database operations and queries
"""

from database.db_manager import DatabaseManager
from database.models import (
    Base,
    MarketSnapshot,
    PaperTrade,
    Signal,
    SystemEvent,
    UserTrade,
)

__all__ = [
    # Models
    "Base",
    "Signal",
    "PaperTrade",
    "MarketSnapshot",
    "UserTrade",
    "SystemEvent",
    # Manager
    "DatabaseManager",
]

