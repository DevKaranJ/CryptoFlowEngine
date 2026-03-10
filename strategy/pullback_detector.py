"""
Pullback Detector - Detects pullback confirmation for entries.

A pullback is a temporary reversal in the direction of a price trend
that offers a better entry point. This module detects:

- Price retesting key levels
- Pullback to initiation candle
- Pullback to absorption level
- Trend continuation confirmation
"""

from dataclasses import dataclass
from typing import Any

from config import get_settings
from core.logging_config import get_logger

logger = get_logger("strategy.pullback")


@dataclass
class PullbackData:
    """Represents pullback detection data."""

    detected: bool
    direction: str  # "bullish", "bearish", "none"
    pullback_type: str  # "to_level", "to_candle", "to_absorption"
    entry_price: float
    stop_price: float
    strength: float  # 0 to 1
    confirmation: bool


class PullbackDetector:
    """
    Detects pullback opportunities for entries.

    Monitors price retraces to key levels for optimal entry timing.
    """

    def __init__(self) -> None:
        """Initialize the pullback detector."""
        self.settings = get_settings()
        self._last_pullback: PullbackData | None = None

    def detect_pullback_to_level(
        self,
        current_price: float,
        key_level: float,
        direction: str,  # "bullish" or "bearish"
        tolerance: float = 0.002  # 0.2% tolerance
    ) -> PullbackData:
        """
        Detect pullback to a key level.

        Args:
            current_price: Current price.
            key_level: Key level to pullback to.
            direction: Expected direction after pullback.
            tolerance: Price tolerance for level touch.

        Returns:
            PullbackData with detection results.
        """
        detected = False
        pullback_type = "to_level"
        strength = 0.0
        confirmation = False

        # Check if price is near the level
        if direction == "bullish":
            # For bullish, looking for pullback TO a support level
            # Price should be above or at the level (after pullback)
            price_diff = (current_price - key_level) / key_level

            if -tolerance <= price_diff <= tolerance:
                # Price at or near the level
                detected = True
                strength = 0.7

                # Stronger if price is slightly above (showing respect)
                if price_diff > 0:
                    strength += 0.2
                    confirmation = True

                entry = key_level
                stop = key_level * 0.995  # 0.5% stop

        else:
            # For bearish, looking for pullback TO a resistance level
            price_diff = (key_level - current_price) / key_level

            if -tolerance <= price_diff <= tolerance:
                detected = True
                strength = 0.7

                if price_diff > 0:
                    strength += 0.2
                    confirmation = True

                entry = key_level
                stop = key_level * 1.005  # 0.5% stop

        return PullbackData(
            detected=detected,
            direction=direction,
            pullback_type=pullback_type,
            entry_price=entry if detected else 0,
            stop_price=stop if detected else 0,
            strength=min(1.0, strength),
            confirmation=confirmation,
        )

    def detect_pullback_to_candle(
        self,
        current_price: float,
        initiation_candle: dict[str, Any],
        direction: str,
        tolerance: float = 0.003  # 0.3% tolerance
    ) -> PullbackData:
        """
        Detect pullback to an initiation candle.

        Args:
            current_price: Current price.
            initiation_candle: The initiation candle data.
            direction: Expected direction after pullback.
            tolerance: Price tolerance.

        Returns:
            PullbackData with detection results.
        """
        if not initiation_candle:
            return PullbackData(
                detected=False,
                direction="none",
                pullback_type="none",
                entry_price=0,
                stop_price=0,
                strength=0,
                confirmation=False,
            )

        detected = False
        pullback_type = "to_candle"
        strength = 0.0
        confirmation = False

        candle_low = initiation_candle.get("low", 0)
        candle_high = initiation_candle.get("high", 0)
        candle_open = initiation_candle.get("open", 0)
        candle_close = initiation_candle.get("close", 0)

        if direction == "bullish":
            # Pullback to bullish candle = retest low of candle
            price_diff = (current_price - candle_low) / candle_low

            if -tolerance <= price_diff <= tolerance:
                detected = True
                strength = 0.8  # Strong signal

                # Entry at candle low or slightly above
                entry = candle_low * 1.001  # 0.1% above
                stop = candle_low * 0.995  # 0.5% stop

                # Confirmation: price starts moving up
                if current_price > candle_open:
                    confirmation = True
                    strength += 0.15

        else:
            # Pullback to bearish candle = retest high of candle
            price_diff = (candle_high - current_price) / candle_high

            if -tolerance <= price_diff <= tolerance:
                detected = True
                strength = 0.8

                entry = candle_high * 0.999
                stop = candle_high * 1.005

                if current_price < candle_open:
                    confirmation = True
                    strength += 0.15

        return PullbackData(
            detected=detected,
            direction=direction,
            pullback_type=pullback_type,
            entry_price=entry if detected else 0,
            stop_price=stop if detected else 0,
            strength=min(1.0, strength),
            confirmation=confirmation,
        )

    def detect_pullback_to_absorption(
        self,
        current_price: float,
        absorption_price: float,
        direction: str,
        tolerance: float = 0.002
    ) -> PullbackData:
        """
        Detect pullback to absorption level.

        Args:
            current_price: Current price.
            absorption_price: Price where absorption occurred.
            direction: Expected direction after pullback.
            tolerance: Price tolerance.

        Returns:
            PullbackData with detection results.
        """
        detected = False
        pullback_type = "to_absorption"
        strength = 0.0
        confirmation = False
        entry = 0
        stop = 0

        if direction == "bullish":
            price_diff = (current_price - absorption_price) / absorption_price

            if -tolerance <= price_diff <= tolerance:
                detected = True
                strength = 0.85  # High strength for absorption pullback
                entry = absorption_price * 1.001
                stop = absorption_price * 0.995

                confirmation = True

        else:
            price_diff = (absorption_price - current_price) / absorption_price

            if -tolerance <= price_diff <= tolerance:
                detected = True
                strength = 0.85
                entry = absorption_price * 0.999
                stop = absorption_price * 1.005

                confirmation = True

        return PullbackData(
            detected=detected,
            direction=direction,
            pullback_type=pullback_type,
            entry_price=entry,
            stop_price=stop,
            strength=min(1.0, strength),
            confirmation=confirmation,
        )

    def detect_pullback_in_trend(
        self,
        candles: list[dict[str, Any]],
        direction: str,
        lookback: int = 5
    ) -> PullbackData:
        """
        Detect pullback within a trend.

        Args:
            candles: Recent candle data.
            direction: Trend direction.
            lookback: How many candles to look back.

        Returns:
            PullbackData with detection results.
        """
        if len(candles) < lookback:
            return PullbackData(
                detected=False,
                direction="none",
                pullback_type="none",
                entry_price=0,
                stop_price=0,
                strength=0,
                confirmation=False,
            )

        recent = candles[-lookback:]
        current_price = candles[-1].get("close", 0)

        if direction == "bullish":
            # In uptrend, pullback = price retracing down
            # Find recent high
            recent_high = max(c.get("high", 0) for c in recent)
            pullback_level = recent_high * 0.995  # Slightly below high

            return self.detect_pullback_to_level(
                current_price=current_price,
                key_level=pullback_level,
                direction="bullish",
                tolerance=0.003,
            )

        else:
            # In downtrend, pullback = price retracing up
            recent_low = min(c.get("low", 0) for c in recent)
            pullback_level = recent_low * 1.005

            return self.detect_pullback_to_level(
                current_price=current_price,
                key_level=pullback_level,
                direction="bearish",
                tolerance=0.003,
            )

    def calculate_stop_loss(
        self,
        entry_price: float,
        direction: str,
        atr: float = 0,
        use_atr: bool = False,
        risk_percent: float = 0.5
    ) -> float:
        """
        Calculate stop loss price.

        Args:
            entry_price: Entry price.
            direction: Trade direction.
            atr: Average True Range value.
            use_atr: Whether to use ATR for stops.
            risk_percent: Risk percentage for stop calculation.

        Returns:
            Stop loss price.
        """
        if use_atr and atr > 0:
            # ATR-based stop
            atr_multiplier = 2.0
            if direction == "bullish":
                return entry_price - (atr * atr_multiplier)
            else:
                return entry_price + (atr * atr_multiplier)
        else:
            # Percentage-based stop
            risk_decimal = risk_percent / 100
            if direction == "bullish":
                return entry_price * (1 - risk_decimal)
            else:
                return entry_price * (1 + risk_decimal)

    def calculate_take_profit(
        self,
        entry_price: float,
        stop_price: float,
        direction: str,
        risk_reward: float = 2.0
    ) -> dict[str, float]:
        """
        Calculate take profit levels.

        Args:
            entry_price: Entry price.
            stop_price: Stop loss price.
            direction: Trade direction.
            risk_reward: Target risk:reward ratio.

        Returns:
            Dictionary with TP1, TP2, TP3 levels.
        """
        risk = abs(entry_price - stop_price)
        reward = risk * risk_reward

        if direction == "bullish":
            tp1 = entry_price + (risk * 1.0)
            tp2 = entry_price + (risk * 2.0)
            tp3 = entry_price + (risk * 3.0)
        else:
            tp1 = entry_price - (risk * 1.0)
            tp2 = entry_price - (risk * 2.0)
            tp3 = entry_price - (risk * 3.0)

        return {
            "tp1": tp1,
            "tp2": tp2,
            "tp3": tp3,
        }

    def validate_pullback_entry(
        self,
        pullback_data: PullbackData,
        market_conditions: dict[str, Any]
    ) -> tuple[bool, str]:
        """
        Validate if pullback entry is valid given market conditions.

        Args:
            pullback_data: Pullback detection data.
            market_conditions: Current market conditions.

        Returns:
            Tuple of (is_valid, reason).
        """
        if not pullback_data.detected:
            return False, "No pullback detected"

        # Check minimum strength
        if pullback_data.strength < 0.5:
            return False, "Pullback strength too low"

        # Check market conditions
        volatility = market_conditions.get("volatility", 0)
        if volatility < 0.3:
            # Low volatility - be cautious
            if pullback_data.strength < 0.7:
                return False, "Low volatility requires stronger signal"

        # Check trend alignment
        trend = market_conditions.get("trend", "ranging")
        if trend == "ranging":
            # In range, pullback to support/resistance is valid
            if pullback_data.confirmation:
                return True, "Valid pullback in ranging market"
            else:
                return False, "No confirmation in ranging market"

        # In trending market, pullback should align with trend
        if pullback_data.direction == "bullish" and trend == "downtrend":
            return False, "Bullish pullback against downtrend"
        if pullback_data.direction == "bearish" and trend == "uptrend":
            return False, "Bearish pullback against uptrend"

        return True, "Valid pullback entry"

    def get_last_pullback(self) -> PullbackData | None:
        """
        Get the last detected pullback.

        Returns:
            Last pullback data or None.
        """
        return self._last_pullback

    def reset(self) -> None:
        """Reset the pullback detector."""
        self._last_pullback = None
        logger.info("Pullback detector reset")

