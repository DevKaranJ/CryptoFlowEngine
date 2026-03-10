"""
Liquidity Engine - Detects liquidity walls and liquidity zones.

Liquidity refers to areas of stop orders or limit orders that can
absorb market orders. This module detects:

- Liquidity walls (large limit order clusters)
- Liquidity zones (areas with concentrated volume)
- Stop hunt zones (areas where stops are likely clustered)
- Fair value gaps (imbalance between high and low)
"""

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any

from config import get_settings
from core.logging_config import get_logger

logger = get_logger("orderflow.liquidity")


@dataclass
class LiquidityLevel:
    """Represents a liquidity level."""

    price: float
    volume: float
    level_type: str  # "bid", "ask", "stop_buy", "stop_sell"
    strength: float  # 0 to 1


@dataclass
class LiquidityZone:
    """Represents a liquidity zone (range of prices)."""

    low: float
    high: float
    volume: float
    zone_type: str
    strength: float


class LiquidityEngine:
    """
    Detects liquidity walls and zones in the market.

    Analyzes orderbook, volume profile, and trade data to identify
    areas of significant liquidity.
    """

    def __init__(self) -> None:
        """Initialize the liquidity engine."""
        self.settings = get_settings()
        self._liquidity_history: deque[dict[str, Any]] = deque(maxlen=500)
        self._current_walls: dict[str, list[LiquidityLevel]] = {
            "bid": [],
            "ask": [],
        }

    def detect_orderbook_walls(
        self,
        bids: list[tuple[float, float]],
        asks: list[tuple[float, float]],
        wall_threshold: float = 10.0  # Multiplier over average
    ) -> dict[str, Any]:
        """
        Detect liquidity walls from orderbook data.

        Args:
            bids: List of (price, quantity) tuples for bids.
            asks: List of (price, quantity) tuples for asks.
            wall_threshold: Multiplier over average to qualify as wall.

        Returns:
            Dictionary with detected walls.
        """
        # Calculate average volume
        avg_bid_vol = sum(qty for _, qty in bids) / len(bids) if bids else 0
        avg_ask_vol = sum(qty for _, qty in asks) / len(asks) if asks else 0

        bid_walls = []
        ask_walls = []

        # Detect bid walls (large buy orders)
        for price, qty in bids:
            if qty >= avg_bid_vol * wall_threshold:
                wall = LiquidityLevel(
                    price=price,
                    volume=qty,
                    level_type="bid",
                    strength=min(1.0, qty / (avg_bid_vol * wall_threshold))
                )
                bid_walls.append(wall)

        # Detect ask walls (large sell orders)
        for price, qty in asks:
            if qty >= avg_ask_vol * wall_threshold:
                wall = LiquidityLevel(
                    price=price,
                    volume=qty,
                    level_type="ask",
                    strength=min(1.0, qty / (avg_ask_vol * wall_threshold))
                )
                ask_walls.append(wall)

        self._current_walls["bid"] = bid_walls
        self._current_walls["ask"] = ask_walls

        return {
            "bid_walls": [
                {"price": w.price, "volume": w.volume, "strength": w.strength}
                for w in bid_walls
            ],
            "ask_walls": [
                {"price": w.price, "volume": w.volume, "strength": w.strength}
                for w in ask_walls
            ],
            "total_bid_liquidity": sum(w.volume for w in bid_walls),
            "total_ask_liquidity": sum(w.volume for w in ask_walls),
        }

    def detect_volume_profile_zones(
        self,
        volume_profile: dict[float, float],
        total_volume: float,
        zone_percent: float = 0.7
    ) -> dict[str, Any]:
        """
        Detect liquidity zones from volume profile.

        Args:
            volume_profile: Dictionary mapping price to volume.
            total_volume: Total volume for normalization.
            zone_percent: Percentage of volume to include in value area.

        Returns:
            Dictionary with detected zones.
        """
        if not volume_profile:
            return {
                "value_area_low": 0.0,
                "value_area_high": 0.0,
                "poc": 0.0,
                "poc_volume": 0.0,
                "zones": [],
            }

        # Sort by volume
        sorted_levels = sorted(
            volume_profile.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Find POC (Point of Control - highest volume)
        poc_price = sorted_levels[0][0]
        poc_volume = sorted_levels[0][1]

        # Calculate Value Area
        total_profile_vol = sum(v for _, v in sorted_levels)
        target_vol = total_profile_vol * zone_percent

        cumsum = 0
        value_area_prices = []
        for price, vol in sorted_levels:
            cumsum += vol
            value_area_prices.append(price)
            if cumsum >= target_vol:
                break

        value_area_low = min(value_area_prices) if value_area_prices else 0
        value_area_high = max(value_area_prices) if value_area_prices else 0

        # Detect high liquidity zones (clusters)
        zones = self._find_liquidity_clusters(volume_profile)

        return {
            "value_area_low": value_area_low,
            "value_area_high": value_area_high,
            "poc": poc_price,
            "poc_volume": poc_volume,
            "value_area_volume": cumsum,
            "zones": zones,
        }

    def _find_liquidity_clusters(
        self,
        volume_profile: dict[float, float],
        min_cluster_size: int = 3
    ) -> list[dict[str, Any]]:
        """
        Find clusters of high liquidity in the profile.

        Args:
            volume_profile: Volume profile dictionary.
            min_cluster_size: Minimum consecutive levels for a cluster.

        Returns:
            List of detected liquidity clusters.
        """
        if not volume_profile:
            return []

        # Calculate average and std deviation
        volumes = list(volume_profile.values())
        if not volumes:
            return []

        avg_vol = sum(volumes) / len(volumes)

        # Find above-average levels
        sorted_prices = sorted(volume_profile.keys())
        high_vol_prices = [
            p for p in sorted_prices
            if volume_profile[p] > avg_vol * 1.5
        ]

        if not high_vol_prices:
            return []

        # Find clusters
        clusters = []
        current_cluster = [high_vol_prices[0]]

        for i in range(1, len(high_vol_prices)):
            price_diff = high_vol_prices[i] - high_vol_prices[i-1]
            # Assuming similar tick sizes, if prices are close, they're a cluster
            if price_diff < avg_vol * 2:  # Adaptive threshold
                current_cluster.append(high_vol_prices[i])
            else:
                if len(current_cluster) >= min_cluster_size:
                    total_vol = sum(volume_profile[p] for p in current_cluster)
                    clusters.append({
                        "low": min(current_cluster),
                        "high": max(current_cluster),
                        "mid": (min(current_cluster) + max(current_cluster)) / 2,
                        "volume": total_vol,
                        "levels": len(current_cluster),
                    })
                current_cluster = [high_vol_prices[i]]

        # Handle last cluster
        if len(current_cluster) >= min_cluster_size:
            total_vol = sum(volume_profile[p] for p in current_cluster)
            clusters.append({
                "low": min(current_cluster),
                "high": max(current_cluster),
                "mid": (min(current_cluster) + max(current_cluster)) / 2,
                "volume": total_vol,
                "levels": len(current_cluster),
            })

        return clusters

    def detect_stop_zones(
        self,
        recent_swings: list[dict[str, Any]],
        current_price: float,
        swing_lookback: int = 20
    ) -> dict[str, Any]:
        """
        Detect likely stop hunt zones based on recent swing highs/lows.

        Args:
            recent_swings: List of recent swing highs/lows.
            current_price: Current market price.
            swing_lookback: How many swings to consider.

        Returns:
            Dictionary with stop zone analysis.
        """
        if not recent_swings:
            return {
                "stop_buy_zone": None,
                "stop_sell_zone": None,
                "nearest_stop_buy": None,
                "nearest_stop_sell": None,
            }

        # Extract swing highs and lows
        swing_highs = [
            s["price"] for s in recent_swings[-swing_lookback:]
            if s.get("type") == "high"
        ]
        swing_lows = [
            s["price"] for s in recent_swings[-swing_lookback:]
            if s.get("type") == "low"
        ]

        # Find clusters of swing levels (likely stop zones)
        stop_buy_zone = self._find_stop_cluster(swing_lows, "below")
        stop_sell_zone = self._find_stop_cluster(swing_highs, "above")

        # Find nearest stops
        nearest_stop_buy = None
        if swing_lows:
            below_prices = [p for p in swing_lows if p < current_price]
            if below_prices:
                nearest_stop_buy = max(below_prices)

        nearest_stop_sell = None
        if swing_highs:
            above_prices = [p for p in swing_highs if p > current_price]
            if above_prices:
                nearest_stop_sell = min(above_prices)

        return {
            "stop_buy_zone": stop_buy_zone,
            "stop_sell_zone": stop_sell_zone,
            "nearest_stop_buy": nearest_stop_buy,
            "nearest_stop_sell": nearest_stop_sell,
            "buy_liquidity_distance": current_price - nearest_stop_buy if nearest_stop_buy else None,
            "sell_liquidity_distance": nearest_stop_sell - current_price if nearest_stop_sell else None,
        }

    def _find_stop_cluster(
        self,
        levels: list[float],
        direction: str  # "above" or "below"
    ) -> dict[str, Any] | None:
        """
        Find a cluster of levels (likely stop zone).

        Args:
            levels: List of price levels.
            direction: Direction to look for cluster.

        Returns:
            Cluster info or None.
        """
        if len(levels) < 3:
            return None

        # Sort and find gaps
        sorted_levels = sorted(levels)
        clusters = []
        current = [sorted_levels[0]]

        for i in range(1, len(sorted_levels)):
            # Calculate typical gap
            gap = sorted_levels[i] - sorted_levels[i-1]
            avg_price = sum(sorted_levels) / len(sorted_levels)
            relative_gap = gap / avg_price

            # If gap is > 0.5% of price, start new cluster
            if relative_gap > 0.005:
                if len(current) >= 2:
                    clusters.append(current)
                current = [sorted_levels[i]]
            else:
                current.append(sorted_levels[i])

        if len(current) >= 2:
            clusters.append(current)

        if not clusters:
            return None

        # Return the cluster closest to current price
        if direction == "below":
            # Looking for buy stops (below current)
            valid_clusters = [c for c in clusters if c[-1] < levels[0]] if levels else []
        else:
            # Looking for sell stops (above current)
            valid_clusters = [c for c in clusters if c[0] > levels[0]] if levels else []

        if valid_clusters:
            cluster = valid_clusters[0]
            return {
                "low": min(cluster),
                "high": max(cluster),
                "mid": (min(cluster) + max(cluster)) / 2,
                "count": len(cluster),
            }

        return None

    def detect_fvg(
        self,
        candles: list[dict[str, Any]],
        fvg_threshold: float = 0.5  # % of candle size
    ) -> list[dict[str, Any]]:
        """
        Detect Fair Value Gaps (FVG).

        A FVG occurs when there's an imbalance between candles:
        - Bullish FVG: current low > previous high (gap up)
        - Bearish FVG: current high < previous low (gap down)

        Args:
            candles: List of candle data.
            fvg_threshold: Minimum gap size as percentage.

        Returns:
            List of detected FVGs.
        """
        if len(candles) < 3:
            return []

        fvgs = []

        for i in range(2, len(candles)):
            current = candles[i]
            prev = candles[i-1]
            prev2 = candles[i-2]

            current_low = current.get("low", 0)
            current_high = current.get("high", 0)
            prev_low = prev.get("low", 0)
            prev_high = prev.get("high", 0)
            prev2_low = prev2.get("low", 0)
            prev2_high = prev2.get("high", 0)

            # Bullish FVG: gap up between prev low and current/prev2
            if prev_low > prev2_high:
                gap_size = prev_low - prev2_high
                avg_range = (current_high - current_low + prev_high - prev_low) / 2
                if gap_size > avg_range * fvg_threshold:
                    fvgs.append({
                        "type": "bullish",
                        "gap_low": prev2_high,
                        "gap_high": prev_low,
                        "gap_mid": (prev2_high + prev_low) / 2,
                        "gap_size": gap_size,
                        "candle_index": i,
                    })

            # Bearish FVG: gap down between prev high and current/prev2
            elif prev_high < prev2_low:
                gap_size = prev2_low - prev_high
                avg_range = (current_high - current_low + prev_high - prev_low) / 2
                if gap_size > avg_range * fvg_threshold:
                    fvgs.append({
                        "type": "bearish",
                        "gap_low": prev_high,
                        "gap_high": prev2_low,
                        "gap_mid": (prev_high + prev2_low) / 2,
                        "gap_size": gap_size,
                        "candle_index": i,
                    })

        return fvgs

    def get_nearest_liquidity(
        self,
        current_price: float,
        bid_walls: list[dict[str, Any]],
        ask_walls: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Get nearest liquidity levels to current price.

        Args:
            current_price: Current market price.
            bid_walls: List of bid liquidity levels.
            ask_walls: List of ask liquidity levels.

        Returns:
            Dictionary with nearest liquidity info.
        """
        nearest_bid = None
        nearest_ask = None

        if bid_walls:
            bid_prices = [w["price"] for w in bid_walls]
            below_bids = [p for p in bid_prices if p < current_price]
            if below_bids:
                nearest_bid = max(below_bids)

        if ask_walls:
            ask_prices = [w["price"] for w in ask_walls]
            above_asks = [p for p in ask_prices if p > current_price]
            if above_asks:
                nearest_ask = min(above_asks)

        return {
            "nearest_bid_liquidity": nearest_bid,
            "nearest_ask_liquidity": nearest_ask,
            "bid_distance": current_price - nearest_bid if nearest_bid else None,
            "ask_distance": nearest_ask - current_price if nearest_ask else None,
            "liquidity_span": nearest_ask - nearest_bid if nearest_bid and nearest_ask else None,
        }

    def record_liquidity_event(self, event_data: dict[str, Any]) -> None:
        """
        Record a liquidity event for history.

        Args:
            event_data: Liquidity event details.
        """
        self._liquidity_history.append(event_data)

    def get_liquidity_history(self, count: int = 50) -> list[dict[str, Any]]:
        """
        Get recent liquidity history.

        Args:
            count: Number of events to return.

        Returns:
            List of recent liquidity events.
        """
        return list(self._liquidity_history)[-count:]

    def reset(self) -> None:
        """Reset the liquidity engine state."""
        self._liquidity_history.clear()
        self._current_walls = {"bid": [], "ask": []}
        logger.info("Liquidity engine reset")


class OrderflowLiquidityAnalyzer:
    """
    High-level analyzer for orderflow liquidity.
    """

    def __init__(self) -> None:
        """Initialize the liquidity analyzer."""
        self.engine = LiquidityEngine()

    def analyze_market(self, market_data: dict[str, Any]) -> dict[str, Any]:
        """
        Perform comprehensive liquidity analysis.

        Args:
            market_data: Market data including orderbook, volume profile, etc.

        Returns:
            Comprehensive liquidity analysis.
        """
        result = {}

        # Orderbook walls
        if "bids" in market_data and "asks" in market_data:
            result["orderbook_walls"] = self.engine.detect_orderbook_walls(
                bids=market_data["bids"],
                asks=market_data["asks"],
            )

        # Volume profile zones
        if "volume_profile" in market_data:
            result["volume_zones"] = self.engine.detect_volume_profile_zones(
                volume_profile=market_data["volume_profile"],
                total_volume=market_data.get("total_volume", 0),
            )

        # FVGs
        if "candles" in market_data:
            result["fvgs"] = self.engine.detect_fvg(
                candles=market_data["candles"],
            )

        return result

