"""
Core module for the crypto trading bot.

This module provides the foundational components:
- WebSocket client for exchange connections
- Market data handler for data processing
- Logging configuration
"""

from core.logging_config import (
    get_logger,
    get_signal_logger,
    get_trade_logger,
    setup_logging,
)
from core.market_data_handler import (
    Candle,
    DataAggregator,
    MarketDataHandler,
    Orderbook,
    OrderbookLevel,
    Ticker,
    Trade,
)
from core.websocket_client import (
    BinanceWebSocketClient,
    BybitWebSocketClient,
    Exchange,
    StreamConfig,
    WebSocketClient,
    create_websocket_client,
)

__all__ = [
    # Logging
    "setup_logging",
    "get_logger",
    "get_signal_logger",
    "get_trade_logger",
    # Market Data
    "Trade",
    "Ticker",
    "Candle",
    "Orderbook",
    "OrderbookLevel",
    "MarketDataHandler",
    "DataAggregator",
    # WebSocket
    "Exchange",
    "StreamConfig",
    "WebSocketClient",
    "BinanceWebSocketClient",
    "BybitWebSocketClient",
    "create_websocket_client",
]

