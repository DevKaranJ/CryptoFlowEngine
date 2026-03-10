"""
Absorption Detector - Detects absorption and iceberg orders.

Absorption occurs when aggressive orders are absorbed by limit orders
without moving the price significantly. This is a strong reversal signal.

This module detects:
- Absorption candles (high volume but price doesn't move much)
- Failed breakouts (liquidity sweep then reversal)
- Delta exhaustion (extreme delta but no price movement)
"""

from collections import deque
from dataclasses import dataclass
from typing import Any

from config import get_settings
from core.logging_config import get_logger

logger = get_logger("orderflow.absorption")


@dataclass
class AbsorptionData:
    """Represents absorption detection data."""

    timestamp: int
    absorption_detected: bool
    absorption_type: str  # "buy", "sell", "none"
    price: float
    volume: float
    delta: float
    strength: float  # 0 to 1


class AbsorptionDetector:
    """
    Detects absorption patterns in orderflow data.

    Absorption is one of the most powerful orderflow signals,
    indicating institutional presence and potential reversal.
    """

    def __init__(self) -> None:
        """Initialize the absorption detector."""
        self.settings = get_settings()
        self._absorption_history: deque[AbsorptionData] = deque(maxlen=200)
        self._current_absorption_type: str = "none"
        self._consecutive_absorption_count: int = 0

    def detect_absorption(
        self,
        buy_volume: float,
        sell_volume: float,
        price_open: float,
        price_close: float,
        price_high: float,
        price_low: float,
        timestamp: int
    ) -> AbsorptionData:
        """
        Detect absorption in a candle/period.

        Args:
            buy_volume: Total buy volume.
            sell_volume: Total sell volume.
            price_open: Period open price.
            price_close: Period close price.
            price_high: Period high price.
            price_low: Period low price.
            timestamp: Current timestamp.

        Returns:
            AbsorptionData with detection results.
        """
        total_volume = buy_volume + sell_volume
        delta = buy_volume - sell_volume
        price_range = price_high - price_low

        # Avoid division by zero
        if price_range == 0:
            price_range = 0.01

        # Calculate absorption strength based on:
        # 1. High volume relative to price movement
        # 2. Delta direction vs price direction
        absorption_type = "none"
        absorption_detected = False
        strength = 0.0

        # Calculate volume efficiency (how much price moved per unit volume)
        price_moved = abs(price_close - price_open)
        volume_efficiency = price_moved / total_volume if total_volume > 0 else 0

        # Low efficiency = potential absorption
        avg_efficiency = price_range / total_volume if total_volume > 0 else 0

        # Detect buy absorption: heavy selling but price didn't drop
        if sell_volume > buy_volume * 2:  # Significant sell imbalance
            if price_close >= price_open or price_close > price_low + (price_range * 0.7):
                # Selling was absorbed, buyers stepped in
                absorption_type = "buy"
                absorption_detected = True
                strength = min(1.0, (sell_volume - buy_volume) / total_volume)

        # Detect sell absorption: heavy buying but price didn't rise
        if buy_volume > sell_volume * 2:  # Significant buy imbalance
            if price_close <= price_open or price_close < price_high - (price_range * 0.7):
                # Buying was absorbed, sellers stepped in
                absorption_type = "sell"
                absorption_detected = True
                strength = min(1.0, (buy_volume - sell_volume) / total_volume)

        # Check for delta exhaustion (extreme delta but price didn't follow)
        avg_delta = total_volume * 0.3  # Expect ~30% delta in active market

        if abs(delta) > avg_delta * 2:  # Extreme delta
            if delta > 0 and price_close <= price_open + (price_range * 0.3):
                # Strong buying but price barely moved up
                absorption_type = "sell"
                absorption_detected = True
                strength = 0.8

            elif delta < 0 and price_close >= price_open - (price_range * 0.3):
                # Strong selling but price barely moved down
                absorption_type = "buy"
                absorption_detected = True
                strength = 0.8

        # Update state
        if absorption_detected:
            self._current_absorption_type = absorption_type
            self._consecutive_absorption_count += 1
        else:
            self._consecutive_absorption_count = 0

        absorption_data = AbsorptionData(
            timestamp=timestamp,
            absorption_detected=absorption_detected,
            absorption_type=absorption_type,
            price=price_close,
            volume=total_volume,
            delta=delta,
            strength=strength,
        )

        if absorption_detected:
            self._absorption_history.append(absorption_data)
            logger.debug(
                f"Absorption detected: {absorption_type} at {price_close}, "
                f"strength={strength:.2f}, volume={total_volume:.4f}"
            )

        return absorption_data

    def analyze_footprint_absorption(
        self,
        levels: dict[float, dict[str, float]],
        candle_open: float,
        candle_close: float,
        candle_high: float,
        candle_low: float,
        timestamp: int
    ) -> dict[str, Any]:
        """
        Analyze footprint data for absorption patterns.

        Args:
            levels: Footprint levels dictionary.
            candle_open: Candle open price.
            candle_close: Candle close price.
            candle_high: Candle high price.
            candle_low: Candle low price.
            timestamp: Current timestamp.

        Returns:
            Dictionary with absorption analysis.
        """
        if not levels:
            return {"absorption": False, "type": "none", "levels": []}

        absorption_levels = []
        price_range = candle_high - candle_low

        for price, level_data in levels.items():
            buy_vol = level_data.get("buy_volume", 0)
            sell_vol = level_data.get("sell_volume", 0)
            total = buy_vol + sell_vol

            if total == 0:
                continue

            # Calculate where price closed relative to this level
            if price_range > 0:
                level_position = (price - candle_low) / price_range
            else:
                level_position = 0.5

            # Buy absorption: high sell at low levels but price stayed high
            if sell_vol > buy_vol * 2 and level_position < 0.4:
                absorption_levels.append({
                    "price": price,
                    "type": "buy",
                    "volume": sell_vol,
                    "position": level_position,
                })

            # Sell absorption: high buy at high levels but price stayed low
            if buy_vol > sell_vol * 2 and level_position > 0.6:
                absorption_levels.append({
                    "price": price,
                    "type": "sell",
                    "volume": buy_vol,
                    "position": level_position,
                })

        # Determine overall absorption
        buy_absorption = [l for l in absorption_levels if l["type"] == "buy"]
        sell_absorption = [l for l in absorption_levels if l["type"] == "sell"]

        if len(buy_absorption) >= 2:
            absorption_type = "buy"
            detected = True
        elif len(sell_absorption) >= 2:
            absorption_type = "sell"
            detected = True
        else:
            absorption_type = "none"
            detected = False

        return {
            "absorption": detected,
            "type": absorption_type,
            "levels": absorption_levels,
            "buy_absorption_count": len(buy_absorption),
            "sell_absorption_count": len(sell_absorption),
        }

    def detect_liquidity_sweep(
        self,
        current_price: float,
        previous_swing_low: float,
        previous_swing_high: float,
        timestamp: int
    ) -> dict[str, Any]:
        """
        Detect liquidity sweeps (stop loss hunts).

        Args:
            current_price: Current price.
            previous_swing_low: Previous swing low.
            previous_swing_high: Previous swing high.
            timestamp: Current timestamp.

        Returns:
            Dictionary with sweep detection results.
        """
        sweep_result = {
            "detected": False,
            "type": "none",
            "swept_price": 0.0,
        }

        # Check for sweep below (liquidity grab at lows)
        if current_price < previous_swing_low:
            # Check if price returned above (sweep successful)
            sweep_result = {
                "detected": True,
                "type": "buy_side_sweep",  # Buyers swept liquidity below
                "swept_price": previous_swing_low,
                "direction": "bullish",
            }

        # Check for sweep above (liquidity grab at highs)
        elif current_price > previous_swing_high:
            sweep_result = {
                "detected": True,
                "type": "sell_side_sweep",  # Sellers swept liquidity above
                "swept_price": previous_swing_high,
                "direction": "bearish",
            }

        if sweep_result["detected"]:
            logger.info(
                f"Liquidity sweep detected: {sweep_result['type']} "
                f"at {sweep_result['swept_price']}"
            )

        return sweep_result

    def detect_failed_breakout(
        self,
        breakout_price: float,
        breakout_direction: str,  # "up" or "down"
        current_price: float,
        lookback_candles: int = 3
    ) -> dict[str, Any]:
        """
        Detect failed breakouts (breakout followed by reversal).

        Args:
            breakout_price: Price where breakout occurred.
            breakout_direction: Direction of breakout.
            current_price: Current price.
            lookback_candles: How far back to check for failure.

        Returns:
            Dictionary with failed breakout detection.
        """
        if breakout_direction == "up":
            # Failed bullish breakout - price broke higher but fell back
            failed = current_price < breakout_price
            return {
                "failed": failed,
                "type": "bullish" if failed else "none",
                "breakout_level": breakout_price,
                "reversal": "bearish" if failed else "",
            }
        else:
            # Failed bearish breakout - price broke lower but rose back
            failed = current_price > breakout_price
            return {
                "failed": failed,
                "type": "bearish" if failed else "none",
                "breakout_level": breakout_price,
                "reversal": "bullish" if failed else "",
            }

    def get_current_absorption_type(self) -> str:
        """
        Get the current absorption state.

        Returns:
            Current absorption type: "buy", "sell", or "none".
        """
        return self._current_absorption_type

    def analyze_bar(self, bar_data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze a bar for absorption patterns.

        This method provides a simplified interface for analyzing bar data
        when only basic market metrics are available (price, volume, delta).

        Args:
            bar_data: Dictionary containing:
                - price: Current price
                - volume: Total volume
                - delta: Volume delta (buy - sell)
                - cvd: Cumulative volume delta (optional)
                - buy_volume: Buy volume (optional, calculated if not provided)
                - sell_volume: Sell volume (optional, calculated if not provided)
                - timestamp: Current timestamp (optional)
                - open, high, low, close: OHLC data (optional, uses price if not provided)

        Returns:
            Dictionary with absorption analysis results.
        """
        import time
        
        # Extract data from bar_data
        price = bar_data.get("price", 0)
        volume = bar_data.get("volume", 0)
        delta = bar_data.get("delta", 0)
        
        # Calculate buy/sell volume from delta if not provided
        buy_volume = bar_data.get("buy_volume")
        sell_volume = bar_data.get("sell_volume")
        
        if buy_volume is None or sell_volume is None:
            # Estimate buy/sell volume from delta
            # delta = buy_volume - sell_volume
            # volume = buy_volume + sell_volume
            # Solving: buy_volume = (volume + delta) / 2, sell_volume = (volume - delta) / 2
            buy_volume = (volume + delta) / 2
            sell_volume = (volume - delta) / 2
        
        # Get timestamp
        timestamp = bar_data.get("timestamp", int(time.time() * 1000))
        
        # Get OHLC data if available, otherwise estimate from price
        price_open = bar_data.get("open", price)
        price_close = bar_data.get("close", price)
        price_high = bar_data.get("high", price * 1.001 if price else 0)  # Add small buffer
        price_low = bar_data.get("low", price * 0.999 if price else 0)
        
        # If OHLC values are all the same (no variation), estimate a reasonable range
        # based on volume and delta (market microstructure)
        if price_high == price_low or price_high == 0:
            # Estimate range as percentage of price based on volume
            # Higher volume = larger expected range
            volume_factor = min(1.0, volume / 1000000)  # Cap at 1%
            price_range_pct = 0.001 + (volume_factor * 0.002)  # 0.1% to 0.3%
            price_range = price * price_range_pct
            price_high = price + price_range
            price_low = price - price_range
        
        # Run absorption detection
        absorption_result = self.detect_absorption(
            buy_volume=buy_volume,
            sell_volume=sell_volume,
            price_open=price_open,
            price_close=price_close,
            price_high=price_high,
            price_low=price_low,
            timestamp=timestamp,
        )
        
        # Return formatted result
        return {
            "detected": absorption_result.absorption_detected,
            "type": absorption_result.absorption_type,
            "strength": absorption_result.strength,
            "price": absorption_result.price,
            "volume": absorption_result.volume,
            "delta": absorption_result.delta,
            "buy_volume": buy_volume,
            "sell_volume": sell_volume,
            "valid_signal": self.is_absorption_valid(absorption_result),
        }

    def get_consecutive_absorption_count(self) -> int:
        """
        Get count of consecutive absorption signals.

        Returns:
            Number of consecutive absorption detections.
        """
        return self._consecutive_absorption_count

    def get_absorption_history(self, count: int = 50) -> list[AbsorptionData]:
        """
        Get recent absorption history.

        Args:
            count: Number of events to return.

        Returns:
            List of recent absorption data.
        """
        return list(self._absorption_history)[-count:]

    def is_absorption_valid(
        self,
        absorption_data: AbsorptionData,
        min_strength: float = 0.5
    ) -> bool:
        """
        Check if absorption signal is valid for trading.

        Args:
            absorption_data: Absorption data to validate.
            min_strength: Minimum strength threshold.

        Returns:
            True if absorption is valid.
        """
        return (
            absorption_data.absorption_detected and
            absorption_data.strength >= min_strength and
            absorption_data.volume > 0
        )

    def reset(self) -> None:
        """Reset the absorption detector state."""
        self._absorption_history.clear()
        self._current_absorption_type = "none"
        self._consecutive_absorption_count = 0
        logger.info("Absorption detector reset")


class OrderflowAbsorptionAnalyzer:
    """
    High-level analyzer combining multiple absorption detection methods.
    """

    def __init__(self) -> None:
        """Initialize the absorption analyzer."""
        self.detector = AbsorptionDetector()

    def analyze_bar(self, bar_data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze a bar for all absorption patterns.

        Args:
            bar_data: Bar data including volumes and prices.

        Returns:
            Comprehensive absorption analysis.
        """
        # Run candle-based detection
        candle_absorption = self.detector.detect_absorption(
            buy_volume=bar_data.get("buy_volume", 0),
            sell_volume=bar_data.get("sell_volume", 0),
            price_open=bar_data.get("open", 0),
            price_close=bar_data.get("close", 0),
            price_high=bar_data.get("high", 0),
            price_low=bar_data.get("low", 0),
            timestamp=bar_data.get("timestamp", 0),
        )

        # Run footprint-based detection if available
        footprint_absorption = {}
        if "levels" in bar_data:
            footprint_absorption = self.detector.analyze_footprint_absorption(
                levels=bar_data["levels"],
                candle_open=bar_data.get("open", 0),
                candle_close=bar_data.get("close", 0),
                candle_high=bar_data.get("high", 0),
                candle_low=bar_data.get("low", 0),
                timestamp=bar_data.get("timestamp", 0),
            )

        # Combine results
        combined_detected = candle_absorption.absorption_detected or footprint_absorption.get("absorption", False)
        combined_type = candle_absorption.absorption_type if candle_absorption.absorption_type != "none" else footprint_absorption.get("type", "none")

        return {
            "absorption_detected": combined_detected,
            "absorption_type": combined_type,
            "strength": candle_absorption.strength,
            "candle_absorption": {
                "detected": candle_absorption.absorption_detected,
                "type": candle_absorption.absorption_type,
                "strength": candle_absorption.strength,
            },
            "footprint_absorption": footprint_absorption,
            "valid_signal": self.detector.is_absorption_valid(candle_absorption),
        }

