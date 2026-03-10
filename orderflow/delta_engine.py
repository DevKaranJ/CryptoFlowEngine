"""
Delta Engine - Calculates and tracks delta values.

Delta represents the net buying or selling pressure, calculated as:
Delta = Buy Volume - Sell Volume

This module tracks delta across different timeframes and detects
delta divergences and spikes.
"""

from collections import deque
from dataclasses import dataclass
from typing import Any

from config import get_settings
from core.logging_config import get_logger

logger = get_logger("orderflow.delta")


@dataclass
class DeltaData:
    """Represents delta data for a time period."""

    timestamp: int
    buy_volume: float
    sell_volume: float
    delta: float

    @property
    def total_volume(self) -> float:
        """Total volume for the period."""
        return self.buy_volume + self.sell_volume

    @property
    def buy_ratio(self) -> float:
        """Percentage of volume that is buying."""
        if self.total_volume == 0:
            return 0.5
        return self.buy_volume / self.total_volume


class DeltaEngine:
    """
    Delta calculation and tracking engine.

    Processes trade data to calculate real-time delta values
    and detect delta patterns.
    """

    def __init__(self) -> None:
        """Initialize the delta engine."""
        self.settings = get_settings()
        self._delta_history: deque[DeltaData] = deque(maxlen=1000)
        self._current_period_buy: float = 0.0
        self._current_period_sell: float = 0.0
        self._current_period_start: int = 0

    def process_trade(self, quantity: float, side: str, timestamp: int, period_ms: int = 60000) -> DeltaData:
        """
        Process a trade and update delta.

        Args:
            quantity: Trade quantity.
            side: Trade side ("buy" or "sell").
            timestamp: Trade timestamp in milliseconds.
            period_ms: Delta calculation period in milliseconds (default 1 minute).

        Returns:
            The current period's delta data.
        """
        # Check if we need to start a new period
        period_start = (timestamp // period_ms) * period_ms

        if period_start != self._current_period_start:
            # Finalize current period
            if self._current_period_start > 0:
                self._finalize_period()

            # Start new period
            self._current_period_start = period_start
            self._current_period_buy = 0.0
            self._current_period_sell = 0.0

        # Update current period
        if side == "buy":
            self._current_period_buy += quantity
        else:
            self._current_period_sell += quantity

        # Return current period data
        return self._get_current_delta()

    def _finalize_period(self) -> None:
        """Finalize the current period and add to history."""
        if self._current_period_start > 0:
            delta_data = DeltaData(
                timestamp=self._current_period_start,
                buy_volume=self._current_period_buy,
                sell_volume=self._current_period_sell,
                delta=self._current_period_buy - self._current_period_sell,
            )
            self._delta_history.append(delta_data)
            logger.debug(
                f"Delta period finalized: {delta_data.timestamp} - "
                f"Buy: {delta_data.buy_volume:.4f}, "
                f"Sell: {delta_data.sell_volume:.4f}, "
                f"Delta: {delta_data.delta:.4f}"
            )

    def _get_current_delta(self) -> DeltaData:
        """Get delta data for the current period."""
        return DeltaData(
            timestamp=self._current_period_start,
            buy_volume=self._current_period_buy,
            sell_volume=self._current_period_sell,
            delta=self._current_period_buy - self._current_period_sell,
        )

    def process_trade_data(self, trade_data: dict[str, Any], period_ms: int = 60000) -> DeltaData:
        """
        Process trade data from dictionary.

        Args:
            trade_data: Trade data dictionary.
            period_ms: Delta calculation period.

        Returns:
            Current period delta data.
        """
        return self.process_trade(
            quantity=trade_data["quantity"],
            side=trade_data["side"],
            timestamp=trade_data["timestamp"],
            period_ms=period_ms,
        )

    def get_current_delta(self) -> DeltaData:
        """
        Get the current period's delta.

        Returns:
            Current period delta data.
        """
        return self._get_current_delta()

    def get_delta_history(self, count: int = 100) -> list[DeltaData]:
        """
        Get historical delta data.

        Args:
            count: Number of periods to return.

        Returns:
            List of historical delta data.
        """
        return list(self._delta_history)[-count:]

    def get_cumulative_delta(self, periods: int = 10) -> float:
        """
        Get cumulative delta over recent periods.

        Args:
            periods: Number of periods to sum.

        Returns:
            Cumulative delta value.
        """
        history = self.get_delta_history(periods)
        return sum(d.delta for d in history)

    def get_average_delta(self, periods: int = 20) -> float:
        """
        Get average delta over recent periods.

        Args:
            periods: Number of periods to average.

        Returns:
            Average delta value.
        """
        history = self.get_delta_history(periods)
        if not history:
            return 0.0
        return sum(d.delta for d in history) / len(history)

    def detect_delta_spike(self, threshold_multiplier: float = 3.0) -> tuple[bool, str]:
        """
        Detect if current delta is a spike compared to average.

        Args:
            threshold_multiplier: How many times average to trigger spike.

        Returns:
            Tuple of (is_spike, "positive" or "negative").
        """
        current = self.get_current_delta().delta
        avg = self.get_average_delta(20)

        if avg == 0:
            return False, ""

        if abs(current) > abs(avg) * threshold_multiplier:
            if current > 0:
                return True, "positive"
            else:
                return True, "negative"

        return False, ""

    def detect_delta_divergence(
        self,
        price_data: list[dict[str, Any]],
        lookback: int = 5
    ) -> tuple[bool, str]:
        """
        Detect delta divergence with price.

        Args:
            price_data: List of price data with "low" or "high" keys.
            lookback: Number of periods to check.

        Returns:
            Tuple of (is_divergence, "bullish" or "bearish").
        """
        history = self.get_delta_history(lookback * 2)
        if len(history) < lookback + 1:
            return False, ""

        # Get recent price swing
        recent_prices = [p.get("low", p.get("close", 0)) for p in price_data[-lookback:]]
        older_prices = [p.get("low", p.get("close", 0)) for p in price_data[-(lookback * 2):-lookback]]

        if not recent_prices or not older_prices:
            return False, ""

        recent_low = min(recent_prices)
        older_low = min(older_prices)

        # Get recent delta swing
        recent_delta = [d.delta for d in history[-lookback:]]
        older_delta = [d.delta for d in history[-(lookback * 2):-lookback]]

        recent_delta_low = min(recent_delta)
        older_delta_low = min(older_delta)

        # Bullish divergence: price makes lower low, delta makes higher low
        if recent_low < older_low and recent_delta_low > older_delta_low:
            return True, "bullish"

        # Bearish divergence: price makes higher high, delta makes lower high
        recent_high = max([p.get("high", p.get("close", 0)) for p in price_data[-lookback:]])
        older_high = max([p.get("high", p.get("close", 0)) for p in price_data[-(lookback * 2):-lookback]])

        recent_delta_high = max(recent_delta)
        older_delta_high = max(older_delta)

        if recent_high > older_high and recent_delta_high < older_delta_high:
            return True, "bearish"

        return False, ""

    def get_delta_oscillator(self, short_period: int = 5, long_period: int = 20) -> float:
        """
        Calculate delta oscillator (short MA - long MA).

        Args:
            short_period: Short MA period.
            long_period: Long MA period.

        Returns:
            Delta oscillator value.
        """
        short_history = self.get_delta_history(short_period)
        long_history = self.get_delta_history(long_period)

        if not short_history or not long_history:
            return 0.0

        short_ma = sum(d.delta for d in short_history) / len(short_history)
        long_ma = sum(d.delta for d in long_history) / len(long_history)

        return short_ma - long_ma

    def reset(self) -> None:
        """Reset the delta engine state."""
        self._delta_history.clear()
        self._current_period_buy = 0.0
        self._current_period_sell = 0.0
        self._current_period_start = 0
        logger.info("Delta engine reset")


class MultiSymbolDeltaEngine:
    """Manages delta engines for multiple symbols."""

    def __init__(self) -> None:
        """Initialize multi-symbol delta engine."""
        self._engines: dict[str, DeltaEngine] = {}

    def get_engine(self, symbol: str) -> DeltaEngine:
        """Get or create a delta engine for a symbol."""
        if symbol not in self._engines:
            self._engines[symbol] = DeltaEngine()
        return self._engines[symbol]

    def process_trade(self, symbol: str, quantity: float, side: str, timestamp: int) -> DeltaData:
        """Process a trade for a specific symbol."""
        return self.get_engine(symbol).process_trade(quantity, side, timestamp)

    def reset_all(self) -> None:
        """Reset all delta engines."""
        for engine in self._engines.values():
            engine.reset()
        self._engines.clear()

