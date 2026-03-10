"""
CVD (Cumulative Volume Delta) Engine - Tracks cumulative volume delta.

CVD is the running total of delta over time:
CVD[t] = CVD[t-1] + Delta[t]

This module tracks CVD across different timeframes and detects
CVD divergences with price.
"""

from collections import deque
from dataclasses import dataclass
from typing import Any

from config import get_settings
from core.logging_config import get_logger

logger = get_logger("orderflow.cvd")


@dataclass
class CVDData:
    """Represents CVD data at a point in time."""

    timestamp: int
    delta: float
    cvd: float

    @property
    def is_positive(self) -> bool:
        """Whether CVD is positive (bullish)."""
        return self.cvd > 0

    @property
    def is_negative(self) -> bool:
        """Whether CVD is negative (bearish)."""
        return self.cvd < 0


class CVDSnapshot:
    """Represents a snapshot of CVD state at a specific time."""

    def __init__(self, timestamp: int, cvd: float, price: float) -> None:
        """
        Initialize CVD snapshot.

        Args:
            timestamp: Snapshot timestamp.
            cvd: CVD value at this time.
            price: Price at this time.
        """
        self.timestamp = timestamp
        self.cvd = cvd
        self.price = price


class CVDEngine:
    """
    Cumulative Volume Delta calculation and tracking engine.

    Tracks CVD over time and detects divergences and swings.
    """

    def __init__(self) -> None:
        """Initialize the CVD engine."""
        self.settings = get_settings()
        self._cvd: float = 0.0
        self._cvd_history: deque[CVDData] = deque(maxlen=2000)
        self._swings: deque[CVDSnapshot] = deque(maxlen=100)
        self._last_cvd_update: int = 0
        self._current_delta: float = 0.0

    def process_delta(self, delta: float, timestamp: int) -> CVDData:
        """
        Process a delta value and update CVD.

        Args:
            delta: Delta value (buy - sell).
            timestamp: Current timestamp in milliseconds.

        Returns:
            Updated CVD data.
        """
        self._current_delta = delta
        self._cvd += delta
        self._last_cvd_update = timestamp

        cvd_data = CVDData(
            timestamp=timestamp,
            delta=delta,
            cvd=self._cvd,
        )

        self._cvd_history.append(cvd_data)

        # Check for CVD swing (trend reversal)
        if len(self._cvd_history) >= 2:
            prev_cvd = self._cvd_history[-2].cvd
            if (prev_cvd < 0 and self._cvd >= 0) or (prev_cvd > 0 and self._cvd <= 0):
                # CVD crossed zero - record swing
                logger.debug(f"CVD swing detected: {prev_cvd:.4f} -> {self._cvd:.4f}")

        return cvd_data

    def process_trade(self, quantity: float, side: str, timestamp: int) -> CVDData:
        """
        Process a trade and update CVD.

        Args:
            quantity: Trade quantity.
            side: Trade side ("buy" or "sell").
            timestamp: Trade timestamp.

        Returns:
            Updated CVD data.
        """
        delta = quantity if side == "buy" else -quantity
        return self.process_delta(delta, timestamp)

    def process_trade_data(self, trade_data: dict[str, Any]) -> CVDData:
        """
        Process trade data from dictionary.

        Args:
            trade_data: Trade data dictionary.

        Returns:
            Updated CVD data.
        """
        quantity = trade_data["quantity"]
        side = trade_data["side"]
        timestamp = trade_data["timestamp"]

        delta = quantity if side == "buy" else -quantity
        return self.process_delta(delta, timestamp)

    def get_current_cvd(self) -> float:
        """
        Get the current CVD value.

        Returns:
            Current CVD.
        """
        return self._cvd

    def get_current_delta(self) -> float:
        """
        Get the current period's delta.

        Returns:
            Current delta.
        """
        return self._current_delta

    def get_cvd_history(self, count: int = 100) -> list[CVDData]:
        """
        Get historical CVD data.

        Args:
            count: Number of data points to return.

        Returns:
            List of historical CVD data.
        """
        return list(self._cvd_history)[-count:]

    def record_swing(self, price: float) -> None:
        """
        Record a CVD swing at the current price level.

        Args:
            price: Current price when swing is recorded.
        """
        swing = CVDSnapshot(
            timestamp=self._last_cvd_update,
            cvd=self._cvd,
            price=price,
        )
        self._swings.append(swing)
        logger.debug(f"CVD swing recorded: CVD={self._cvd:.4f}, Price={price}")

    def get_swing_highs(self, lookback: int = 10) -> list[CVDSnapshot]:
        """
        Get recent CVD swing highs.

        Args:
            lookback: Number of swings to look back.

        Returns:
            List of swing high snapshots.
        """
        swings = list(self._swings)[-lookback:]
        highs = []
        last_cvd = float("-inf")

        for swing in swings:
            if swing.cvd > last_cvd:
                highs.append(swing)
                last_cvd = swing.cvd

        return highs

    def get_swing_lows(self, lookback: int = 10) -> list[CVDSnapshot]:
        """
        Get recent CVD swing lows.

        Args:
            lookback: Number of swings to look back.

        Returns:
            List of swing low snapshots.
        """
        swings = list(self._swings)[-lookback:]
        lows = []
        last_cvd = float("inf")

        for swing in swings:
            if swing.cvd < last_cvd:
                lows.append(swing)
                last_cvd = swing.cvd

        return lows

    def detect_divergence(
        self,
        price_swing_highs: list[float],
        price_swing_lows: list[float],
        lookback: int = 5
    ) -> tuple[bool, str]:
        """
        Detect CVD divergence with price swings.

        Args:
            price_swing_highs: List of recent price swing highs.
            price_swing_lows: List of recent price swing lows.
            lookback: Number of swings to compare.

        Returns:
            Tuple of (is_divergence, "bullish" or "bearish").
        """
        if not price_swing_highs or not price_swing_lows:
            return False, ""

        # Get recent swings
        swing_highs = self.get_swing_highs(lookback * 2)
        swing_lows = self.get_swing_lows(lookback * 2)

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return False, ""

        # Check for bullish divergence:
        # Price makes lower low, but CVD makes higher low
        recent_price_low = min(price_swing_lows[-lookback:]) if len(price_swing_lows) >= lookback else min(price_swing_lows)
        older_price_low = min(price_swing_lows[:-lookback]) if len(price_swing_lows) > lookback else price_swing_lows[0]

        recent_cvd_low = swing_lows[-1].cvd if swing_lows else self._cvd
        older_cvd_low = swing_lows[0].cvd if len(swing_lows) > 1 else self._cvd

        if recent_price_low < older_price_low and recent_cvd_low > older_cvd_low:
            return True, "bullish"

        # Check for bearish divergence:
        # Price makes higher high, but CVD makes lower high
        recent_price_high = max(price_swing_highs[-lookback:]) if len(price_swing_highs) >= lookback else max(price_swing_highs)
        older_price_high = max(price_swing_highs[:-lookback]) if len(price_swing_highs) > lookback else price_swing_highs[0]

        recent_cvd_high = swing_highs[-1].cvd if swing_highs else self._cvd
        older_cvd_high = swing_highs[0].cvd if len(swing_highs) > 1 else self._cvd

        if recent_price_high > older_price_high and recent_cvd_high < older_cvd_high:
            return True, "bearish"

        return False, ""

    def get_cvd_momentum(self, periods: int = 10) -> float:
        """
        Calculate CVD momentum (rate of change).

        Args:
            periods: Number of periods for momentum calculation.

        Returns:
            CVD momentum value.
        """
        history = self.get_cvd_history(periods * 2)
        if len(history) < periods + 1:
            return 0.0

        recent_cvd = history[-1].cvd
        older_cvd = history[-(periods + 1)].cvd

        return recent_cvd - older_cvd

    def get_cvd_rate_of_change(self, periods: int = 20) -> float:
        """
        Calculate CVD rate of change as percentage.

        Args:
            periods: Number of periods for ROC calculation.

        Returns:
            CVD rate of change (percentage).
        """
        history = self.get_cvd_history(periods * 2)
        if len(history) < periods + 1:
            return 0.0

        recent_cvd = history[-1].cvd
        older_cvd = history[-(periods + 1)].cvd

        if older_cvd == 0:
            return 0.0

        return ((recent_cvd - older_cvd) / abs(older_cvd)) * 100

    def get_trend_strength(self, periods: int = 20) -> float:
        """
        Calculate CVD trend strength.

        Args:
            periods: Number of periods to analyze.

        Returns:
            Trend strength from -1 (strong bearish) to 1 (strong bullish).
        """
        history = self.get_cvd_history(periods)
        if len(history) < periods:
            return 0.0

        # Count positive vs negative deltas
        positive_deltas = sum(1 for d in history if d.delta > 0)
        negative_deltas = sum(1 for d in history if d.delta < 0)

        total = positive_deltas + negative_deltas
        if total == 0:
            return 0.0

        return (positive_deltas - negative_deltas) / total

    def reset(self) -> None:
        """Reset the CVD engine state."""
        self._cvd = 0.0
        self._cvd_history.clear()
        self._swings.clear()
        self._last_cvd_update = 0
        self._current_delta = 0.0
        logger.info("CVD engine reset")


class MultiSymbolCVDEngine:
    """Manages CVD engines for multiple symbols."""

    def __init__(self) -> None:
        """Initialize multi-symbol CVD engine."""
        self._engines: dict[str, CVDEngine] = {}

    def get_engine(self, symbol: str) -> CVDEngine:
        """Get or create a CVD engine for a symbol."""
        if symbol not in self._engines:
            self._engines[symbol] = CVDEngine()
        return self._engines[symbol]

    def process_trade(self, symbol: str, quantity: float, side: str, timestamp: int) -> CVDData:
        """Process a trade for a specific symbol."""
        return self.get_engine(symbol).process_trade(quantity, side, timestamp)

    def get_cvd(self, symbol: str) -> float:
        """Get current CVD for a symbol."""
        return self.get_engine(symbol).get_current_cvd()

    def reset_all(self) -> None:
        """Reset all CVD engines."""
        for engine in self._engines.values():
            engine.reset()
        self._engines.clear()

