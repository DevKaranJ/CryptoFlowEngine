"""
Market data handler for processing and normalizing exchange data.

This module handles incoming market data from WebSocket streams,
normalizes it, and provides interfaces for the orderflow engine.
"""

import asyncio
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

import numpy as np

from config import get_settings
from core.logging_config import get_logger

logger = get_logger("market_data")


@dataclass
class Trade:
    """Represents a single trade."""

    symbol: str
    price: float
    quantity: float
    side: str  # "buy" or "sell"
    timestamp: int
    trade_id: int

    @property
    def notional(self) -> float:
        """Trade notional value (price * quantity)."""
        return self.price * self.quantity


@dataclass
class Ticker:
    """Represents ticker data."""

    symbol: str
    last_price: float
    price_change: float
    price_change_percent: float
    high_price: float
    low_price: float
    volume: float
    quote_volume: float
    timestamp: int


@dataclass
class Candle:
    """Represents a candlestick (OHLCV)."""

    symbol: str
    interval: str
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int
    is_closed: bool

    @property
    def body(self) -> float:
        """Candle body size."""
        return abs(self.close - self.open)

    @property
    def upper_wick(self) -> float:
        """Upper wick size."""
        return self.high - max(self.open, self.close)

    @property
    def lower_wick(self) -> float:
        """Lower wick size."""
        return min(self.open, self.close) - self.low

    @property
    def is_bullish(self) -> bool:
        """Whether candle is bullish."""
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        """Whether candle is bearish."""
        return self.close < self.open


@dataclass
class OrderbookLevel:
    """Represents a single orderbook level."""

    price: float
    quantity: float


@dataclass
class Orderbook:
    """Represents the orderbook state."""

    symbol: str
    bids: list[OrderbookLevel]  # Sorted by price descending
    asks: list[OrderbookLevel]  # Sorted by price ascending
    timestamp: int
    last_update_id: int

    @property
    def spread(self) -> float:
        """Bid-ask spread."""
        if not self.bids or not self.asks:
            return 0.0
        return self.asks[0].price - self.bids[0].price

    @property
    def mid_price(self) -> float:
        """Mid price."""
        if not self.bids or not self.asks:
            return 0.0
        return (self.asks[0].price + self.bids[0].price) / 2

    def get_bid_ask_volumes(self, levels: int = 5) -> tuple[float, float]:
        """
        Get cumulative bid and ask volumes for top N levels.

        Args:
            levels: Number of levels to consider.

        Returns:
            Tuple of (bid_volume, ask_volume).
        """
        bid_vol = sum(level.quantity for level in self.bids[:levels])
        ask_vol = sum(level.quantity for level in self.asks[:levels])
        return bid_vol, ask_vol


class MarketDataHandler:
    """
    Handles market data processing and normalization.

    Manages multiple data streams and provides aggregated views
    for the orderflow and strategy engines.
    """

    def __init__(self) -> None:
        """Initialize the market data handler."""
        self.settings = get_settings()
        self._trades: dict[str, deque] = {}  # symbol -> deque of recent trades
        self._tickers: dict[str, Ticker] = {}  # symbol -> latest ticker
        self._candles: dict[str, dict[str, deque]] = {}  # symbol -> interval -> deque of candles
        self._orderbooks: dict[str, Orderbook] = {}  # symbol -> latest orderbook
        self._callbacks: list[Callable] = []

        # Configure buffer sizes
        self._max_trades_buffer = 1000
        self._max_candles_buffer = 500

    def register_callback(self, callback: Callable) -> None:
        """
        Register a callback for market data updates.

        Args:
            callback: Async function to call on updates.
        """
        self._callbacks.append(callback)

    async def handle_trade(self, trade_data: dict[str, Any]) -> None:
        """
        Handle incoming trade data.

        Args:
            trade_data: Raw trade data from WebSocket.
        """
        trade = Trade(
            symbol=trade_data["symbol"],
            price=trade_data["price"],
            quantity=trade_data["quantity"],
            side=trade_data["side"],
            timestamp=trade_data["timestamp"],
            trade_id=trade_data.get("trade_id", 0),
        )

        # Initialize buffer for symbol if needed
        if trade.symbol not in self._trades:
            self._trades[trade.symbol] = deque(maxlen=self._max_trades_buffer)
        else:
            # Remove old trades (older than 5 minutes)
            cutoff_time = trade.timestamp - (5 * 60 * 1000)
            while self._trades[trade.symbol] and self._trades[trade.symbol][0].timestamp < cutoff_time:
                self._trades[trade.symbol].popleft()

        self._trades[trade.symbol].append(trade)

        # Notify callbacks
        for callback in self._callbacks:
            await callback("trade", trade)

    async def handle_ticker(self, ticker_data: dict[str, Any]) -> None:
        """
        Handle incoming ticker data.

        Args:
            ticker_data: Raw ticker data from WebSocket.
        """
        ticker = Ticker(
            symbol=ticker_data["symbol"],
            last_price=ticker_data["last_price"],
            price_change=ticker_data["price_change"],
            price_change_percent=ticker_data["price_change_percent"],
            high_price=ticker_data["high_price"],
            low_price=ticker_data["low_price"],
            volume=ticker_data["volume"],
            quote_volume=ticker_data["quote_volume"],
            timestamp=ticker_data.get("timestamp", 0),
        )

        self._tickers[ticker.symbol] = ticker

        # Notify callbacks
        for callback in self._callbacks:
            await callback("ticker", ticker)

    async def handle_kline(self, kline_data: dict[str, Any]) -> None:
        """
        Handle incoming kline (candle) data.

        Args:
            kline_data: Raw kline data from WebSocket.
        """
        candle = Candle(
            symbol=kline_data["symbol"],
            interval=kline_data["interval"],
            open_time=kline_data["open_time"],
            open=kline_data["open"],
            high=kline_data["high"],
            low=kline_data["low"],
            close=kline_data["close"],
            volume=kline_data["volume"],
            close_time=kline_data["close_time"],
            is_closed=kline_data.get("is_closed", False),
        )

        # Initialize buffers for symbol and interval if needed
        if candle.symbol not in self._candles:
            self._candles[candle.symbol] = {}
        if candle.interval not in self._candles[candle.symbol]:
            self._candles[candle.symbol][candle.interval] = deque(maxlen=self._max_candles_buffer)

        candles = self._candles[candle.symbol][candle.interval]

        # Update existing candle or add new one
        if candles and candles[-1].open_time == candle.open_time:
            candles[-1] = candle
        else:
            candles.append(candle)

        # Notify callbacks
        for callback in self._callbacks:
            await callback("kline", candle)

    def get_recent_trades(self, symbol: str, count: int = 100) -> list[Trade]:
        """
        Get recent trades for a symbol.

        Args:
            symbol: Trading symbol.
            count: Number of recent trades to return.

        Returns:
            List of recent trades.
        """
        if symbol not in self._trades:
            return []
        trades = list(self._trades[symbol])
        return trades[-count:]

    def get_trade_summary(self, symbol: str, lookback_ms: int = 60000) -> dict[str, Any]:
        """
        Get a summary of recent trades.

        Args:
            symbol: Trading symbol.
            lookback_ms: Lookback period in milliseconds (default 1 minute).

        Returns:
            Dictionary with trade summary statistics.
        """
        if symbol not in self._trades:
            return {
                "buy_volume": 0.0,
                "sell_volume": 0.0,
                "buy_count": 0,
                "sell_count": 0,
                "total_volume": 0.0,
                "total_notional": 0.0,
            }

        cutoff_time = (datetime.now().timestamp() * 1000) - lookback_ms
        recent_trades = [t for t in self._trades[symbol] if t.timestamp > cutoff_time]

        buy_trades = [t for t in recent_trades if t.side == "buy"]
        sell_trades = [t for t in recent_trades if t.side == "sell"]

        return {
            "buy_volume": sum(t.quantity for t in buy_trades),
            "sell_volume": sum(t.quantity for t in sell_trades),
            "buy_count": len(buy_trades),
            "sell_count": len(sell_trades),
            "total_volume": sum(t.quantity for t in recent_trades),
            "total_notional": sum(t.notional for t in recent_trades),
            "trade_count": len(recent_trades),
        }

    def get_ticker(self, symbol: str) -> Ticker | None:
        """
        Get the latest ticker for a symbol.

        Args:
            symbol: Trading symbol.

        Returns:
            Latest ticker or None if not available.
        """
        return self._tickers.get(symbol)

    def get_candles(self, symbol: str, interval: str, count: int = 100) -> list[Candle]:
        """
        Get candles for a symbol and interval.

        Args:
            symbol: Trading symbol.
            interval: Candle interval (e.g., "1m", "5m", "15m").
            count: Number of candles to return.

        Returns:
            List of candles.
        """
        if symbol not in self._candles or interval not in self._candles[symbol]:
            return []
        candles = list(self._candles[symbol][interval])
        return candles[-count:]

    def get_latest_candle(self, symbol: str, interval: str) -> Candle | None:
        """
        Get the latest candle for a symbol and interval.

        Args:
            symbol: Trading symbol.
            interval: Candle interval.

        Returns:
            Latest candle or None if not available.
        """
        candles = self.get_candles(symbol, interval, 1)
        return candles[0] if candles else None

    def get_closed_candles(self, symbol: str, interval: str, count: int = 100) -> list[Candle]:
        """
        Get closed candles for a symbol and interval.

        Args:
            symbol: Trading symbol.
            interval: Candle interval.
            count: Number of closed candles to return.

        Returns:
            List of closed candles.
        """
        candles = self.get_candles(symbol, interval, count)
        return [c for c in candles if c.is_closed]

    def calculate_vwap(self, symbol: str, interval: str = "1m", periods: int = 20) -> float | None:
        """
        Calculate Volume Weighted Average Price.

        Args:
            symbol: Trading symbol.
            interval: Candle interval.
            periods: Number of periods for VWAP calculation.

        Returns:
            VWAP value or None if not enough data.
        """
        candles = self.get_candles(symbol, interval, periods)
        if len(candles) < periods:
            return None

        total_pv = sum(c.close * c.volume for c in candles)
        total_vol = sum(c.volume for c in candles)

        if total_vol == 0:
            return None

        return total_pv / total_vol

    def calculate_volume_profile(self, symbol: str, interval: str = "1m", bins: int = 20) -> dict[float, float]:
        """
        Calculate volume profile (volume at price levels).

        Args:
            symbol: Trading symbol.
            interval: Candle interval.
            bins: Number of price bins.

        Returns:
            Dictionary mapping price levels to volume.
        """
        candles = self.get_candles(symbol, interval, 100)
        if not candles:
            return {}

        # Create price bins
        prices = [(c.high + c.low) / 2 for c in candles]
        min_price = min(prices)
        max_price = max(prices)

        if min_price == max_price:
            return {min_price: sum(c.volume for c in candles)}

        bin_size = (max_price - min_price) / bins
        profile: dict[float, float] = {}

        for candle in candles:
            # Distribute volume across the price range
            start_bin = int((candle.low - min_price) / bin_size)
            end_bin = int((candle.high - min_price) / bin_size)

            for b in range(start_bin, min(end_bin + 1, bins)):
                price_level = min_price + (b + 0.5) * bin_size
                profile[price_level] = profile.get(price_level, 0) + candle.volume / max(1, end_bin - start_bin + 1)

        return profile


class DataAggregator:
    """
    Aggregates market data for orderflow calculations.

    Provides higher-level data transformations needed
    by the orderflow and strategy engines.
    """

    def __init__(self, market_data_handler: MarketDataHandler) -> None:
        """
        Initialize the data aggregator.

        Args:
            market_data_handler: The market data handler instance.
        """
        self.handler = market_data_handler

    def aggregate_trades_by_candle(
        self, symbol: str, interval: str = "1m"
    ) -> list[dict[str, Any]]:
        """
        Aggregate trades into candle-compatible format.

        Args:
            symbol: Trading symbol.
            interval: Aggregation interval.

        Returns:
            List of aggregated trade data per candle period.
        """
        trades = self.handler.get_recent_trades(symbol, 500)
        if not trades:
            return []

        # Group trades by minute
        trade_groups: dict[int, list[Trade]] = {}
        for trade in trades:
            minute_key = trade.timestamp // 60000  # 1 minute intervals
            if minute_key not in trade_groups:
                trade_groups[minute_key] = []
            trade_groups[minute_key].append(trade)

        # Aggregate each group
        result = []
        for minute_key, group_trades in sorted(trade_groups.items()):
            buy_vol = sum(t.quantity for t in group_trades if t.side == "buy")
            sell_vol = sum(t.quantity for t in group_trades if t.side == "sell")
            total_vol = sum(t.quantity for t in group_trades)

            result.append({
                "timestamp": minute_key * 60000,
                "buy_volume": buy_vol,
                "sell_volume": sell_vol,
                "total_volume": total_vol,
                "buy_ratio": buy_vol / total_vol if total_vol > 0 else 0.5,
                "trade_count": len(group_trades),
            })

        return result

    def calculate_delta_series(self, symbol: str, intervals: int = 50) -> list[float]:
        """
        Calculate delta values for recent periods.

        Args:
            symbol: Trading symbol.
            intervals: Number of intervals to calculate.

        Returns:
            List of delta values.
        """
        agg_data = self.aggregate_trades_by_candle(symbol)
        if not agg_data:
            return []

        deltas = [d["buy_volume"] - d["sell_volume"] for d in agg_data]
        return deltas[-intervals:]

    def calculate_cvd(self, symbol: str) -> float:
        """
        Calculate Cumulative Volume Delta.

        Args:
            symbol: Trading symbol.

        Returns:
            CVD value.
        """
        agg_data = self.aggregate_trades_by_candle(symbol)
        if not agg_data:
            return 0.0

        return sum(d["buy_volume"] - d["sell_volume"] for d in agg_data)

