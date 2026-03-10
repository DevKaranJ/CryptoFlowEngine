"""
PnL Tracker - Tracks profit and loss for paper trades.

Calculates and tracks:
- Realized PnL
- Unrealized PnL
- Win rate
- Risk metrics
- Performance statistics
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from config import get_settings
from core.logging_config import get_logger

logger = get_logger("paper_trading.pnl")


@dataclass
class TradeRecord:
    """Record of a closed trade."""

    id: int
    signal_id: str
    symbol: str
    direction: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_percent: float
    result: str
    entry_time: int
    exit_time: int
    duration_ms: int


@dataclass
class PerformanceMetrics:
    """Performance metrics summary."""

    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    avg_pnl: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    avg_duration_ms: int
    profit_factor: float


class PnLTracker:
    """
    Tracks PnL and performance metrics.

    Provides comprehensive statistics for strategy evaluation.
    """

    def __init__(self) -> None:
        """Initialize the PnL tracker."""
        self.settings = get_settings()
        self._trades: deque[TradeRecord] = deque(maxlen=1000)
        self._daily_stats: dict[str, dict[str, Any]] = {}

    def record_trade(
        self,
        signal_id: str,
        symbol: str,
        direction: str,
        entry_price: float,
        exit_price: float,
        quantity: float,
        pnl: float,
        result: str,
        entry_time: int,
        exit_time: int,
    ) -> TradeRecord:
        """
        Record a closed trade.

        Args:
            signal_id: Related signal ID.
            symbol: Trading symbol.
            direction: Trade direction.
            entry_price: Entry price.
            exit_price: Exit price.
            quantity: Trade quantity.
            pnl: Profit/loss amount.
            result: Trade result.
            entry_time: Entry timestamp.
            exit_time: Exit timestamp.

        Returns:
            TradeRecord object.
        """
        # Calculate PnL percentage
        position_value = entry_price * quantity
        pnl_percent = (pnl / position_value * 100) if position_value > 0 else 0

        # Calculate duration
        duration_ms = exit_time - entry_time

        # Create record
        trade = TradeRecord(
            id=len(self._trades) + 1,
            signal_id=signal_id,
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=quantity,
            pnl=pnl,
            pnl_percent=pnl_percent,
            result=result,
            entry_time=entry_time,
            exit_time=exit_time,
            duration_ms=duration_ms,
        )

        self._trades.append(trade)

        # Update daily stats
        self._update_daily_stats(symbol, pnl)

        logger.info(
            f"Trade recorded: {symbol} {direction} | "
            f"PnL: {pnl:.2f} ({pnl_percent:.2f}%) | "
            f"Result: {result}"
        )

        return trade

    def _update_daily_stats(self, symbol: str, pnl: float) -> None:
        """Update daily statistics."""
        today = datetime.now().strftime("%Y-%m-%d")

        if today not in self._daily_stats:
            self._daily_stats[today] = {
                "trades": 0,
                "wins": 0,
                "losses": 0,
                "pnl": 0.0,
                "symbols": set(),
            }

        self._daily_stats[today]["trades"] += 1
        self._daily_stats[today]["pnl"] += pnl
        self._daily_stats[today]["symbols"].add(symbol)

        if pnl > 0:
            self._daily_stats[today]["wins"] += 1
        elif pnl < 0:
            self._daily_stats[today]["losses"] += 1

    def get_performance_metrics(self, lookback: int = 100) -> PerformanceMetrics:
        """
        Calculate performance metrics.

        Args:
            lookback: Number of trades to analyze.

        Returns:
            PerformanceMetrics object.
        """
        trades = list(self._trades)[-lookback:]

        if not trades:
            return PerformanceMetrics(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0,
                total_pnl=0,
                avg_pnl=0,
                avg_win=0,
                avg_loss=0,
                largest_win=0,
                largest_loss=0,
                avg_duration_ms=0,
                profit_factor=0,
            )

        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl < 0]

        total_trades = len(trades)
        winning_count = len(winning_trades)
        losing_count = len(losing_trades)

        total_pnl = sum(t.pnl for t in trades)
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0

        avg_win = sum(t.pnl for t in winning_trades) / winning_count if winning_count > 0 else 0
        avg_loss = sum(t.pnl for t in losing_trades) / losing_count if losing_count > 0 else 0

        largest_win = max((t.pnl for t in trades), default=0)
        largest_loss = min((t.pnl for t in trades), default=0)

        avg_duration = sum(t.duration_ms for t in trades) / total_trades if total_trades > 0 else 0

        # Profit factor (gross profit / gross loss)
        gross_profit = sum(t.pnl for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t.pnl for t in losing_trades)) if losing_trades else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        win_rate = (winning_count / total_trades * 100) if total_trades > 0 else 0

        return PerformanceMetrics(
            total_trades=total_trades,
            winning_trades=winning_count,
            losing_trades=losing_count,
            win_rate=win_rate,
            total_pnl=total_pnl,
            avg_pnl=avg_pnl,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            avg_duration_ms=int(avg_duration),
            profit_factor=profit_factor,
        )

    def get_symbol_stats(self, symbol: str) -> dict[str, Any]:
        """
        Get statistics for a specific symbol.

        Args:
            symbol: Trading symbol.

        Returns:
            Statistics dictionary.
        """
        symbol_trades = [t for t in self._trades if t.symbol == symbol]

        if not symbol_trades:
            return {
                "symbol": symbol,
                "total_trades": 0,
                "win_rate": 0,
                "total_pnl": 0,
            }

        winning = [t for t in symbol_trades if t.pnl > 0]
        losing = [t for t in symbol_trades if t.pnl < 0]

        return {
            "symbol": symbol,
            "total_trades": len(symbol_trades),
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "win_rate": len(winning) / len(symbol_trades) * 100,
            "total_pnl": sum(t.pnl for t in symbol_trades),
            "avg_pnl": sum(t.pnl for t in symbol_trades) / len(symbol_trades),
        }

    def get_daily_stats(self, date: str | None = None) -> dict[str, Any]:
        """
        Get daily statistics.

        Args:
            date: Date string (YYYY-MM-DD). Uses today if None.

        Returns:
            Daily statistics.
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        if date not in self._daily_stats:
            return {
                "date": date,
                "trades": 0,
                "wins": 0,
                "losses": 0,
                "pnl": 0,
            }

        stats = self._daily_stats[date]
        return {
            "date": date,
            "trades": stats["trades"],
            "wins": stats["wins"],
            "losses": stats["losses"],
            "pnl": stats["pnl"],
            "win_rate": stats["wins"] / stats["trades"] * 100 if stats["trades"] > 0 else 0,
            "symbols": list(stats["symbols"]),
        }

    def get_trades_by_result(self, result: str, count: int = 50) -> list[TradeRecord]:
        """
        Get trades filtered by result.

        Args:
            result: Result type (tp_hit, sl_hit, etc).
            count: Maximum number to return.

        Returns:
            List of trades.
        """
        filtered = [t for t in self._trades if t.result == result]
        return filtered[-count:]

    def get_recent_trades(self, count: int = 50) -> list[TradeRecord]:
        """
        Get recent trades.

        Args:
            count: Number of trades to return.

        Returns:
            List of recent trades.
        """
        return list(self._trades)[-count:]

    def get_consecutive_wins(self) -> int:
        """Get count of consecutive winning trades."""
        wins = 0
        for trade in reversed(self._trades):
            if trade.pnl > 0:
                wins += 1
            else:
                break
        return wins

    def get_consecutive_losses(self) -> int:
        """Get count of consecutive losing trades."""
        losses = 0
        for trade in reversed(self._trades):
            if trade.pnl < 0:
                losses += 1
            else:
                break
        return losses

    def calculate_expectancy(self) -> float:
        """
        Calculate trading expectancy.

        Expectancy = (Win Rate * Avg Win) - (Loss Rate * Avg Loss)

        Returns:
            Expectancy value.
        """
        metrics = self.get_performance_metrics()
        win_rate = metrics.win_rate / 100
        loss_rate = 1 - win_rate

        expectancy = (win_rate * metrics.avg_win) - (loss_rate * abs(metrics.avg_loss))
        return expectancy

    def get_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe ratio based on trade returns.

        Args:
            risk_free_rate: Annual risk-free rate.

        Returns:
            Sharpe ratio.
        """
        trades = list(self._trades)
        if len(trades) < 2:
            return 0.0

        returns = [t.pnl_percent / 100 for t in trades]
        avg_return = sum(returns) / len(returns)

        # Calculate standard deviation
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5

        if std_dev == 0:
            return 0.0

        # Annualize (assuming ~252 trading days, 1 trade per day average)
        periods = len(trades)
        if periods == 0:
            return 0.0

        sharpe = (avg_return - risk_free_rate / periods) / std_dev * (periods ** 0.5)
        return sharpe

    def reset(self) -> None:
        """Reset the PnL tracker."""
        self._trades.clear()
        self._daily_stats.clear()
        logger.info("PnL tracker reset")


class RiskManager:
    """
    Risk management utilities.

    Provides risk calculations and position sizing.
    """

    def __init__(self) -> None:
        """Initialize risk manager."""
        self.settings = get_settings()

    def calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_price: float,
        risk_percent: float | None = None
    ) -> float:
        """
        Calculate position size based on risk.

        Args:
            account_balance: Current account balance.
            entry_price: Entry price.
            stop_price: Stop loss price.
            risk_percent: Risk percentage (uses config if None).

        Returns:
            Position size.
        """
        if risk_percent is None:
            risk_percent = self.settings.risk.default_risk_percent

        risk_amount = account_balance * (risk_percent / 100)
        risk_per_unit = abs(entry_price - stop_price)

        if risk_per_unit == 0:
            return 0.0

        position_size = risk_amount / risk_per_unit

        # Apply max position size constraint
        max_position = account_balance * self.settings.risk.max_position_size
        max_size = max_position / entry_price

        return min(position_size, max_size)

    def validate_risk_reward(
        self,
        entry_price: float,
        stop_price: float,
        tp_price: float,
        direction: str
    ) -> tuple[bool, float]:
        """
        Validate risk:reward ratio.

        Args:
            entry_price: Entry price.
            stop_price: Stop loss price.
            tp_price: Take profit price.
            direction: Trade direction.

        Returns:
            Tuple of (is_valid, rr_ratio).
        """
        risk = abs(entry_price - stop_price)

        if direction == "long":
            reward = tp_price - entry_price
        else:
            reward = entry_price - tp_price

        if risk == 0:
            return False, 0.0

        rr_ratio = reward / risk

        is_valid = rr_ratio >= self.settings.risk.min_risk_reward

        return is_valid, rr_ratio

    def calculate_kelly_criterion(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> float:
        """
        Calculate Kelly Criterion for position sizing.

        Args:
            win_rate: Win rate (0-1).
            avg_win: Average winning amount.
            avg_loss: Average losing amount.

        Returns:
            Kelly percentage (0-1).
        """
        if avg_loss == 0:
            return 0.0

        win_loss_ratio = avg_win / abs(avg_loss)
        kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio

        # Cap at 0.25 (25%) for safety
        return max(0, min(kelly, 0.25))

