"""
Logging configuration for the crypto trading bot.

This module provides structured logging setup with file rotation
and console output.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any

from config import get_settings, PROJECT_ROOT


def setup_logging() -> logging.Logger:
    """
    Set up the logging system for the application.

    Creates log directories, configures handlers with rotation,
    and sets up the root logger.

    Returns:
        The configured root logger.
    """
    settings = get_settings()

    # Create log directory
    log_path = PROJECT_ROOT / settings.logging.file
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger("cryptobot")
    logger.setLevel(getattr(logging, settings.logging.level.upper()))

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(settings.logging.format)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_path),
        maxBytes=settings.logging.max_bytes,
        backupCount=settings.logging.backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(settings.logging.format)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: The name of the module (usually __name__).

    Returns:
        A logger instance for the given name.
    """
    return logging.getLogger(f"cryptobot.{name}")


class SignalLogger:
    """Specialized logger for trading signals."""

    def __init__(self) -> None:
        """Initialize the signal logger."""
        self.logger = logging.getLogger("cryptobot.signals")
        self._setup_signal_handler()

    def _setup_signal_handler(self) -> None:
        """Set up a dedicated handler for signal logging."""
        settings = get_settings()
        log_path = PROJECT_ROOT / "logs" / "signals.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        handler = logging.handlers.RotatingFileHandler(
            filename=str(log_path),
            maxBytes=settings.logging.max_bytes,
            backupCount=settings.logging.backup_count,
            encoding="utf-8"
        )
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s | SIGNAL | %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_signal(self, signal_data: dict[str, Any]) -> None:
        """
        Log a trading signal.

        Args:
            signal_data: Dictionary containing signal information.
        """
        self.logger.info(str(signal_data))

    def log_approval(self, signal_id: int, approved: bool, reason: str = "") -> None:
        """
        Log user approval decision.

        Args:
            signal_id: The ID of the signal.
            approved: Whether the signal was approved.
            reason: Optional reason for the decision.
        """
        status = "APPROVED" if approved else "REJECTED"
        self.logger.info(f"Signal {signal_id}: {status} - {reason}")


class TradeLogger:
    """Specialized logger for trade execution."""

    def __init__(self) -> None:
        """Initialize the trade logger."""
        self.logger = logging.getLogger("cryptobot.trades")
        self._setup_trade_handler()

    def _setup_trade_handler(self) -> None:
        """Set up a dedicated handler for trade logging."""
        log_path = PROJECT_ROOT / "logs" / "trades.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        handler = logging.handlers.RotatingFileHandler(
            filename=str(log_path),
            maxBytes=10485760,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s | TRADE | %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_paper_trade(self, trade_data: dict[str, Any]) -> None:
        """
        Log a paper trade.

        Args:
            trade_data: Dictionary containing trade information.
        """
        self.logger.info(str(trade_data))

    def log_pnl(self, trade_id: int, pnl: float, result: str) -> None:
        """
        Log PnL result.

        Args:
            trade_id: The ID of the trade.
            pnl: Profit or loss amount.
            result: Trade result (TP hit, SL hit, etc.)
        """
        self.logger.info(f"Trade {trade_id}: {result} - PnL: {pnl:.2f}")


# Global logger instances
_signal_logger: SignalLogger | None = None
_trade_logger: TradeLogger | None = None


def get_signal_logger() -> SignalLogger:
    """Get the global signal logger instance."""
    global _signal_logger
    if _signal_logger is None:
        _signal_logger = SignalLogger()
    return _signal_logger


def get_trade_logger() -> TradeLogger:
    """Get the global trade logger instance."""
    global _trade_logger
    if _trade_logger is None:
        _trade_logger = TradeLogger()
    return _trade_logger

