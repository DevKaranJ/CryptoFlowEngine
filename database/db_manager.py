"""
Database manager for the crypto trading bot.

Handles database operations including:
- Session management
- CRUD operations for all models
- Query helpers
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from config import get_settings, PROJECT_ROOT
from core.logging_config import get_logger
from database.models import (
    Base,
    MarketSnapshot,
    PaperTrade,
    Signal,
    SystemEvent,
    UserTrade,
)

logger = get_logger("database")


class DatabaseManager:
    """Manages database operations."""

    def __init__(self, db_path: str | None = None) -> None:
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database. Uses config if not provided.
        """
        settings = get_settings()

        if db_path is None:
            db_path = settings.database.path

        # Make path absolute
        if not Path(db_path).is_absolute():
            db_path = str(PROJECT_ROOT / db_path)

        # Create directory if needed
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Create engine
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,
            pool_pre_ping=True,
        )

        # Create session factory
        self.SessionFactory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
        )

        # Create tables
        self._create_tables()

        logger.info(f"Database initialized at {db_path}")

    def _create_tables(self) -> None:
        """Create all database tables."""
        Base.metadata.create_all(self.engine)
        logger.debug("Database tables created")

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionFactory()

    # ==================== SIGNAL OPERATIONS ====================

    def create_signal(
        self,
        signal_data: dict[str, Any]
    ) -> Signal:
        """
        Create a new signal in the database.

        Args:
            signal_data: Signal data dictionary.

        Returns:
            Created Signal object.
        """
        with self.get_session() as session:
            signal = Signal(
                signal_id=signal_data.get("id", ""),
                timestamp=signal_data.get("timestamp", 0),
                symbol=signal_data.get("symbol", ""),
                direction=signal_data.get("direction", ""),
                entry_price=signal_data.get("entry_price", 0),
                stop_price=signal_data.get("stop_price", 0),
                tp1=signal_data.get("tp1"),
                tp2=signal_data.get("tp2"),
                tp3=signal_data.get("tp3"),
                confidence=signal_data.get("confidence", 0),
                confidence_level=signal_data.get("confidence_level", "low"),
                reason=signal_data.get("reason", ""),
                status=signal_data.get("status", "pending"),
                strategy=signal_data.get("strategy", "orderflow_reversal"),
                timeframe=signal_data.get("timeframe", "15m"),
            )
            session.add(signal)
            session.commit()
            session.refresh(signal)

            logger.info(f"Signal created: {signal.signal_id}")
            return signal

    def get_signal_by_id(self, signal_id: str) -> Signal | None:
        """
        Get a signal by its signal_id.

        Args:
            signal_id: The signal ID.

        Returns:
            Signal object or None.
        """
        with self.get_session() as session:
            stmt = select(Signal).where(Signal.signal_id == signal_id)
            return session.scalar(stmt)

    def get_pending_signals(self, limit: int = 50) -> list[Signal]:
        """
        Get pending signals.

        Args:
            limit: Maximum number to return.

        Returns:
            List of pending signals.
        """
        with self.get_session() as session:
            stmt = (
                select(Signal)
                .where(Signal.status == "pending")
                .order_by(Signal.timestamp.desc())
                .limit(limit)
            )
            return list(session.scalars(stmt))

    def get_signals_by_symbol(
        self,
        symbol: str,
        limit: int = 100
    ) -> list[Signal]:
        """
        Get signals for a symbol.

        Args:
            symbol: Trading symbol.
            limit: Maximum number to return.

        Returns:
            List of signals.
        """
        with self.get_session() as session:
            stmt = (
                select(Signal)
                .where(Signal.symbol == symbol)
                .order_by(Signal.timestamp.desc())
                .limit(limit)
            )
            return list(session.scalars(stmt))

    def update_signal_status(
        self,
        signal_id: str,
        status: str,
        user_decision: str | None = None,
        decision_reason: str | None = None
    ) -> bool:
        """
        Update signal status.

        Args:
            signal_id: Signal ID to update.
            status: New status.
            user_decision: User decision if applicable.
            decision_reason: Reason for decision.

        Returns:
            True if updated successfully.
        """
        with self.get_session() as session:
            stmt = select(Signal).where(Signal.signal_id == signal_id)
            signal = session.scalar(stmt)

            if signal:
                signal.status = status
                if user_decision:
                    signal.user_decision = user_decision
                if decision_reason:
                    signal.decision_reason = decision_reason
                session.commit()
                logger.info(f"Signal {signal_id} status updated to {status}")
                return True

            return False

    # ==================== PAPER TRADE OPERATIONS ====================

    def create_paper_trade(
        self,
        signal_id: int,
        trade_data: dict[str, Any]
    ) -> PaperTrade:
        """
        Create a new paper trade.

        Args:
            signal_id: ID of the related signal.
            trade_data: Trade data dictionary.

        Returns:
            Created PaperTrade object.
        """
        with self.get_session() as session:
            trade = PaperTrade(
                signal_id=signal_id,
                entry_price=trade_data.get("entry_price", 0),
                quantity=trade_data.get("quantity", 0.01),
                entry_time=trade_data.get("entry_time", 0),
                status=trade_data.get("status", "open"),
            )
            session.add(trade)
            session.commit()
            session.refresh(trade)

            logger.info(f"Paper trade created: {trade.id}")
            return trade

    def update_paper_trade(
        self,
        trade_id: int,
        update_data: dict[str, Any]
    ) -> bool:
        """
        Update a paper trade.

        Args:
            trade_id: Trade ID to update.
            update_data: Data to update.

        Returns:
            True if updated successfully.
        """
        with self.get_session() as session:
            stmt = select(PaperTrade).where(PaperTrade.id == trade_id)
            trade = session.scalar(stmt)

            if trade:
                for key, value in update_data.items():
                    if hasattr(trade, key):
                        setattr(trade, key, value)
                session.commit()
                logger.info(f"Paper trade {trade_id} updated")
                return True

            return False

    def get_open_paper_trades(self) -> list[PaperTrade]:
        """
        Get all open paper trades.

        Returns:
            List of open trades.
        """
        with self.get_session() as session:
            stmt = (
                select(PaperTrade)
                .where(PaperTrade.status == "open")
                .order_by(PaperTrade.entry_time.desc())
            )
            return list(session.scalars(stmt))

    def close_paper_trade(
        self,
        trade_id: int,
        exit_price: float,
        exit_time: int,
        result: str,
        exit_reason: str
    ) -> bool:
        """
        Close a paper trade.

        Args:
            trade_id: Trade ID.
            exit_price: Exit price.
            exit_time: Exit timestamp.
            result: Trade result.
            exit_reason: Reason for exit.

        Returns:
            True if closed successfully.
        """
        with self.get_session() as session:
            stmt = select(PaperTrade).where(PaperTrade.id == trade_id)
            trade = session.scalar(stmt)

            if trade:
                trade.exit_price = exit_price
                trade.exit_time = exit_time
                trade.status = "closed"
                trade.result = result
                trade.exit_reason = exit_reason

                # Calculate PnL
                if trade.direction:
                    direction = trade.direction
                else:
                    # Get direction from signal
                    signal_stmt = select(Signal).where(Signal.id == trade.signal_id)
                    signal = session.scalar(signal_stmt)
                    direction = signal.direction if signal else "long"

                if direction == "long":
                    trade.pnl = (exit_price - trade.entry_price) * trade.quantity
                else:
                    trade.pnl = (trade.entry_price - exit_price) * trade.quantity

                trade.pnl_percent = (trade.pnl / (trade.entry_price * trade.quantity)) * 100

                session.commit()
                logger.info(f"Paper trade {trade_id} closed: {result}, PnL: {trade.pnl}")
                return True

            return False

    # ==================== MARKET SNAPSHOT OPERATIONS ====================

    def create_market_snapshot(
        self,
        signal_id: int,
        snapshot_data: dict[str, Any]
    ) -> MarketSnapshot:
        """
        Create a market snapshot.

        Args:
            signal_id: ID of related signal.
            snapshot_data: Snapshot data.

        Returns:
            Created MarketSnapshot object.
        """
        with self.get_session() as session:
            snapshot = MarketSnapshot(
                signal_id=signal_id,
                cvd=snapshot_data.get("cvd"),
                delta=snapshot_data.get("delta"),
                volume=snapshot_data.get("volume"),
                buy_imbalance_count=snapshot_data.get("buy_imbalance_count"),
                sell_imbalance_count=snapshot_data.get("sell_imbalance_count"),
                stacked_imbalance=snapshot_data.get("stacked_imbalance"),
                current_price=snapshot_data.get("current_price", 0),
                vah=snapshot_data.get("vah"),
                val=snapshot_data.get("val"),
                poc=snapshot_data.get("poc"),
                volatility=snapshot_data.get("volatility"),
                trend=snapshot_data.get("trend"),
                notes=snapshot_data.get("notes"),
            )
            session.add(snapshot)
            session.commit()
            session.refresh(snapshot)

            return snapshot

    # ==================== USER TRADE OPERATIONS ====================

    def create_user_trade(self, trade_data: dict[str, Any]) -> UserTrade:
        """
        Create a user trade.

        Args:
            trade_data: Trade data dictionary.

        Returns:
            Created UserTrade object.
        """
        with self.get_session() as session:
            trade = UserTrade(
                timestamp=trade_data.get("timestamp", 0),
                symbol=trade_data.get("symbol", ""),
                entry_price=trade_data.get("entry_price", 0),
                entry_time=trade_data.get("entry_time", 0),
                direction=trade_data.get("direction", ""),
                quantity=trade_data.get("quantity", 0.01),
                status=trade_data.get("status", "open"),
                trade_type=trade_data.get("trade_type", "manual"),
                notes=trade_data.get("notes"),
            )
            session.add(trade)
            session.commit()
            session.refresh(trade)

            logger.info(f"User trade created: {trade.id}")
            return trade

    # ==================== SYSTEM EVENT OPERATIONS ====================

    def log_event(
        self,
        event_type: str,
        message: str,
        severity: str = "INFO",
        details: str | None = None
    ) -> None:
        """
        Log a system event.

        Args:
            event_type: Type of event.
            message: Event message.
            severity: Event severity.
            details: Additional details.
        """
        with self.get_session() as session:
            event = SystemEvent(
                timestamp=int(datetime.now().timestamp() * 1000),
                event_type=event_type,
                severity=severity,
                message=message,
                details=details,
            )
            session.add(event)
            session.commit()

    # ==================== STATISTICS ====================

    def get_signal_statistics(self, symbol: str | None = None) -> dict[str, Any]:
        """
        Get signal statistics.

        Args:
            symbol: Optional symbol filter.

        Returns:
            Statistics dictionary.
        """
        with self.get_session() as session:
            if symbol:
                signals = session.scalars(
                    select(Signal).where(Signal.symbol == symbol)
                ).all()
            else:
                signals = session.scalars(select(Signal)).all()

            total = len(signals)
            if total == 0:
                return {"total": 0, "approved": 0, "rejected": 0, "pending": 0}

            approved = sum(1 for s in signals if s.status == "approved")
            rejected = sum(1 for s in signals if s.status == "rejected")
            pending = sum(1 for s in signals if s.status == "pending")

            avg_confidence = sum(s.confidence for s in signals) / total if total > 0 else 0

            return {
                "total": total,
                "approved": approved,
                "rejected": rejected,
                "pending": pending,
                "approval_rate": (approved / total * 100) if total > 0 else 0,
                "avg_confidence": avg_confidence,
            }

    def get_pnl_statistics(self) -> dict[str, Any]:
        """
        Get paper trading PnL statistics.

        Returns:
            PnL statistics dictionary.
        """
        with self.get_session() as session:
            trades = session.scalars(
                select(PaperTrade).where(PaperTrade.status == "closed")
            ).all()

            total = len(trades)
            if total == 0:
                return {
                    "total_trades": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "win_rate": 0,
                    "total_pnl": 0,
                    "avg_pnl": 0,
                }

            winning = sum(1 for t in trades if t.pnl and t.pnl > 0)
            losing = sum(1 for t in trades if t.pnl and t.pnl <= 0)
            total_pnl = sum(t.pnl for t in trades if t.pnl)

            return {
                "total_trades": total,
                "winning_trades": winning,
                "losing_trades": losing,
                "win_rate": (winning / total * 100) if total > 0 else 0,
                "total_pnl": total_pnl,
                "avg_pnl": total_pnl / total if total > 0 else 0,
            }

    def close(self) -> None:
        """Close database connections."""
        self.engine.dispose()
        logger.info("Database connection closed")

