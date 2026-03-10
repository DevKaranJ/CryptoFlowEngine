"""
Signal Builder - Generates trading signals from strategy components.

This module combines all strategy components to generate
trade signals with entry, stop loss, and take profit levels.

Signal Confidence Scoring:
- Zone confluence: +25 points
- Absorption: +20 points
- CVD divergence: +20 points
- Stacked imbalance: +20 points
- Volume spike: +15 points

Total: 100 points
- >70 = strong trade
- 50-70 = medium
- <50 = ignore
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from config import get_settings
from core.logging_config import get_logger

logger = get_logger("strategy.signal")


class SignalDirection(str, Enum):
    """Signal direction."""

    LONG = "long"
    SHORT = "short"
    NONE = "none"


class SignalStatus(str, Enum):
    """Signal status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    FILLED = "filled"
    CANCELLED = "cancelled"


@dataclass
class TradingSignal:
    """Represents a complete trading signal."""

    id: str | None = None
    timestamp: int = 0
    symbol: str = ""
    direction: SignalDirection = SignalDirection.NONE

    # Entry levels
    entry_price: float = 0.0
    stop_price: float = 0.0
    tp1: float = 0.0
    tp2: float = 0.0
    tp3: float = 0.0

    # Confidence
    confidence: float = 0.0
    confidence_level: str = "low"  # "low", "medium", "high"

    # Reason and context
    reason: list[str] = field(default_factory=list)
    market_context: dict[str, Any] = field(default_factory=dict)

    # Status
    status: SignalStatus = SignalStatus.PENDING

    # Metadata
    strategy: str = "orderflow_reversal"
    timeframe: str = "15m"

    @property
    def risk_reward_ratio(self) -> float:
        """Calculate risk:reward ratio."""
        if self.direction == SignalDirection.LONG:
            reward = self.tp1 - self.entry_price
            risk = self.entry_price - self.stop_price
        elif self.direction == SignalDirection.SHORT:
            reward = self.entry_price - self.tp1
            risk = self.stop_price - self.entry_price
        else:
            return 0.0

        if risk == 0:
            return 0.0

        return reward / risk

    def to_dict(self) -> dict[str, Any]:
        """Convert signal to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "timestamp_str": datetime.fromtimestamp(
                self.timestamp / 1000
            ).strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else "",
            "symbol": self.symbol,
            "direction": self.direction.value,
            "entry_price": self.entry_price,
            "stop_price": self.stop_price,
            "tp1": self.tp1,
            "tp2": self.tp2,
            "tp3": self.tp3,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level,
            "reason": self.reason,
            "status": self.status.value,
            "strategy": self.strategy,
            "timeframe": self.timeframe,
            "risk_reward": self.risk_reward_ratio,
        }


class SignalBuilder:
    """
    Builds trading signals from strategy components.

    Combines zone detection, absorption, CVD, imbalance, and
    initiation detection to generate high-quality signals.
    """

    def __init__(self) -> None:
        """Initialize the signal builder."""
        self.settings = get_settings()
        self._signal_history: list[TradingSignal] = []

    def build_signal(
        self,
        symbol: str,
        direction: SignalDirection,
        entry_price: float,
        market_data: dict[str, Any],
        strategy_components: dict[str, Any]
    ) -> TradingSignal:
        """
        Build a complete trading signal.

        Args:
            symbol: Trading symbol.
            direction: Signal direction.
            entry_price: Entry price.
            market_data: Current market data.
            strategy_components: Results from strategy components.

        Returns:
            Complete TradingSignal.
        """
        # Calculate confidence score
        confidence, reasons = self._calculate_confidence(
            direction=direction,
            strategy_components=strategy_components,
        )

        # Determine confidence level
        if confidence >= self.settings.strategy.strong_confidence:
            confidence_level = "high"
        elif confidence >= self.settings.strategy.min_confidence:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        # Calculate stop loss and take profits
        stop_price = self._calculate_stop_loss(
            entry_price=entry_price,
            direction=direction,
            market_data=market_data,
            strategy_components=strategy_components,
        )

        tp_levels = self._calculate_take_profits(
            entry_price=entry_price,
            stop_price=stop_price,
            direction=direction,
        )

        # Create signal
        signal = TradingSignal(
            id=self._generate_signal_id(),
            timestamp=int(datetime.now().timestamp() * 1000),
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            stop_price=stop_price,
            tp1=tp_levels["tp1"],
            tp2=tp_levels["tp2"],
            tp3=tp_levels["tp3"],
            confidence=confidence,
            confidence_level=confidence_level,
            reason=reasons,
            market_context={
                "price": market_data.get("current_price", 0),
                "cvd": market_data.get("cvd", 0),
                "delta": market_data.get("delta", 0),
                "volume": market_data.get("volume", 0),
            },
            strategy="orderflow_reversal",
        )

        # Validate signal
        if not self._validate_signal(signal):
            logger.warning(f"Signal validation failed for {symbol}")

        self._signal_history.append(signal)

        logger.info(
            f"Signal generated: {signal.direction.value} {symbol} "
            f"@ {signal.entry_price} | "
            f"SL: {signal.stop_price} | "
            f"TP1: {signal.tp1} | "
            f"Confidence: {signal.confidence}% ({signal.confidence_level})"
        )

        return signal

    def _generate_signal_id(self) -> str:
        """Generate unique signal ID."""
        import uuid
        return f"SIG-{uuid.uuid4().hex[:8].upper()}"

    def _calculate_confidence(
        self,
        direction: SignalDirection,
        strategy_components: dict[str, Any]
    ) -> tuple[float, list[str]]:
        """
        Calculate signal confidence score.

        Args:
            direction: Signal direction.
            strategy_components: Results from strategy components.

        Returns:
            Tuple of (confidence, reasons).
        """
        confidence = 0.0
        reasons = []

        components = strategy_components.get("components", {})

        # Zone confluence (+25)
        zones = components.get("zones", {})
        if zones.get("near_support") and direction == SignalDirection.LONG:
            confidence += 25
            reasons.append("Near support zone")
        elif zones.get("near_resistance") and direction == SignalDirection.SHORT:
            confidence += 25
            reasons.append("Near resistance zone")

        # Absorption (+20)
        absorption = components.get("absorption", {})
        if absorption.get("detected"):
            confidence += 20
            reasons.append(f"Absorption detected ({absorption.get('type', 'unknown')})")

        # CVD divergence (+20)
        cvd = components.get("cvd_divergence", {})
        if cvd.get("detected"):
            confidence += 20
            reasons.append(f"CVD {cvd.get('type')} divergence")

        # Stacked imbalance (+20)
        imbalance = components.get("imbalance", {})
        if imbalance.get("stacked"):
            confidence += 20
            reasons.append(f"Stacked {imbalance.get('type')} imbalance")

        # Volume spike (+15)
        volume = components.get("volume", {})
        if volume.get("spike"):
            confidence += 15
            reasons.append("Volume spike")

        # Cap at 100
        confidence = min(100.0, confidence)

        return confidence, reasons

    def _calculate_stop_loss(
        self,
        entry_price: float,
        direction: SignalDirection,
        market_data: dict[str, Any],
        strategy_components: dict[str, Any]
    ) -> float:
        """
        Calculate stop loss price.

        Args:
            entry_price: Entry price.
            direction: Signal direction.
            market_data: Current market data.
            strategy_components: Strategy components results.

        Returns:
            Stop loss price.
        """
        # Use absorption level or swing low/high for stop
        components = strategy_components.get("components", {})

        # Get recent swing levels
        zones = components.get("zones", {})
        swing_lows = zones.get("swing_lows", [])
        swing_highs = zones.get("swing_highs", [])

        risk_percent = self.settings.risk.default_risk_percent / 100

        if direction == SignalDirection.LONG:
            # For long, stop below entry
            # Try to use swing low for stop
            if swing_lows:
                recent_low = min(swing_lows[-3:]) if len(swing_lows) >= 3 else swing_lows[-1]
                # Stop below swing low or at risk percentage
                stop = min(entry_price * (1 - risk_percent), recent_low * 0.998)
            else:
                stop = entry_price * (1 - risk_percent)

        else:
            # For short, stop above entry
            if swing_highs:
                recent_high = max(swing_highs[-3:]) if len(swing_highs) >= 3 else swing_highs[-1]
                stop = max(entry_price * (1 + risk_percent), recent_high * 1.002)
            else:
                stop = entry_price * (1 + risk_percent)

        return round(stop, 2)

    def _calculate_take_profits(
        self,
        entry_price: float,
        stop_price: float,
        direction: SignalDirection
    ) -> dict[str, float]:
        """
        Calculate take profit levels.

        Args:
            entry_price: Entry price.
            stop_price: Stop loss price.
            direction: Signal direction.

        Returns:
            Dictionary with TP1, TP2, TP3.
        """
        risk = abs(entry_price - stop_price)
        min_rr = self.settings.risk.min_risk_reward

        # TP1 at 1:1
        if direction == SignalDirection.LONG:
            tp1 = entry_price + risk
            tp2 = entry_price + (risk * 2)
            tp3 = entry_price + (risk * 3)
        else:
            tp1 = entry_price - risk
            tp2 = entry_price - (risk * 2)
            tp3 = entry_price - (risk * 3)

        return {
            "tp1": round(tp1, 2),
            "tp2": round(tp2, 2),
            "tp3": round(tp3, 2),
        }

    def _validate_signal(self, signal: TradingSignal) -> bool:
        """
        Validate a signal before generating it.

        Args:
            signal: Signal to validate.

        Returns:
            True if signal is valid.
        """
        # Check minimum confidence
        if signal.confidence < self.settings.strategy.min_confidence:
            logger.debug(f"Signal below minimum confidence: {signal.confidence}")
            return False

        # Check minimum risk:reward
        if signal.risk_reward_ratio < self.settings.risk.min_risk_reward:
            logger.debug(f"Signal below minimum R:R: {signal.risk_reward_ratio}")
            return False

        # Check valid prices
        if signal.entry_price <= 0 or signal.stop_price <= 0:
            logger.debug("Invalid price values")
            return False

        return True

    def get_signal_summary(self, signal: TradingSignal) -> str:
        """
        Get human-readable signal summary.

        Args:
            signal: Signal to summarize.

        Returns:
            Formatted signal string.
        """
        direction = signal.direction.value.upper()
        summary = f"""
{direction} {signal.symbol} SIGNAL

Entry: {signal.entry_price}
Stop: {signal.stop_price}

Targets
TP1: {signal.tp1}
TP2: {signal.tp2}
TP3: {signal.tp3}

Confidence: {signal.confidence}% ({signal.confidence_level.upper()})

Reason:
"""
        for reason in signal.reason:
            summary += f"• {reason}\n"

        summary += f"\nR:R: 1:{signal.risk_reward_ratio:.1f}"

        return summary

    def get_signals(self, count: int = 50) -> list[TradingSignal]:
        """
        Get recent signals.

        Args:
            count: Number of signals to return.

        Returns:
            List of recent signals.
        """
        return self._signal_history[-count:]

    def get_pending_signals(self) -> list[TradingSignal]:
        """Get all pending signals."""
        return [s for s in self._signal_history if s.status == SignalStatus.PENDING]

    def reset(self) -> None:
        """Reset the signal builder."""
        self._signal_history.clear()
        logger.info("Signal builder reset")


class OrderflowStrategy:
    """
    Complete orderflow trading strategy.

    Orchestrates all strategy components to detect and generate signals.
    """

    def __init__(self) -> None:
        """Initialize the orderflow strategy."""
        self.settings = get_settings()
        self.signal_builder = SignalBuilder()

    def analyze(
        self,
        market_data: dict[str, Any],
        orderflow_data: dict[str, Any]
    ) -> TradingSignal | None:
        """
        Run complete strategy analysis.

        Args:
            market_data: Current market data.
            orderflow_data: Orderflow engine data.

        Returns:
            TradingSignal if strategy triggers, None otherwise.
        """
        symbol = market_data.get("symbol", "BTCUSDT")
        current_price = market_data.get("current_price", 0)

        # Collect strategy components
        components = {
            "zones": orderflow_data.get("zones", {}),
            "absorption": orderflow_data.get("absorption", {}),
            "cvd_divergence": orderflow_data.get("cvd_divergence", {}),
            "imbalance": orderflow_data.get("imbalance", {}),
            "volume": orderflow_data.get("volume", {}),
            "initiation": orderflow_data.get("initiation", {}),
            "pullback": orderflow_data.get("pullback", {}),
        }

        # Check for long signal conditions
        long_conditions = self._check_long_conditions(components)
        if long_conditions["valid"]:
            return self.signal_builder.build_signal(
                symbol=symbol,
                direction=SignalDirection.LONG,
                entry_price=current_price,
                market_data=market_data,
                strategy_components={"components": components},
            )

        # Check for short signal conditions
        short_conditions = self._check_short_conditions(components)
        if short_conditions["valid"]:
            return self.signal_builder.build_signal(
                symbol=symbol,
                direction=SignalDirection.SHORT,
                entry_price=current_price,
                market_data=market_data,
                strategy_components={"components": components},
            )

        return None

    def _check_long_conditions(self, components: dict[str, Any]) -> dict[str, Any]:
        """
        Check for long signal conditions.

        Args:
            components: Strategy components.

        Returns:
            Dictionary with validation result.
        """
        conditions = {
            "valid": False,
            "reason": "",
        }

        # Check absorption (sell absorption = potential long)
        absorption = components.get("absorption", {})
        if not absorption.get("detected") or absorption.get("type") != "buy":
            conditions["reason"] = "No buy absorption"
            return conditions

        # Check CVD divergence (bullish)
        cvd = components.get("cvd_divergence", {})
        if cvd.get("detected") and cvd.get("type") != "bullish":
            conditions["reason"] = "No bullish CVD divergence"
            return conditions

        # Check imbalance
        imbalance = components.get("imbalance", {})
        if not imbalance.get("stacked") or imbalance.get("type") != "buy":
            conditions["reason"] = "No stacked buy imbalance"
            return conditions

        # Check initiation
        initiation = components.get("initiation", {})
        if initiation.get("detected") and initiation.get("direction") != "bullish":
            conditions["reason"] = "No bullish initiation"
            return conditions

        conditions["valid"] = True
        conditions["reason"] = "All long conditions met"
        return conditions

    def _check_short_conditions(self, components: dict[str, Any]) -> dict[str, Any]:
        """
        Check for short signal conditions.

        Args:
            components: Strategy components.

        Returns:
            Dictionary with validation result.
        """
        conditions = {
            "valid": False,
            "reason": "",
        }

        # Check absorption (buy absorption = potential short)
        absorption = components.get("absorption", {})
        if not absorption.get("detected") or absorption.get("type") != "sell":
            conditions["reason"] = "No sell absorption"
            return conditions

        # Check CVD divergence (bearish)
        cvd = components.get("cvd_divergence", {})
        if cvd.get("detected") and cvd.get("type") != "bearish":
            conditions["reason"] = "No bearish CVD divergence"
            return conditions

        # Check imbalance
        imbalance = components.get("imbalance", {})
        if not imbalance.get("stacked") or imbalance.get("type") != "sell":
            conditions["reason"] = "No stacked sell imbalance"
            return conditions

        # Check initiation
        initiation = components.get("initiation", {})
        if initiation.get("detected") and initiation.get("direction") != "bearish":
            conditions["reason"] = "No bearish initiation"
            return conditions

        conditions["valid"] = True
        conditions["reason"] = "All short conditions met"
        return conditions

