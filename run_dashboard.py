"""
Dashboard runner script.

Starts only the dashboard API server without the trading bot.
Useful for viewing signals and trades without connecting to exchanges.
"""

import uvicorn

from config import get_settings
from core.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger("dashboard")

# Import after setup
from dashboard import create_app, set_dependencies, update_bot_state
from database import DatabaseManager
from paper_trading import PaperTradingSimulator, PnLTracker


def main() -> None:
    """Run the dashboard server."""
    settings = get_settings()

    logger.info("Initializing dashboard...")

    # Initialize dependencies
    db = DatabaseManager()
    simulator = PaperTradingSimulator(db)
    pnl_tracker = PnLTracker()

    set_dependencies(simulator, db, pnl_tracker)

    # Set bot state to running (paper trading mode)
    update_bot_state(
        running=True,
        connected=True,
        current_strategy="Paper Trading Mode",
        active_pairs=settings.exchange.symbols,
    )

    # Create app
    app = create_app()

    logger.info(f"Starting dashboard on {settings.dashboard.host}:{settings.dashboard.port}")

    # Run server
    uvicorn.run(
        app,
        host=settings.dashboard.host,
        port=settings.dashboard.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()

