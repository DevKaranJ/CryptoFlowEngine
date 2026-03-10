"""
Paper Trading module for the crypto trading bot.

This module provides paper trading functionality:
- Simulator: Virtual trade executor
- PnL Tracker: Profit and loss tracking
"""

from paper_trading.pnl_tracker import PnLTracker, PerformanceMetrics, RiskManager, TradeRecord
from paper_trading.simulator import PaperTradingSimulator, Position, SignalApprovalHandler, TradeResult

__all__ = [
    # Simulator
    "PaperTradingSimulator",
    "Position",
    "TradeResult",
    "SignalApprovalHandler",
    # PnL Tracker
    "PnLTracker",
    "TradeRecord",
    "PerformanceMetrics",
    "RiskManager",
]

