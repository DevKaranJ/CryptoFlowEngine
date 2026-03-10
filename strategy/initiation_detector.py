"""
Initiation Detector - Detects initiation candles.

An initiation candle is the first candle after absorption that shows
the aggressive side taking control. This is a key entry signal.

This module detects:
- Bullish initiation: First strong buying after sell absorption
- Bearish initiation: First strong selling after buy absorption
- Momentum candle confirmation
"""

from dataclasses import dataclass
from typing import Any

from config import get_settings
from core.logging_config import get_logger

logger = get_logger("strategy.initiation")


@dataclass
class InitiationData:
    """Represents initiation detection data."""

    detected: bool
    direction: str  # "bullish", "bearish", "none"
    candle_index: int
    price: float
    strength: float  # 0 to 1
    confirmation: bool


class InitiationDetector:
    """
    Detects initiation candles.

    An initiation candle signals the start of a new move after
    consolidation or absorption.
    """

    def __init__(self) -> None:
        """Initialize the initiation detector."""
        self.settings = get_settings()
        self._last_initiation: InitiationData | None = None

    def detect_initiation(
        self,
        current_candle: dict[str, Any],
        previous_candle: dict[str, Any],
        absorption_candle: dict[str, Any] | None = None,
        imbalance_type: str = "none"
    ) -> InitiationData:
        """
        Detect initiation candle.

        Args:
            current_candle: Current candle data.
            previous_candle: Previous candle data.
            absorption_candle: The absorption candle (if known).
            imbalance_type: Type of imbalance detected ("buy", "sell", "none").

        Returns:
            InitiationData with detection results.
        """
        current_close = current_candle.get("close", 0)
        current_open = current_candle.get("open", 0)
        current_high = current_candle.get("high", 0)
        current_low = current_candle.get("low", 0)
        current_volume = current_candle.get("volume", 0)

        prev_close = previous_candle.get("close", 0)
        prev_open = previous_candle.get("open", 0)

        detected = False
        direction = "none"
        strength = 0.0
        confirmation = False

        # Calculate candle properties
        is_bullish = current_close > current_open
        is_bearish = current_close < current_open
        candle_size = abs(current_close - current_open)
        candle_range = current_high - current_low

        # Avoid division by zero
        if candle_range == 0:
            candle_range = 0.01

        # Check for bullish initiation
        if is_bullish and imbalance_type == "sell":
            # Previous candle showed sell imbalance, now we have buying
            # Check if this is a strong confirmation

            # Condition 1: Close near top of candle
            close_position = (current_close - current_low) / candle_range
            strong_close = close_position > 0.7

            # Condition 2: Volume confirmation
            volume_increase = current_volume > previous_candle.get("volume", 0) * 1.2

            # Condition 3: Close above previous candle high (if available)
            break_high = current_close > previous_candle.get("high", current_close)

            if strong_close or break_high:
                detected = True
                direction = "bullish"
                confirmation = True

                # Calculate strength
                strength = 0.5
                if strong_close:
                    strength += 0.2
                if volume_increase:
                    strength += 0.15
                if break_high:
                    strength += 0.15

        # Check for bearish initiation
        elif is_bearish and imbalance_type == "buy":
            # Previous candle showed buy imbalance, now we have selling
            # Check if this is a strong confirmation

            # Condition 1: Close near bottom of candle
            close_position = (current_high - current_close) / candle_range
            strong_close = close_position > 0.7

            # Condition 2: Volume confirmation
            volume_increase = current_volume > previous_candle.get("volume", 0) * 1.2

            # Condition 3: Close below previous candle low
            break_low = current_close < previous_candle.get("low", current_close)

            if strong_close or break_low:
                detected = True
                direction = "bearish"
                confirmation = True

                # Calculate strength
                strength = 0.5
                if strong_close:
                    strength += 0.2
                if volume_increase:
                    strength += 0.15
                if break_low:
                    strength += 0.15

        # Alternative: Check for momentum candle without known absorption
        elif not absorption_candle:
            # Bullish momentum
            if is_bullish and candle_size > candle_range * 0.6:
                # Strong bullish candle
                close_position = (current_close - current_low) / candle_range
                if close_position > 0.8:  # Strong close
                    detected = True
                    direction = "bullish"
                    strength = 0.6
                    confirmation = True

            # Bearish momentum
            elif is_bearish and candle_size > candle_range * 0.6:
                close_position = (current_high - current_close) / candle_range
                if close_position > 0.8:  # Strong close
                    detected = True
                    direction = "bearish"
                    strength = 0.6
                    confirmation = True

        initiation = InitiationData(
            detected=detected,
            direction=direction,
            candle_index=current_candle.get("index", 0),
            price=current_close,
            strength=min(1.0, strength),
            confirmation=confirmation,
        )

        if detected:
            self._last_initiation = initiation
            logger.info(
                f"Initiation detected: {direction} at {current_close}, "
                f"strength={strength:.2f}"
            )

        return initiation

    def detect_initiation_with_absorption(
        self,
        candles: list[dict[str, Any]],
        absorption_index: int,
        current_index: int
    ) -> InitiationData:
        """
        Detect initiation after a known absorption candle.

        Args:
            candles: List of candle data.
            absorption_index: Index of the absorption candle.
            current_index: Current candle index.

        Returns:
            InitiationData with detection results.
        """
        if absorption_index < 0 or current_index <= absorption_index:
            return InitiationData(
                detected=False,
                direction="none",
                candle_index=current_index,
                price=0,
                strength=0,
                confirmation=False,
            )

        absorption_candle = candles[absorption_index]
        current_candle = candles[current_index]
        prev_candle = candles[current_index - 1]

        # Determine absorption type
        absorption_buy = absorption_candle.get("buy_volume", 0) > absorption_candle.get("sell_volume", 0) * 2
        absorption_sell = absorption_candle.get("sell_volume", 0) > absorption_candle.get("buy_volume", 0) * 2

        imbalance_type = "none"
        if absorption_sell:
            imbalance_type = "sell"
        elif absorption_buy:
            imbalance_type = "buy"

        return self.detect_initiation(
            current_candle=current_candle,
            previous_candle=prev_candle,
            absorption_candle=absorption_candle,
            imbalance_type=imbalance_type,
        )

    def is_momentum_candle(
        self,
        candle: dict[str, Any],
        avg_volume: float = 0
    ) -> dict[str, Any]:
        """
        Check if a candle has momentum characteristics.

        Args:
            candle: Candle data.
            avg_volume: Average volume for comparison.

        Returns:
            Dictionary with momentum analysis.
        """
        close = candle.get("close", 0)
        open_price = candle.get("open", 0)
        high = candle.get("high", 0)
        low = candle.get("low", 0)
        volume = candle.get("volume", 0)

        is_bullish = close > open_price
        is_bearish = close < open_price

        candle_range = high - low
        if candle_range == 0:
            candle_range = 0.01

        body = abs(close - open_price)
        body_ratio = body / candle_range

        # Check close position
        if is_bullish:
            close_position = (close - low) / candle_range
        else:
            close_position = (high - close) / candle_range

        # Check volume
        volume_spike = False
        if avg_volume > 0 and volume > avg_volume * 1.5:
            volume_spike = True

        # Determine momentum
        has_momentum = False
        direction = "none"

        if is_bullish and body_ratio > 0.5 and close_position > 0.7:
            has_momentum = True
            direction = "bullish"
        elif is_bearish and body_ratio > 0.5 and close_position > 0.7:
            has_momentum = True
            direction = "bearish"

        return {
            "has_momentum": has_momentum,
            "direction": direction,
            "body_ratio": body_ratio,
            "close_position": close_position,
            "volume_spike": volume_spike,
        }

    def detect_breakout_initiation(
        self,
        candles: list[dict[str, Any]],
        breakout_level: float,
        direction: str  # "bullish" or "bearish"
    ) -> InitiationData:
        """
        Detect initiation after a breakout.

        Args:
            candles: List of candle data.
            breakout_level: Level that was broken.
            direction: Direction of breakout.

        Returns:
            InitiationData with detection results.
        """
        if not candles:
            return InitiationData(
                detected=False,
                direction="none",
                candle_index=0,
                price=0,
                strength=0,
                confirmation=False,
            )

        current_candle = candles[-1]
        current_close = current_candle.get("close", 0)

        # Check if current candle confirms the breakout
        if direction == "bullish":
            # For bullish breakout, candle should be bullish and close above level
            is_valid = (
                current_close > breakout_level and
                current_close > current_candle.get("open", 0)
            )
            detected = is_valid
            detected_direction = "bullish" if is_valid else "none"

        else:
            # For bearish breakout, candle should be bearish and close below level
            is_valid = (
                current_close < breakout_level and
                current_close < current_candle.get("open", 0)
            )
            detected = is_valid
            detected_direction = "bearish" if is_valid else "none"

        return InitiationData(
            detected=detected,
            direction=detected_direction,
            candle_index=len(candles) - 1,
            price=current_close,
            strength=0.7 if detected else 0,
            confirmation=detected,
        )

    def get_last_initiation(self) -> InitiationData | None:
        """
        Get the last detected initiation.

        Returns:
            Last initiation data or None.
        """
        return self._last_initiation

    def reset(self) -> None:
        """Reset the initiation detector."""
        self._last_initiation = None
        logger.info("Initiation detector reset")

