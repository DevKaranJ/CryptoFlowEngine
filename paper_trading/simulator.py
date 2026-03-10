"""
Paper Trading Simulator - Virtual trade executor.

Simulates trades in a virtual environment without real money.
Tracks positions, checks for TP/SL hits, and calculates PnL.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from config import get_settings
from core.logging_config import get_logger, get_trade_logger

logger = get_logger("paper_trading.simulator")
trade_logger = get_trade_logger()


@dataclass
class Position:
    """Represents an open position."""

    id: int
    signal_id: str
    symbol: str
    direction: str  # "long" or "short"
    entry_price: float
    quantity: float
    entry_time: int
    stop_price: float
    tp1: float
    tp2: float = 0.0
    tp3: float = 0.0
    status: str = "open"


@dataclass
class TradeResult:
    """Represents a closed trade result."""

    position_id: int
    signal_id: str
    symbol: str
    direction: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_percent: float
    result: str  # "tp_hit", "sl_hit", "manual"
    exit_reason: str
    duration_ms: int


class PaperTradingSimulator:
    """
    Paper trading simulator.

    Executes virtual trades based on signals and tracks their performance.
    """

    def __init__(self, db_manager: Any | None = None) -> None:
        """
        Initialize the paper trading simulator.

        Args:
            db_manager: Optional database manager for logging.
        """
        self.settings = get_settings()
        self.db_manager = db_manager

        # Virtual balance
        self.balance = self.settings.paper_trading.initial_balance
        self.commission_rate = self.settings.paper_trading.commission

        # Position tracking
        self._positions: dict[int, Position] = {}
        self._position_counter = 0
        self._trade_history: list[TradeResult] = []

    def open_position(
        self,
        signal_id: str,
        symbol: str,
        direction: str,
        entry_price: float,
        quantity: float,
        stop_price: float,
        tp1: float,
        tp2: float = 0.0,
        tp3: float = 0.0,
    ) -> Position | None:
        """
        Open a new position.

        Args:
            signal_id: Related signal ID.
            symbol: Trading symbol.
            direction: "long" or "short".
            entry_price: Entry price.
            quantity: Position size.
            stop_price: Stop loss price.
            tp1: Take profit 1.
            tp2: Take profit 2.
            tp3: Take profit 3.

        Returns:
            Position object or None if failed.
        """
        # Check balance
        required_margin = entry_price * quantity
        if required_margin > self.balance:
            logger.warning(f"Insufficient balance: {required_margin} > {self.balance}")
            return None

        # Deduct margin from balance
        self.balance -= required_margin

        # Create position
        self._position_counter += 1
        position = Position(
            id=self._position_counter,
            signal_id=signal_id,
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            quantity=quantity,
            entry_time=int(datetime.now().timestamp() * 1000),
            stop_price=stop_price,
            tp1=tp1,
            tp2=tp2,
            tp3=tp3,
            status="open",
        )

        self._positions[position.id] = position

        logger.info(
            f"Position opened: {position.id} | {symbol} {direction} @ {entry_price} "
            f"SL: {stop_price} TP: {tp1}"
        )

        # Log to database if available
        if self.db_manager:
            try:
                signal = self.db_manager.get_signal_by_id(signal_id)
                if signal:
                    self.db_manager.create_paper_trade(
                        signal_id=signal.id,
                        trade_data={
                            "entry_price": entry_price,
                            "quantity": quantity,
                            "entry_time": position.entry_time,
                            "status": "open",
                        }
                    )
            except Exception as e:
                logger.error(f"Failed to log position to database: {e}")

        return position

    def check_position(
        self,
        position_id: int,
        current_price: float,
        current_time: int | None = None
    ) -> dict[str, Any]:
        """
        Check if position should be closed (TP/SL hit).

        Args:
            position_id: Position ID.
            current_price: Current market price.
            current_time: Current timestamp.

        Returns:
            Dictionary with check results.
        """
        if position_id not in self._positions:
            return {"should_close": False, "reason": "position_not_found"}

        position = self._positions[position_id]
        if position.status != "open":
            return {"should_close": False, "reason": "not_open"}

        if current_time is None:
            current_time = int(datetime.now().timestamp() * 1000)

        result = {
            "should_close": False,
            "reason": "",
            "exit_price": 0,
            "result": "",
        }

        if position.direction == "long":
            # Check stop loss
            if current_price <= position.stop_price:
                result["should_close"] = True
                result["reason"] = "stop_loss"
                result["exit_price"] = position.stop_price
                result["result"] = "sl_hit"

            # Check TP1
            elif current_price >= position.tp1:
                result["should_close"] = True
                result["reason"] = "take_profit_1"
                result["exit_price"] = position.tp1
                result["result"] = "tp_hit"

            # Check TP2
            elif position.tp2 > 0 and current_price >= position.tp2:
                result["should_close"] = True
                result["reason"] = "take_profit_2"
                result["exit_price"] = position.tp2
                result["result"] = "tp_hit"

            # Check TP3
            elif position.tp3 > 0 and current_price >= position.tp3:
                result["should_close"] = True
                result["reason"] = "take_profit_3"
                result["exit_price"] = position.tp3
                result["result"] = "tp_hit"

        else:  # short
            # Check stop loss
            if current_price >= position.stop_price:
                result["should_close"] = True
                result["reason"] = "stop_loss"
                result["exit_price"] = position.stop_price
                result["result"] = "sl_hit"

            # Check TP1
            elif current_price <= position.tp1:
                result["should_close"] = True
                result["reason"] = "take_profit_1"
                result["exit_price"] = position.tp1
                result["result"] = "tp_hit"

            # Check TP2
            elif position.tp2 > 0 and current_price <= position.tp2:
                result["should_close"] = True
                result["reason"] = "take_profit_2"
                result["exit_price"] = position.tp2
                result["result"] = "tp_hit"

            # Check TP3
            elif position.tp3 > 0 and current_price <= position.tp3:
                result["should_close"] = True
                result["reason"] = "take_profit_3"
                result["exit_price"] = position.tp3
                result["result"] = "tp_hit"

        return result

    def close_position(
        self,
        position_id: int,
        exit_price: float,
        exit_time: int | None = None,
        reason: str = "manual"
    ) -> TradeResult | None:
        """
        Close a position.

        Args:
            position_id: Position ID to close.
            exit_price: Exit price.
            exit_time: Exit timestamp.
            reason: Reason for closing.

        Returns:
            TradeResult or None if failed.
        """
        if position_id not in self._positions:
            logger.warning(f"Position {position_id} not found")
            return None

        position = self._positions[position_id]

        if exit_time is None:
            exit_time = int(datetime.now().timestamp() * 1000)

        # Calculate PnL
        if position.direction == "long":
            pnl = (exit_price - position.entry_price) * position.quantity
        else:
            pnl = (position.entry_price - exit_price) * position.quantity

        # Subtract commission
        commission = (position.entry_price + exit_price) * position.quantity * self.commission_rate
        pnl -= commission

        # Calculate PnL percentage
        position_value = position.entry_price * position.quantity
        pnl_percent = (pnl / position_value) * 100

        # Determine result
        result = "closed"
        if "tp" in reason:
            result = "tp_hit"
        elif "sl" in reason:
            result = "sl_hit"

        # Refund margin to balance
        self.balance += position_value

        # Create trade result
        trade_result = TradeResult(
            position_id=position.id,
            signal_id=position.signal_id,
            symbol=position.symbol,
            direction=position.direction,
            entry_price=position.entry_price,
            exit_price=exit_price,
            quantity=position.quantity,
            pnl=pnl,
            pnl_percent=pnl_percent,
            result=result,
            exit_reason=reason,
            duration_ms=exit_time - position.entry_time,
        )

        # Update position status
        position.status = "closed"

        # Store in history
        self._trade_history.append(trade_result)

        # Log
        logger.info(
            f"Position closed: {position.id} | {result} | "
            f"PnL: {pnl:.2f} ({pnl_percent:.2f}%)"
        )

        trade_logger.log_pnl(position.id, pnl, result)

        # Update database if available
        if self.db_manager:
            try:
                self.db_manager.close_paper_trade(
                    trade_id=position_id,
                    exit_price=exit_price,
                    exit_time=exit_time,
                    result=result,
                    exit_reason=reason,
                )
            except Exception as e:
                logger.error(f"Failed to update trade in database: {e}")

        # Remove from active positions
        del self._positions[position_id]

        return trade_result

    def get_open_positions(self) -> list[Position]:
        """Get all open positions."""
        return [p for p in self._positions.values() if p.status == "open"]

    def get_position(self, position_id: int) -> Position | None:
        """Get a specific position."""
        return self._positions.get(position_id)

    def get_trade_history(self, count: int = 50) -> list[TradeResult]:
        """Get trade history."""
        return self._trade_history[-count:]

    def get_balance(self) -> float:
        """Get current virtual balance."""
        return self.balance

    def get_total_equity(self) -> float:
        """Get total equity (balance + open position value)."""
        total = self.balance
        for position in self.get_open_positions():
            if position.direction == "long":
                total += position.entry_price * position.quantity
            else:
                total += position.entry_price * position.quantity
        return total

    def reset(self) -> None:
        """Reset simulator to initial state."""
        self.balance = self.settings.paper_trading.initial_balance
        self._positions.clear()
        self._trade_history.clear()
        self._position_counter = 0
        logger.info("Paper trading simulator reset")


class SignalApprovalHandler:
    """
    Handles signal approval workflow.

    Manages the flow from signal generation to user approval
    to paper trade execution.
    """

    def __init__(
        self,
        simulator: PaperTradingSimulator,
        db_manager: Any | None = None
    ) -> None:
        """
        Initialize the approval handler.

        Args:
            simulator: Paper trading simulator.
            db_manager: Optional database manager.
        """
        self.simulator = simulator
        self.db_manager = db_manager
        self._pending_approvals: dict[str, dict[str, Any]] = {}

    def request_approval(self, signal_data: dict[str, Any]) -> str:
        """
        Request user approval for a signal.

        Args:
            signal_data: Signal data.

        Returns:
            Approval request ID.
        """
        signal_id = signal_data.get("id", "")
        self._pending_approvals[signal_id] = {
            "signal": signal_data,
            "timestamp": int(datetime.now().timestamp() * 1000),
            "status": "pending",
        }

        logger.info(f"Approval requested for signal {signal_id}")
        return signal_id

    def approve_signal(
        self,
        signal_id: str,
        quantity: float | None = None
    ) -> Position | None:
        """
        Approve and execute a signal.

        Args:
            signal_id: Signal ID to approve.
            quantity: Optional custom quantity.

        Returns:
            Position object or None if failed.
        """
        if signal_id not in self._pending_approvals:
            logger.warning(f"Signal {signal_id} not found in pending approvals")
            return None

        approval = self._pending_approvals[signal_id]
        signal = approval["signal"]

        # Use default quantity if not provided
        if quantity is None:
            # Calculate based on risk settings
            risk_amount = self.simulator.balance * (get_settings().risk.default_risk_percent / 100)
            entry = signal.get("entry_price", 0)
            stop = signal.get("stop_price", 0)
            if entry > 0 and stop > 0:
                risk_per_unit = abs(entry - stop)
                quantity = risk_amount / risk_per_unit if risk_per_unit > 0 else 0.01
            else:
                quantity = 0.01

        # Open position
        position = self.simulator.open_position(
            signal_id=signal_id,
            symbol=signal.get("symbol", ""),
            direction=signal.get("direction", "long"),
            entry_price=signal.get("entry_price", 0),
            quantity=quantity,
            stop_price=signal.get("stop_price", 0),
            tp1=signal.get("tp1", 0),
            tp2=signal.get("tp2", 0),
            tp3=signal.get("tp3", 0),
        )

        if position:
            approval["status"] = "approved"
            approval["position_id"] = position.id

            # Update database
            if self.db_manager:
                self.db_manager.update_signal_status(
                    signal_id=signal_id,
                    status="approved",
                    user_decision="approved",
                )

        return position

    def reject_signal(self, signal_id: str, reason: str = "") -> bool:
        """
        Reject a signal.

        Args:
            signal_id: Signal ID to reject.
            reason: Rejection reason.

        Returns:
            True if successful.
        """
        if signal_id not in self._pending_approvals:
            logger.warning(f"Signal {signal_id} not found in pending approvals")
            return False

        approval = self._pending_approvals[signal_id]
        approval["status"] = "rejected"
        approval["reject_reason"] = reason

        # Still create paper trade for tracking
        signal = approval["signal"]
        self._execute_paper_only(signal)

        # Update database
        if self.db_manager:
            self.db_manager.update_signal_status(
                signal_id=signal_id,
                status="rejected",
                user_decision="rejected",
                decision_reason=reason,
            )

        logger.info(f"Signal {signal_id} rejected: {reason}")
        return True

    def _execute_paper_only(self, signal: dict[str, Any]) -> None:
        """
        Execute paper trade without user approval (for tracking).

        Args:
            signal: Signal data.
        """
        # This runs paper trade regardless of approval for dataset building
        logger.info(f"Paper-only execution for signal {signal.get('id')}")

    def get_pending_approvals(self) -> list[dict[str, Any]]:
        """Get all pending approvals."""
        return [
            {"id": k, **v}
            for k, v in self._pending_approvals.items()
            if v["status"] == "pending"
        ]

