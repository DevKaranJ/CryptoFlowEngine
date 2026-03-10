"""
Dashboard module for the crypto trading bot.

This module provides the web dashboard:
- API Server: FastAPI server
- Routes: API endpoints
"""

from dashboard.api_server import create_app, set_dependencies, update_bot_state, _bot_state
from dashboard.routes import router

__all__ = [
    "create_app",
    "set_dependencies",
    "update_bot_state",
    "_bot_state",
    "router",
]

