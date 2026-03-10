"""
Zone Detector - Detects support and resistance zones.

This module identifies key price zones based on:
- Volume Profile (VAH, VAL, POC)
- Recent swing highs/lows
- Historical price clusters
- Round numbers and psychological levels
"""

from collections import deque
from dataclasses import dataclass
from typing import Any

from config import get_settings
from core.logging_config import get_logger

logger = get_logger("strategy.zones")


@dataclass
class Zone:
    """Represents a price zone."""

    low: float
    high: float
    zone_type: str  # "support", "resistance", "value_area"
    strength: float  # 0 to 1
    touches: int  # Number of times price tested this zone
    source: str  # How zone was identified


class ZoneDetector:
    """
    Detects support and resistance zones.

    Uses multiple methods to identify key price levels where
    the market has shown reaction in the past.
    """

    def __init__(self) -> None:
        """Initialize the zone detector."""
        self.settings = get_settings()
        self._zones: deque[Zone] = deque(maxlen=100)
        self._swing_highs: deque[float] = deque(maxlen=50)
        self._swing_lows: deque[float] = deque(maxlen=50)
        self._poc_history: deque[float] = deque(maxlen=50)
        self._value_area_high: deque[float] = deque(maxlen=50)
        self._value_area_low: deque[float] = deque(maxlen=50)

    def detect_zones_from_candles(
        self,
        candles: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Detect zones from candle data.

        Args:
            candles: List of candle dictionaries with high, low, close, volume.

        Returns:
            Dictionary with detected zones.
        """
        if len(candles) < self.settings.strategy.zone_lookback_candles:
            return {
                "support_zones": [],
                "resistance_zones": [],
                "value_area": {"high": 0, "low": 0, "poc": 0},
            }

        # Extract swing highs and lows
        self._detect_swings(candles)

        # Calculate volume profile zones
        volume_zones = self._calculate_volume_profile_zones(candles)

        # Find congestion zones (price clusters)
        congestion_zones = self._find_congestion_zones(candles)

        # Build support and resistance zones
        support_zones = []
        resistance_zones = []

        # Add swing-based zones
        for low in list(self._swing_lows)[-10:]:
            zone = self._create_zone(low, low * 0.002, "support", "swing")
            support_zones.append(zone)

        for high in list(self._swing_highs)[-10:]:
            zone = self._create_zone(high * 0.002, high, "resistance", "swing")
            resistance_zones.append(zone)

        # Add volume profile zones
        if volume_zones["poc"]:
            # POC as both support and resistance
            pass  # Already tracked in history

        # Add congestion zones
        for zone_data in congestion_zones:
            if zone_data["type"] == "support":
                support_zones.append(zone_data["zone"])
            else:
                resistance_zones.append(zone_data["zone"])

        # Consolidate overlapping zones
        support_zones = self._consolidate_zones(support_zones)
        resistance_zones = self._consolidate_zones(resistance_zones)

        return {
            "support_zones": [
                {"low": z.low, "high": z.high, "strength": z.strength, "touches": z.touches}
                for z in support_zones
            ],
            "resistance_zones": [
                {"low": z.low, "high": z.high, "strength": z.strength, "touches": z.touches}
                for z in resistance_zones
            ],
            "value_area": volume_zones,
            "swing_highs": list(self._swing_highs),
            "swing_lows": list(self._swing_lows),
        }

    def _detect_swings(self, candles: list[dict[str, Any]]) -> None:
        """
        Detect swing highs and lows from candles.

        Args:
            candles: List of candle data.
        """
        lookback = 5  # Look back 5 candles to find swing

        for i in range(lookback, len(candles) - lookback):
            current = candles[i]
            prev_candles = candles[i-lookback:i]
            next_candles = candles[i+1:i+lookback+1]

            current_high = current.get("high", 0)
            current_low = current.get("low", 0)

            # Check for swing high
            is_swing_high = all(c.get("high", 0) <= current_high for c in prev_candles) and \
                           all(c.get("high", 0) < current_high for c in next_candles)

            if is_swing_high:
                if not self._swing_highs or current_high != self._swing_highs[-1]:
                    self._swing_highs.append(current_high)

            # Check for swing low
            is_swing_low = all(c.get("low", 0) >= current_low for c in prev_candles) and \
                          all(c.get("low", 0) > current_low for c in next_candles)

            if is_swing_low:
                if not self._swing_lows or current_low != self._swing_lows[-1]:
                    self._swing_lows.append(current_low)

    def _calculate_volume_profile_zones(
        self,
        candles: list[dict[str, Any]]
    ) -> dict[str, float]:
        """
        Calculate value area from volume profile.

        Args:
            candles: List of candle data.

        Returns:
            Dictionary with VAH, VAL, POC.
        """
        if not candles:
            return {"high": 0, "low": 0, "poc": 0}

        # Group volume by price buckets
        price_buckets: dict[int, float] = {}

        for candle in candles:
            high = candle.get("high", 0)
            low = candle.get("low", 0)
            volume = candle.get("volume", 0)

            if high == low:
                continue

            # Create bucket key (price // tick_size)
            tick_size = high * 0.001  # 0.1% of price
            bucket_low = int(low / tick_size)
            bucket_high = int(high / tick_size)

            # Distribute volume across buckets
            vol_per_bucket = volume / max(1, bucket_high - bucket_low)
            for b in range(bucket_low, bucket_high + 1):
                price_buckets[b] = price_buckets.get(b, 0) + vol_per_bucket

        if not price_buckets:
            return {"high": 0, "low": 0, "poc": 0}

        # Find POC (Point of Control)
        poc_bucket = max(price_buckets.keys(), key=lambda b: price_buckets[b])
        tick_size = candles[0].get("high", 1) * 0.001
        poc = poc_bucket * tick_size

        # Calculate Value Area (70% of volume)
        total_volume = sum(price_buckets.values())
        target_volume = total_volume * 0.7

        sorted_buckets = sorted(price_buckets.items(), key=lambda x: x[1], reverse=True)
        cumsum = 0
        value_buckets = []

        for bucket, vol in sorted_buckets:
            cumsum += vol
            value_buckets.append(bucket)
            if cumsum >= target_volume:
                break

        value_area_low = min(value_buckets) * tick_size if value_buckets else 0
        value_area_high = max(value_buckets) * tick_size if value_buckets else 0

        # Update history
        self._poc_history.append(poc)
        self._value_area_high.append(value_area_high)
        self._value_area_low.append(value_area_low)

        return {
            "high": value_area_high,
            "low": value_area_low,
            "poc": poc,
        }

    def _find_congestion_zones(
        self,
        candles: list[dict[str, Any]],
        tolerance: float = 0.002
    ) -> list[dict[str, Any]]:
        """
        Find congestion zones where price has clustered.

        Args:
            candles: List of candle data.
            tolerance: Price tolerance for clustering (2% default).

        Returns:
            List of congestion zones.
        """
        closes = [c.get("close", 0) for c in candles]
        if not closes:
            return []

        # Find price clusters
        clusters: dict[int, list[float]] = {}
        cluster_threshold = tolerance

        for price in closes:
            found_cluster = False
            for cluster_id in clusters:
                cluster_prices = clusters[cluster_id]
                if cluster_prices:
                    avg_price = sum(cluster_prices) / len(cluster_prices)
                    if abs(price - avg_price) / avg_price < cluster_threshold:
                        cluster_prices.append(price)
                        found_cluster = True
                        break

            if not found_cluster:
                new_id = len(clusters)
                clusters[new_id] = [price]

        # Find significant clusters (>3 touches)
        zones = []
        for cluster_id, cluster_prices in clusters.items():
            if len(cluster_prices) >= 3:
                avg_price = sum(cluster_prices) / len(cluster_prices)
                cluster_low = min(cluster_prices)
                cluster_high = max(cluster_prices)

                # Determine if support or resistance based on current price
                current_price = closes[-1] if closes else avg_price

                if avg_price < current_price:
                    zone_type = "support"
                    zone = self._create_zone(
                        cluster_low,
                        cluster_high,
                        zone_type,
                        "congestion",
                        strength=len(cluster_prices) / 10
                    )
                else:
                    zone_type = "resistance"
                    zone = self._create_zone(
                        cluster_low,
                        cluster_high,
                        zone_type,
                        "congestion",
                        strength=len(cluster_prices) / 10
                    )

                zones.append({
                    "type": zone_type,
                    "zone": zone,
                    "touches": len(cluster_prices),
                })

        return zones

    def _create_zone(
        self,
        low: float,
        high: float,
        zone_type: str,
        source: str,
        strength: float = 0.5,
        touches: int = 1
    ) -> Zone:
        """
        Create a zone object.

        Args:
            low: Zone low price.
            high: Zone high price.
            zone_type: "support" or "resistance".
            source: How zone was identified.
            strength: Zone strength (0-1).
            touches: Number of touches.

        Returns:
            Zone object.
        """
        return Zone(
            low=low,
            high=high,
            zone_type=zone_type,
            strength=min(1.0, strength),
            touches=touches,
            source=source,
        )

    def _consolidate_zones(self, zones: list[Zone]) -> list[Zone]:
        """
        Consolidate overlapping zones.

        Args:
            zones: List of zones to consolidate.

        Returns:
            List of consolidated zones.
        """
        if not zones:
            return []

        # Sort by low price
        sorted_zones = sorted(zones, key=lambda z: z.low)

        consolidated = []
        current = sorted_zones[0]

        for zone in sorted_zones[1:]:
            # Check for overlap
            if zone.low <= current.high * 1.001:  # 0.1% tolerance
                # Merge zones
                new_low = min(current.low, zone.low)
                new_high = max(current.high, zone.high)
                new_touches = current.touches + zone.touches
                new_strength = min(1.0, (current.strength + zone.strength) / 2 + 0.1)

                current = Zone(
                    low=new_low,
                    high=new_high,
                    zone_type=current.zone_type,
                    strength=new_strength,
                    touches=new_touches,
                    source=current.source,
                )
            else:
                consolidated.append(current)
                current = zone

        consolidated.append(current)

        return consolidated

    def is_near_zone(self, price: float, zones: list[dict[str, Any]], tolerance: float = 0.002) -> bool:
        """
        Check if price is near any zone.

        Args:
            price: Current price.
            zones: List of zone dictionaries.
            tolerance: Tolerance as percentage.

        Returns:
            True if price is near a zone.
        """
        for zone in zones:
            low = zone.get("low", 0)
            high = zone.get("high", 0)

            if low <= price <= high:
                return True

            # Check if within tolerance
            if price < low and (low - price) / price < tolerance:
                return True
            if price > high and (price - high) / price < tolerance:
                return True

        return False

    def get_nearest_zone(
        self,
        price: float,
        zones: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        """
        Get the nearest zone to the current price.

        Args:
            price: Current price.
            zones: List of zones.

        Returns:
            Nearest zone info or None.
        """
        if not zones:
            return None

        nearest = None
        min_distance = float("inf")

        for zone in zones:
            zone_mid = (zone.get("low", 0) + zone.get("high", 0)) / 2
            distance = abs(price - zone_mid) / price

            if distance < min_distance:
                min_distance = distance
                nearest = zone

        return nearest

    def get_zones_for_direction(
        self,
        current_price: float,
        direction: str,  # "long" or "short"
        zones: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Get relevant zones for a trade direction.

        Args:
            current_price: Current price.
            direction: "long" or "short".
            zones: All detected zones.

        Returns:
            List of relevant zones.
        """
        if direction == "long":
            # Get support zones below current price
            relevant = [
                z for z in zones.get("support_zones", [])
                if z["high"] < current_price
            ]
            # Sort by proximity to current price
            relevant.sort(key=lambda z: current_price - z["high"], reverse=True)
            return relevant[:3]
        else:
            # Get resistance zones above current price
            relevant = [
                z for z in zones.get("resistance_zones", [])
                if z["low"] > current_price
            ]
            # Sort by proximity to current price
            relevant.sort(key=lambda z: z["low"] - current_price)
            return relevant[:3]

    def reset(self) -> None:
        """Reset the zone detector."""
        self._zones.clear()
        self._swing_highs.clear()
        self._swing_lows.clear()
        self._poc_history.clear()
        self._value_area_high.clear()
        self._value_area_low.clear()
        logger.info("Zone detector reset")

