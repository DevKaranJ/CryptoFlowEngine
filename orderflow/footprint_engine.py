"""
Footprint Engine - Simulates footprint charts from trade data.

This module processes trade data to create simulated footprint charts,
calculating buy/sell volume at each price level.
"""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

from config import get_settings
from core.logging_config import get_logger

logger = get_logger("orderflow.footprint")


@dataclass
class FootprintLevel:
    """Represents a single price level in the footprint."""

    price: float
    buy_volume: float = 0.0
    sell_volume: float = 0.0

    @property
    def total_volume(self) -> float:
        """Total volume at this price level."""
        return self.buy_volume + self.sell_volume

    @property
    def delta(self) -> float:
        """Delta (buy - sell) at this price level."""
        return self.buy_volume - self.sell_volume

    @property
    def imbalance_ratio(self) -> float:
        """Buy/sell ratio. Returns 1.0 if no volume."""
        if self.sell_volume == 0:
            return float("inf") if self.buy_volume > 0 else 1.0
        return self.buy_volume / self.sell_volume

    @property
    def is_buy_imbalance(self) -> bool:
        """Check if there's a buy imbalance (ratio >= threshold)."""
        settings = get_settings()
        return self.imbalance_ratio >= settings.orderflow.imbalance_threshold

    @property
    def is_sell_imbalance(self) -> bool:
        """Check if there's a sell imbalance (ratio <= 1/threshold)."""
        settings = get_settings()
        threshold = 1 / settings.orderflow.imbalance_threshold
        return self.imbalance_ratio <= threshold

    @property
    def buyer_aggression(self) -> float:
        """Percentage of volume that is buying."""
        if self.total_volume == 0:
            return 0.5
        return self.buy_volume / self.total_volume

    @property
    def seller_aggression(self) -> float:
        """Percentage of volume that is selling."""
        if self.total_volume == 0:
            return 0.5
        return self.sell_volume / self.total_volume


@dataclass
class FootprintBar:
    """Represents a footprint bar (simulated candle with footprint)."""

    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    levels: dict[float, FootprintLevel] = field(default_factory=dict)

    @property
    def total_buy_volume(self) -> float:
        """Total buy volume in the bar."""
        return sum(level.buy_volume for level in self.levels.values())

    @property
    def total_sell_volume(self) -> float:
        """Total sell volume in the bar."""
        return sum(level.sell_volume for level in self.levels.values())

    @property
    def delta(self) -> float:
        """Net delta (buy - sell) for the bar."""
        return self.total_buy_volume - self.total_sell_volume

    @property
    def buy_imbalance_count(self) -> int:
        """Number of levels with buy imbalance."""
        return sum(1 for level in self.levels.values() if level.is_buy_imbalance)

    @property
    def sell_imbalance_count(self) -> int:
        """Number of levels with sell imbalance."""
        return sum(1 for level in self.levels.values() if level.is_sell_imbalance)


class FootprintEngine:
    """
    Footprint Engine for real-time orderflow analysis.

    Processes incoming trades to build footprint charts and calculate
    orderflow metrics.
    """

    def __init__(self) -> None:
        """Initialize the footprint engine."""
        self.settings = get_settings()
        self._current_bar: FootprintBar | None = None
        self._bar_history: deque[FootprintBar] = deque(maxlen=500)
        self._price_precision: int = 2  # Default for BTC

    def set_price_precision(self, precision: int) -> None:
        """
        Set the price decimal precision.

        Args:
            precision: Number of decimal places.
        """
        self._price_precision = precision

    def _round_price(self, price: float) -> float:
        """Round price to the configured precision."""
        return round(price, self._price_precision)

    def process_trade(self, symbol: str, price: float, quantity: float, side: str, timestamp: int) -> None:
        """
        Process a single trade and update the current footprint bar.

        Args:
            symbol: Trading symbol (for future multi-symbol support).
            price: Trade price.
            quantity: Trade quantity.
            side: Trade side ("buy" or "sell").
            timestamp: Trade timestamp in milliseconds.
        """
        # Determine bar start time (1-minute bars)
        bar_start = (timestamp // 60000) * 60000

        # Initialize new bar if needed
        if self._current_bar is None or self._current_bar.timestamp != bar_start:
            self._finalize_bar()
            self._current_bar = FootprintBar(
                timestamp=bar_start,
                open=price,
                high=price,
                low=price,
                close=price,
                volume=0.0,
            )

        # Update current bar
        self._current_bar.volume += quantity
        self._current_bar.high = max(self._current_bar.high, price)
        self._current_bar.low = min(self._current_bar.low, price)
        self._current_bar.close = price

        # Update footprint level
        rounded_price = self._round_price(price)
        if rounded_price not in self._current_bar.levels:
            self._current_bar.levels[rounded_price] = FootprintLevel(price=rounded_price)

        level = self._current_bar.levels[rounded_price]
        if side == "buy":
            level.buy_volume += quantity
        else:
            level.sell_volume += quantity

    def _finalize_bar(self) -> None:
        """Finalize the current bar and add to history."""
        if self._current_bar is not None:
            self._bar_history.append(self._current_bar)
            logger.debug(
                f"Bar finalized: {self._current_bar.timestamp} - "
                f"Delta: {self._current_bar.delta:.4f}, "
                f"Buy Imb: {self._current_bar.buy_imbalance_count}, "
                f"Sell Imb: {self._current_bar.sell_imbalance_count}"
            )

    def update_from_trade_data(self, trade_data: dict[str, Any]) -> None:
        """
        Update footprint from trade data dictionary.

        Args:
            trade_data: Trade data with keys: symbol, price, quantity, side, timestamp.
        """
        self.process_trade(
            symbol=trade_data["symbol"],
            price=trade_data["price"],
            quantity=trade_data["quantity"],
            side=trade_data["side"],
            timestamp=trade_data["timestamp"],
        )

    def get_current_bar(self) -> FootprintBar | None:
        """
        Get the current (in-progress) footprint bar.

        Returns:
            Current footprint bar or None if no data.
        """
        return self._current_bar

    def get_closed_bars(self, count: int = 100) -> list[FootprintBar]:
        """
        Get closed footprint bars.

        Args:
            count: Number of bars to return.

        Returns:
            List of closed footprint bars.
        """
        return list(self._bar_history)[-count:]

    def get_latest_bars(self, count: int = 10) -> list[FootprintBar]:
        """
        Get the latest footprint bars (including current).

        Args:
            count: Number of bars to return.

        Returns:
            List of latest bars.
        """
        bars = list(self._bar_history)
        if self._current_bar:
            bars.append(self._current_bar)
        return bars[-count:]

    def get_levels_with_imbalance(self, bar: FootprintBar, side: str = "buy") -> list[FootprintLevel]:
        """
        Get price levels with significant imbalance.

        Args:
            bar: The footprint bar to analyze.
            side: "buy" or "sell" imbalance.

        Returns:
            List of levels with the specified imbalance.
        """
        if side == "buy":
            return [level for level in bar.levels.values() if level.is_buy_imbalance]
        else:
            return [level for level in bar.levels.values() if level.is_sell_imbalance]

    def detect_stacked_imbalance(self, bar: FootprintBar, side: str = "buy") -> bool:
        """
        Detect stacked imbalance (consecutive levels with same imbalance).

        Args:
            bar: The footprint bar to analyze.
            side: "buy" or "sell" imbalance.

        Returns:
            True if stacked imbalance detected.
        """
        if not bar.levels:
            return False

        # Sort prices
        sorted_prices = sorted(bar.levels.keys())
        threshold = self.settings.orderflow.stacked_imbalance_levels

        consecutive = 0
        max_consecutive = 0

        for price in sorted_prices:
            level = bar.levels[price]
            if side == "buy" and level.is_buy_imbalance:
                consecutive += 1
            elif side == "sell" and level.is_sell_imbalance:
                consecutive += 1
            else:
                max_consecutive = max(max_consecutive, consecutive)
                consecutive = 0

        max_consecutive = max(max_consecutive, consecutive)
        return max_consecutive >= threshold

    def get_absorption_levels(self, bar: FootprintBar) -> dict[str, list[FootprintLevel]]:
        """
        Detect absorption: high volume but price not moving significantly.

        Args:
            bar: The footprint bar to analyze.

        Returns:
            Dictionary with "buy_absorption" and "sell_absorption" lists.
        """
        result = {"buy_absorption": [], "sell_absorption": []}

        if not bar.levels:
            return result

        # Calculate average volume per level
        total_vol = sum(level.total_volume for level in bar.levels.values())
        avg_vol = total_vol / len(bar.levels) if bar.levels else 0

        # Find absorption levels: high volume but closed near level's price
        threshold = self.settings.orderflow.absorption_threshold

        for level in bar.levels.values():
            if level.total_volume > avg_vol * 2:
                # Check if price closed near this level with high sell but didn't drop much
                price_range = bar.high - bar.low
                if price_range > 0:
                    level_position = (level.price - bar.low) / price_range

                    # Buy absorption: high sell volume but price stayed high
                    if level.is_sell_imbalance and level_position > threshold:
                        result["buy_absorption"].append(level)

                    # Sell absorption: high buy volume but price stayed low
                    if level.is_buy_imbalance and level_position < (1 - threshold):
                        result["sell_absorption"].append(level)

        return result

    def get_market_profile(self, bar: FootprintBar) -> dict[str, Any]:
        """
        Get market profile statistics for a bar.

        Args:
            bar: The footprint bar to analyze.

        Returns:
            Dictionary with market profile data.
        """
        if not bar.levels:
            return {
                "value_area_high": 0.0,
                "value_area_low": 0.0,
                "poc": 0.0,
                "total_volume": 0.0,
                "buy_volume": 0.0,
                "sell_volume": 0.0,
            }

        # Calculate total volume
        total_volume = sum(level.total_volume for level in bar.levels.values())

        # Find POC (Point of Control - level with most volume)
        poc_price = max(bar.levels.keys(), key=lambda p: bar.levels[p].total_volume)
        poc_volume = bar.levels[poc_price].total_volume

        # Calculate Value Area (70% of volume)
        sorted_levels = sorted(
            bar.levels.items(),
            key=lambda x: x[1].total_volume,
            reverse=True
        )

        cumsum = 0
        value_area_threshold = total_volume * 0.7
        value_area_levels = []

        for price, level in sorted_levels:
            cumsum += level.total_volume
            value_area_levels.append(price)
            if cumsum >= value_area_threshold:
                break

        return {
            "value_area_high": max(value_area_levels) if value_area_levels else 0.0,
            "value_area_low": min(value_area_levels) if value_area_levels else 0.0,
            "poc": poc_price,
            "poc_volume": poc_volume,
            "total_volume": total_volume,
            "buy_volume": bar.total_buy_volume,
            "sell_volume": bar.total_sell_volume,
            "delta": bar.delta,
        }

    def reset(self) -> None:
        """Reset the footprint engine state."""
        self._current_bar = None
        self._bar_history.clear()
        logger.info("Footprint engine reset")


class MultiSymbolFootprintEngine:
    """
    Manages footprint engines for multiple symbols.
    """

    def __init__(self) -> None:
        """Initialize multi-symbol footprint engine."""
        self._engines: dict[str, FootprintEngine] = {}

    def get_engine(self, symbol: str) -> FootprintEngine:
        """
        Get or create a footprint engine for a symbol.

        Args:
            symbol: Trading symbol.

        Returns:
            FootprintEngine instance for the symbol.
        """
        if symbol not in self._engines:
            self._engines[symbol] = FootprintEngine()
        return self._engines[symbol]

    def process_trade(self, symbol: str, price: float, quantity: float, side: str, timestamp: int) -> None:
        """
        Process a trade for a specific symbol.

        Args:
            symbol: Trading symbol.
            price: Trade price.
            quantity: Trade quantity.
            side: Trade side.
            timestamp: Trade timestamp.
        """
        self.get_engine(symbol).process_trade(symbol, price, quantity, side, timestamp)

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """
        Get footprint statistics for all symbols.

        Returns:
            Dictionary mapping symbols to their stats.
        """
        result = {}
        for symbol, engine in self._engines.items():
            current_bar = engine.get_current_bar()
            if current_bar:
                result[symbol] = {
                    "delta": current_bar.delta,
                    "volume": current_bar.volume,
                    "buy_imbalance": current_bar.buy_imbalance_count,
                    "sell_imbalance": current_bar.sell_imbalance_count,
                    "profile": engine.get_market_profile(current_bar),
                }
        return result

    def reset_all(self) -> None:
        """Reset all footprint engines."""
        for engine in self._engines.values():
            engine.reset()
        self._engines.clear()

