"""
AI module for the crypto trading bot.

This module provides AI-powered analysis:
- Signal Explainer: Generates human-readable explanations
- Signal Validator: Validates signals (NOT generates them)

IMPORTANT: The AI does NOT generate trading signals. Signal generation
is done by the strategy engine. AI's role is to explain and validate.
"""

from ai.signal_explainer import SignalExplainer, SignalExplanation, SignalValidator

__all__ = [
    "SignalExplanation",
    "SignalExplainer",
    "SignalValidator",
]

