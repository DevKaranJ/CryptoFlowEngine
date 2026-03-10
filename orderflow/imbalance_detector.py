"""
Imbalance Detector - Detects buy/sell imbalances in the market.

An imbalance occurs when there's a significant difference between
buy and sell volume at specific price levels or time periods.

This module detects:
- Single-level imbalances
- Stacked imbalances (consecutive levels with same imbalance)
- Time-based imbalances
"""

from collections import deque
from dataclasses import dataclass
from typing import Any

from config import get_settings
from core.logging_config import get_logger

logger = get_logger("orderflow.imbalance")


@dataclass
class ImbalanceData:
    """Represents imbalance data at a price level."""

    price: float
    buy_volume: float
    sell_volume: float
    ratio: float
    imbalance_type: str  # "buy", "sell", "balanced"

    @property
    def is_significant(self) -> bool:
        """Check if imbalance is significant based on threshold."""
        settings = get_settings()
        return abs(self.ratio) >= settings.orderflow.imbalance_threshold


class ImbalanceDetector:
    """
    Detects buy/sell imbalances in orderflow data.

    Analyzes footprint data and trade flows to identify significant
    imbalances that may indicate institutional activity.
    """

    def __init__(self) -> None:
        """Initialize the imbalance detector."""
        self.settings = get_settings()
        self._imbalance_history: deque[dict[str, Any]] = deque(maxlen=500)
        self._stacked_imbalance_count: int = 0
        self._current_imbalance_type: str = "balanced"

    def detect_level_imbalance(
        self,
        buy_volume: float,
        sell_volume: float
    ) -> ImbalanceData:
        """
        Detect imbalance at a single price level.

        Args:
            buy_volume: Buy volume at the level.
            sell_volume: Sell volume at the level.

        Returns:
            ImbalanceData with ratio and type.
        """
        if sell_volume == 0:
            ratio = float("inf") if buy_volume > 0 else 1.0
            imbalance_type = "buy" if ratio >= self.settings.orderflow.imbalance_threshold else "balanced"
        elif buy_volume == 0:
            ratio = 0.0
            imbalance_type = "sell"
        else:
            ratio = buy_volume / sell_volume
            if ratio >= self.settings.orderflow.imbalance_threshold:
                imbalance_type = "buy"
            elif ratio <= (1 / self.settings.orderflow.imbalance_threshold):
                imbalance_type = "sell"
            else:
                imbalance_type = "balanced"

        return ImbalanceData(
            price=0.0,  # Price not set for level-only detection
            buy_volume=buy_volume,
            sell_volume=sell_volume,
            ratio=ratio,
            imbalance_type=imbalance_type,
        )

    def analyze_footprint_levels(self, levels: dict[float, dict[str, float]]) -> dict[str, Any]:
        """
        Analyze footprint levels for imbalances.

        Args:
            levels: Dictionary mapping price to {buy_volume, sell_volume}.

        Returns:
            Dictionary with imbalance analysis results.
        """
        if not levels:
            return {
                "buy_imbalance_levels": [],
                "sell_imbalance_levels": [],
                "stacked_buy": False,
                "stacked_sell": False,
                "imbalance_count": 0,
            }

        buy_imbalances = []
        sell_imbalances = []
        sorted_prices = sorted(levels.keys())

        for price in sorted_prices:
            level_data = levels[price]
            imbalance = self.detect_level_imbalance(
                level_data.get("buy_volume", 0),
                level_data.get("sell_volume", 0)
            )

            if imbalance.imbalance_type == "buy":
                buy_imbalances.append({"price": price, "ratio": imbalance.ratio})
            elif imbalance.imbalance_type == "sell":
                sell_imbalances.append({"price": price, "ratio": imbalance.ratio})

        # Detect stacked imbalances
        stacked_buy = self._detect_stacked(buy_imbalances)
        stacked_sell = self._detect_stacked(sell_imbalances)

        result = {
            "buy_imbalance_levels": buy_imbalances,
            "sell_imbalance_levels": sell_imbalances,
            "stacked_buy": stacked_buy,
            "stacked_sell": stacked_sell,
            "total_buy_imbalances": len(buy_imbalances),
            "total_sell_imbalances": len(sell_imbalances),
        }

        # Update state
        if stacked_buy:
            self._current_imbalance_type = "buy"
            self._stacked_imbalance_count += 1
        elif stacked_sell:
            self._current_imbalance_type = "sell"
            self._stacked_imbalance_count += 1
        else:
            self._current_imbalance_type = "balanced"

        return result

    def _detect_stacked(self, imbalance_levels: list[dict[str, Any]]) -> bool:
        """
        Detect if there are stacked imbalances (consecutive levels).

        Args:
            imbalance_levels: List of levels with imbalance.

        Returns:
            True if stacked imbalance detected.
        """
        if len(imbalance_levels) < self.settings.orderflow.stacked_imbalance_levels:
            return False

        # Check if there are enough consecutive levels
        # Sort by price and check for proximity
        prices = sorted([level["price"] for level in imbalance_levels])

        consecutive_count = 1
        max_consecutive = 1

        # Calculate average price step
        if len(prices) > 1:
            avg_step = (prices[-1] - prices[0]) / (len(prices) - 1)
        else:
            avg_step = 0

        for i in range(1, len(prices)):
            if avg_step > 0 and (prices[i] - prices[i-1]) <= avg_step * 1.5:
                consecutive_count += 1
                max_consecutive = max(max_consecutive, consecutive_count)
            else:
                consecutive_count = 1

        return max_consecutive >= self.settings.orderflow.stacked_imbalance_levels

    def detect_time_imbalance(
        self,
        buy_volume: float,
        sell_volume: float,
        threshold: float | None = None
    ) -> dict[str, Any]:
        """
        Detect time-based imbalance (over a time period).

        Args:
            buy_volume: Total buy volume in period.
            sell_volume: Total sell volume in period.
            threshold: Custom threshold (uses config if None).

        Returns:
            Dictionary with imbalance details.
        """
        if threshold is None:
            threshold = self.settings.orderflow.imbalance_threshold

        total = buy_volume + sell_volume
        if total == 0:
            return {
                "imbalance": False,
                "type": "balanced",
                "ratio": 1.0,
                "buy_volume": 0,
                "sell_volume": 0,
            }

        ratio = buy_volume / sell_volume if sell_volume > 0 else float("inf")

        if ratio >= threshold:
            imbalance_type = "buy"
            is_imbalance = True
        elif ratio <= (1 / threshold):
            imbalance_type = "sell"
            is_imbalance = True
        else:
            imbalance_type = "balanced"
            is_imbalance = False

        return {
            "imbalance": is_imbalance,
            "type": imbalance_type,
            "ratio": ratio if ratio != float("inf") else 999999,
            "buy_volume": buy_volume,
            "sell_volume": sell_volume,
            "total_volume": total,
            "buy_percent": (buy_volume / total) * 100,
        }

    def get_imbalance_strength(self, levels: list[dict[str, Any]]) -> float:
        """
        Calculate overall imbalance strength.

        Args:
            levels: List of imbalance levels with ratios.

        Returns:
            Strength value from -1 (strong sell) to 1 (strong buy).
        """
        if not levels:
            return 0.0

        # Calculate weighted average ratio
        total_weight = 0.0
        weighted_sum = 0.0

        for level in levels:
            ratio = level.get("ratio", 1.0)
            # Convert ratio to a -1 to 1 scale
            if ratio == float("inf"):
                normalized = 1.0
            elif ratio == 0:
                normalized = -1.0
            else:
                # Log scale for better handling of large ratios
                normalized = (ratio - 1) / (ratio + 1)

            weight = level.get("volume", 1.0)
            weighted_sum += normalized * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return weighted_sum / total_weight

    def record_imbalance_event(self, imbalance_data: dict[str, Any]) -> None:
        """
        Record an imbalance event for history tracking.

        Args:
            imbalance_data: Dictionary with imbalance details.
        """
        self._imbalance_history.append(imbalance_data)

        if imbalance_data.get("stacked"):
            logger.debug(
                f"Stacked imbalance recorded: {imbalance_data.get('type')} "
                f"at {imbalance_data.get('price_levels', [])}"
            )

    def get_imbalance_history(self, count: int = 50) -> list[dict[str, Any]]:
        """
        Get recent imbalance history.

        Args:
            count: Number of events to return.

        Returns:
            List of recent imbalance events.
        """
        return list(self._imbalance_history)[-count:]

    def get_stacked_imbalance_count(self) -> int:
        """
        Get count of stacked imbalances in current sequence.

        Returns:
            Number of consecutive stacked imbalances.
        """
        return self._stacked_imbalance_count

    def analyze_market(self, market_data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze market data for imbalances.

        This method provides a standardized interface for the websocket
        dispatcher to call during market analysis.

        Args:
            market_data: Dictionary containing:
                - price: Current price
                - volume: Total volume
                - buy_volume: Buy volume (optional)
                - sell_volume: Sell volume (optional)
                - delta: Volume delta (optional)
                - cvd: Cumulative volume delta (optional)
                - levels: Footprint levels dictionary (optional)

        Returns:
            Dictionary with imbalance analysis results including:
                - detected: Whether imbalance was detected
                - type: "buy", "sell", or "balanced"
                - stacked: Whether stacked imbalance detected
                - ratio: Imbalance ratio
                - buy_volume: Total buy volume
                - sell_volume: Total sell volume
        """
        price = market_data.get("price", 0)
        volume = market_data.get("volume", 0)
        
        # Get or estimate buy/sell volumes
        buy_volume = market_data.get("buy_volume")
        sell_volume = market_data.get("sell_volume")
        delta = market_data.get("delta", 0)
        
        if buy_volume is None or sell_volume is None:
            # Estimate from delta if not provided
            # delta = buy_volume - sell_volume
            # volume = buy_volume + sell_volume
            # Solving: buy_volume = (volume + delta) / 2, sell_volume = (volume - delta) / 2
            buy_volume = (volume + delta) / 2
            sell_volume = (volume - delta) / 2
        
        # Get footprint levels if provided
        levels = market_data.get("levels", {})
        
        # Run time-based imbalance detection
        time_imbalance = self.detect_time_imbalance(buy_volume, sell_volume)
        
        # Run footprint level analysis if levels provided
        level_analysis = {}
        if levels:
            level_analysis = self.analyze_footprint_levels(levels)
        
        # Determine overall imbalance type
        imbalance_type = "balanced"
        if time_imbalance.get("imbalance"):
            imbalance_type = time_imbalance.get("type", "balanced")
        elif level_analysis.get("stacked_buy"):
            imbalance_type = "buy"
        elif level_analysis.get("stacked_sell"):
            imbalance_type = "sell"
        
        # Determine if stacked
        is_stacked = level_analysis.get("stacked_buy", False) or level_analysis.get("stacked_sell", False)
        
        # Calculate overall ratio
        ratio = time_imbalance.get("ratio", 1.0)
        
        result = {
            "detected": time_imbalance.get("imbalance", False) or is_stacked,
            "type": imbalance_type,
            "stacked": is_stacked,
            "ratio": ratio,
            "buy_volume": buy_volume,
            "sell_volume": sell_volume,
            "total_volume": volume,
            "buy_percent": time_imbalance.get("buy_percent", 50),
            "stacked_buy": level_analysis.get("stacked_buy", False),
            "stacked_sell": level_analysis.get("stacked_sell", False),
            "buy_imbalance_count": level_analysis.get("total_buy_imbalances", 0),
            "sell_imbalance_count": level_analysis.get("total_sell_imbalances", 0),
        }
        
        # Update state
        if is_stacked:
            self._current_imbalance_type = imbalance_type
            self._stacked_imbalance_count += 1
        
        # Record event
        self.record_imbalance_event(result)
        
        return result

    def analyze_bar(self, bar_data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze a bar for imbalances.

        This method provides a simplified interface for analyzing bar data
        when only basic market metrics are available.

        Args:
            bar_data: Dictionary containing:
                - price: Current price
                - volume: Total volume
                - delta: Volume delta (optional)
                - cvd: Cumulative volume delta (optional)
                - buy_volume: Buy volume (optional)
                - sell_volume: Sell volume (optional)
                - timestamp: Current timestamp (optional)

        Returns:
            Dictionary with imbalance analysis results.
        """
        import time
        
        # Extract data from bar_data
        price = bar_data.get("price", 0)
        volume = bar_data.get("volume", 0)
        delta = bar_data.get("delta", 0)
        
        # Get or estimate buy/sell volumes
        buy_volume = bar_data.get("buy_volume")
        sell_volume = bar_data.get("sell_volume")
        
        if buy_volume is None or sell_volume is None:
            # Estimate from delta if not provided
            buy_volume = (volume + delta) / 2
            sell_volume = (volume - delta) / 2
        
        # Run time-based imbalance detection
        time_imbalance = self.detect_time_imbalance(buy_volume, sell_volume)
        
        # Get strength
        imbalance_levels = []
        if time_imbalance.get("imbalance"):
            imbalance_levels = [{"ratio": time_imbalance.get("ratio", 1.0), "volume": volume}]
        
        strength = self.get_imbalance_strength(imbalance_levels)
        
        return {
            "detected": time_imbalance.get("imbalance", False),
            "type": time_imbalance.get("type", "balanced"),
            "ratio": time_imbalance.get("ratio", 1.0),
            "buy_volume": buy_volume,
            "sell_volume": sell_volume,
            "total_volume": volume,
            "buy_percent": time_imbalance.get("buy_percent", 50),
            "strength": strength,
        }

    def reset(self) -> None:
        """Reset the imbalance detector state."""
        self._imbalance_history.clear()
        self._stacked_imbalance_count = 0
        self._current_imbalance_type = "balanced"
        logger.info("Imbalance detector reset")


class OrderflowImbalanceAnalyzer:
    """
    High-level analyzer for orderflow imbalances.

    Combines multiple imbalance detection methods for
    comprehensive market analysis.
    """

    def __init__(self) -> None:
        """Initialize the orderflow imbalance analyzer."""
        self.detector = ImbalanceDetector()

    def analyze_bar(self, bar_data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze a complete bar for imbalances.

        Args:
            bar_data: Bar data with levels, volumes, etc.

        Returns:
            Comprehensive imbalance analysis.
        """
        levels = bar_data.get("levels", {})

        # Analyze footprint levels
        level_analysis = self.detector.analyze_footprint_levels(levels)

        # Get time-based imbalance
        buy_vol = bar_data.get("buy_volume", 0)
        sell_vol = bar_data.get("sell_volume", 0)
        time_imbalance = self.detector.detect_time_imbalance(buy_vol, sell_vol)

        # Calculate strength
        all_imbalances = level_analysis["buy_imbalance_levels"] + level_analysis["sell_imbalance_levels"]
        strength = self.detector.get_imbalance_strength(all_imbalances)

        return {
            "has_imbalance": level_analysis["total_buy_imbalances"] > 0 or level_analysis["total_sell_imbalances"] > 0,
            "imbalance_type": "buy" if level_analysis["total_buy_imbalances"] > level_analysis["total_sell_imbalances"] else "sell",
            "stacked_buy": level_analysis["stacked_buy"],
            "stacked_sell": level_analysis["stacked_sell"],
            "buy_imbalance_count": level_analysis["total_buy_imbalances"],
            "sell_imbalance_count": level_analysis["total_sell_imbalances"],
            "time_imbalance": time_imbalance,
            "strength": strength,
            "buy_levels": level_analysis["buy_imbalance_levels"],
            "sell_levels": level_analysis["sell_imbalance_levels"],
        }

    def detect_recent_imbalance_shift(self, lookback: int = 5) -> tuple[bool, str]:
        """
        Detect recent shift in imbalance (e.g., buy to sell).

        Args:
            lookback: Number of bars to look back.

        Returns:
            Tuple of (is_shift, direction).
        """
        history = self.detector.get_imbalance_history(lookback)
        if len(history) < 2:
            return False, ""

        recent_type = history[-1].get("type", "balanced")
        previous_type = history[-2].get("type", "balanced")

        if recent_type != previous_type and recent_type != "balanced":
            return True, recent_type

        return False, ""

