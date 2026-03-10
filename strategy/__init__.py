"""
Strategy module for the crypto trading bot.

This module provides trading strategy components:
- Zone Detector: Support/resistance zones
- Initiation Detector: Initiation candle detection
- Pullback Detector: Pullback confirmation
- Signal Builder: Signal generation
- Orderflow Strategy: Complete strategy orchestration
"""

from strategy.initiation_detector import InitiationData, InitiationDetector
from strategy.pullback_detector import PullbackData, PullbackDetector
from strategy.signal_builder import (
    OrderflowStrategy,
    SignalBuilder,
    SignalDirection,
    SignalStatus,
    TradingSignal,
)
from strategy.zone_detector import Zone, ZoneDetector

__all__ = [
    # Zone Detector
    "Zone",
    "ZoneDetector",
    # Initiation Detector
    "InitiationData",
    "InitiationDetector",
    # Pullback Detector
    "PullbackData",
    "PullbackDetector",
    # Signal Builder
    "SignalDirection",
    "SignalStatus",
    "TradingSignal",
    "SignalBuilder",
    # Strategy
    "OrderflowStrategy",
]

