"""
AI Signal Explainer - Generates human-readable explanations for signals.

IMPORTANT: This AI does NOT generate trading signals. Its role is ONLY to:
- Analyze signal context
- Summarize reasoning
- Produce a readable explanation

The signal generation is done by the strategy engine (NOT by AI).
"""

from dataclasses import dataclass
from typing import Any

from config import get_settings
from core.logging_config import get_logger

logger = get_logger("ai.explainer")


@dataclass
class SignalExplanation:
    """Represents an AI explanation for a trading signal."""

    signal_id: str
    summary: str
    detailed_reasoning: list[str]
    market_context: str
    risk_assessment: str
    confidence_note: str


class SignalExplainer:
    """
    Generates human-readable explanations for trading signals.

    This AI explains the ORDERFLOW logic behind signals, not generate them.
    """

    def __init__(self) -> None:
        """Initialize the signal explainer."""
        self.settings = get_settings()

    def explain_signal(
        self,
        signal_data: dict[str, Any],
        market_context: dict[str, Any]
    ) -> SignalExplanation:
        """
        Generate explanation for a trading signal.

        Args:
            signal_data: The trading signal data.
            market_context: Current market context.

        Returns:
            SignalExplanation with human-readable explanation.
        """
        symbol = signal_data.get("symbol", "UNKNOWN")
        direction = signal_data.get("direction", "none").upper()
        entry = signal_data.get("entry_price", 0)
        stop = signal_data.get("stop_price", 0)
        tp1 = signal_data.get("tp1", 0)
        tp2 = signal_data.get("tp2", 0)
        confidence = signal_data.get("confidence", 0)
        reasons = signal_data.get("reason", [])

        # Build explanation
        detailed_reasoning = []

        # Add signal header
        summary = f"{direction} {symbol} SIGNAL\n\n"

        # Add entry levels
        summary += f"Entry: {entry}\n"
        summary += f"Stop: {stop}\n"
        if tp1:
            summary += f"TP1: {tp1}\n"
        if tp2:
            summary += f"TP2: {tp2}\n"
        summary += f"\nConfidence: {confidence}%\n\n"

        # Add reasons
        summary += "Reason:\n"
        for reason in reasons:
            summary += f"• {reason}\n"
            detailed_reasoning.append(reason)

        # Analyze market context
        context_analysis = self._analyze_market_context(market_context)
        market_context_str = self._format_market_context(context_analysis)

        # Risk assessment
        risk_assessment = self._assess_risk(
            signal_data=signal_data,
            market_context=market_context
        )

        # Confidence note
        confidence_note = self._generate_confidence_note(confidence)

        return SignalExplanation(
            signal_id=signal_data.get("id", "UNKNOWN"),
            summary=summary,
            detailed_reasoning=detailed_reasoning,
            market_context=market_context_str,
            risk_assessment=risk_assessment,
            confidence_note=confidence_note,
        )

    def _analyze_market_context(self, market_context: dict[str, Any]) -> dict[str, str]:
        """
        Analyze market context.

        Args:
            market_context: Market context data.

        Returns:
            Analysis dictionary.
        """
        analysis = {}

        # CVD analysis
        cvd = market_context.get("cvd", 0)
        if cvd > 0:
            analysis["cvd"] = "CVD is positive (bullish pressure)"
        elif cvd < 0:
            analysis["cvd"] = "CVD is negative (bearish pressure)"
        else:
            analysis["cvd"] = "CVD is neutral"

        # Delta analysis
        delta = market_context.get("delta", 0)
        if delta > 0:
            analysis["delta"] = "Delta is positive (buyers aggressive)"
        elif delta < 0:
            analysis["delta"] = "Delta is negative (sellers aggressive)"
        else:
            analysis["delta"] = "Delta is balanced"

        # Volume analysis
        volume = market_context.get("volume", 0)
        avg_volume = market_context.get("avg_volume", 0)
        if avg_volume > 0:
            volume_ratio = volume / avg_volume
            if volume_ratio > 1.5:
                analysis["volume"] = f"High volume spike ({volume_ratio:.1f}x average)"
            elif volume_ratio > 1.0:
                analysis["volume"] = f"Above average volume ({volume_ratio:.1f}x)"
            else:
                analysis["volume"] = "Normal volume"
        else:
            analysis["volume"] = "Volume data unavailable"

        # Trend analysis
        trend = market_context.get("trend", "unknown")
        analysis["trend"] = f"Market is {trend}"

        return analysis

    def _format_market_context(self, analysis: dict[str, str]) -> str:
        """
        Format market context analysis.

        Args:
            analysis: Analysis dictionary.

        Returns:
            Formatted string.
        """
        context = "Market Context:\n"
        for key, value in analysis.items():
            context += f"• {value}\n"
        return context

    def _assess_risk(
        self,
        signal_data: dict[str, Any],
        market_context: dict[str, Any]
    ) -> str:
        """
        Assess risk for the signal.

        Args:
            signal_data: Signal data.
            market_context: Market context.

        Returns:
            Risk assessment string.
        """
        entry = signal_data.get("entry_price", 0)
        stop = signal_data.get("stop_price", 0)
        direction = signal_data.get("direction", "none")

        if entry == 0 or stop == 0:
            return "Risk assessment unavailable"

        # Calculate risk percentage
        risk_percent = abs(entry - stop) / entry * 100

        # Calculate R:R
        tp1 = signal_data.get("tp1", 0)
        if tp1 > 0:
            if direction == "long":
                reward_percent = (tp1 - entry) / entry * 100
            else:
                reward_percent = (entry - tp1) / entry * 100

            rr_ratio = reward_percent / risk_percent if risk_percent > 0 else 0

            assessment = f"Risk: {risk_percent:.2f}%, Reward: {reward_percent:.2f}%, R:R = 1:{rr_ratio:.1f}"

            if rr_ratio >= 2.0:
                assessment += " (Good risk:reward)"
            elif rr_ratio >= 1.5:
                assessment += " (Acceptable risk:reward)"
            else:
                assessment += " (Low risk:reward - caution)"

            return assessment

        return f"Risk: {risk_percent:.2f}%"

    def _generate_confidence_note(self, confidence: float) -> str:
        """
        Generate confidence note.

        Args:
            confidence: Confidence percentage.

        Returns:
            Confidence note string.
        """
        if confidence >= 70:
            return (
                "This is a HIGH confidence signal based on multiple "
                "orderflow confirmations. The setup shows strong "
                "institutional activity patterns."
            )
        elif confidence >= 50:
            return (
                "This is a MEDIUM confidence signal. While the setup "
                "shows valid orderflow patterns, consider additional "
                "confirmation before entering."
            )
        else:
            return (
                "This is a LOW confidence signal. The orderflow patterns "
                "are present but not strongly confirmed. Exercise caution "
                "and consider smaller position size."
            )

    def generate_full_explanation(
        self,
        signal_data: dict[str, Any],
        market_context: dict[str, Any]
    ) -> str:
        """
        Generate a complete formatted explanation.

        Args:
            signal_data: The trading signal.
            market_context: Current market context.

        Returns:
            Complete formatted explanation string.
        """
        explanation = self.explain_signal(signal_data, market_context)

        output = f"""
{'='*50}
{explanation.summary}
{'='*50}

{explanation.market_context}

Risk Assessment:
{explanation.risk_assessment}

AI Note:
{explanation.confidence_note}

{'='*50}
DISCLAIMER: This is NOT financial advice. 
Always do your own research before trading.
{'='*50}
"""
        return output


class SignalValidator:
    """
    Validates signals based on additional criteria.

    This does NOT generate signals - only validates existing ones.
    """

    def __init__(self) -> None:
        """Initialize the signal validator."""
        self.settings = get_settings()

    def validate_signal(
        self,
        signal_data: dict[str, Any],
        market_context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Validate a trading signal.

        Args:
            signal_data: Signal to validate.
            market_context: Current market context.

        Returns:
            Validation result with is_valid and reasons.
        """
        is_valid = True
        reasons = []

        # Check minimum confidence
        confidence = signal_data.get("confidence", 0)
        min_conf = self.settings.strategy.min_confidence
        if confidence < min_conf:
            is_valid = False
            reasons.append(f"Confidence {confidence}% below minimum {min_conf}%")

        # Check risk:reward
        entry = signal_data.get("entry_price", 0)
        stop = signal_data.get("stop_price", 0)
        tp1 = signal_data.get("tp1", 0)

        if entry > 0 and stop > 0 and tp1 > 0:
            direction = signal_data.get("direction", "none")
            risk = abs(entry - stop)

            if direction == "long":
                reward = tp1 - entry
            else:
                reward = entry - tp1

            if reward > 0:
                rr = reward / risk
                min_rr = self.settings.risk.min_risk_reward
                if rr < min_rr:
                    is_valid = False
                    reasons.append(f"R:R ratio {rr:.1f} below minimum {min_rr}")

        # Check for adverse market conditions
        volatility = market_context.get("volatility", 1.0)
        if volatility < 0.3:
            reasons.append("Low volatility - may result in choppy price action")

        trend = market_context.get("trend", "unknown")
        direction = signal_data.get("direction", "none")

        # Check trend alignment
        if trend != "unknown" and trend != "ranging":
            if direction == "long" and trend == "downtrend":
                is_valid = False
                reasons.append("Long signal against downtrend")
            elif direction == "short" and trend == "uptrend":
                is_valid = False
                reasons.append("Short signal against uptrend")

        return {
            "is_valid": is_valid,
            "reasons": reasons,
        }

    def should_take_trade(
        self,
        signal_data: dict[str, Any],
        market_context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Determine if a signal should be taken.

        Args:
            signal_data: Signal data.
            market_context: Market context.

        Returns:
            Decision with recommendation.
        """
        validation = self.validate_signal(signal_data, market_context)

        confidence = signal_data.get("confidence", 0)
        direction = signal_data.get("direction", "none")

        # Make recommendation
        if not validation["is_valid"]:
            recommendation = "SKIP"
            reason = "; ".join(validation["reasons"])
        elif confidence >= 70:
            recommendation = "TAKE"
            reason = "High confidence with valid risk:reward"
        elif confidence >= 50:
            recommendation = "CONSIDER"
            reason = "Medium confidence - use smaller size"
        else:
            recommendation = "SKIP"
            reason = "Low confidence signal"

        return {
            "recommendation": recommendation,
            "reason": reason,
            "validation": validation,
            "position_size_suggestion": self._suggest_position_size(
                confidence=confidence,
                is_valid=validation["is_valid"]
            ),
        }

    def _suggest_position_size(
        self,
        confidence: float,
        is_valid: bool
    ) -> str:
        """
        Suggest position size based on confidence.

        Args:
            confidence: Signal confidence.
            is_valid: Whether signal passed validation.

        Returns:
            Position size suggestion.
        """
        if not is_valid:
            return "0% (signal invalid)"

        if confidence >= 70:
            return "Full size (1x risk)"
        elif confidence >= 50:
            return "Half size (0.5x risk)"
        else:
            return "Quarter size or skip (0.25x risk)"

