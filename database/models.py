"""
Database models for the crypto trading bot.

SQLAlchemy models for:
- Signals: Trading signals generated
- Paper Trades: Virtual paper trades
- Market Snapshots: Market state when signal occurred
- User Trades: User's manual trades
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class SignalDirectionEnum(str, Enum):
    """Signal direction enum."""

    LONG = "long"
    SHORT = "short"


class SignalStatusEnum(str, Enum):
    """Signal status enum."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    FILLED = "filled"
    CANCELLED = "cancelled"


class TradeStatusEnum(str, Enum):
    """Trade status enum."""

    OPEN = "open"
    CLOSED = "closed"
    TP_HIT = "tp_hit"
    SL_HIT = "sl_hit"
    CANCELLED = "cancelled"


class Signal(Base):
    """Trading signal model."""

    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    signal_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # Timestamp
    timestamp: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Symbol and direction
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)

    # Entry levels
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    stop_price: Mapped[float] = mapped_column(Float, nullable=False)
    tp1: Mapped[float] = mapped_column(Float, nullable=True)
    tp2: Mapped[float] = mapped_column(Float, nullable=True)
    tp3: Mapped[float] = mapped_column(Float, nullable=True)

    # Confidence
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_level: Mapped[str] = mapped_column(String(20), nullable=False)

    # Reason
    reason: Mapped[str] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SignalStatusEnum.PENDING.value,
        index=True
    )

    # Strategy info
    strategy: Mapped[str] = mapped_column(String(50), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)

    # User decision
    user_decision: Mapped[str] = mapped_column(String(20), nullable=True)
    decision_reason: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    paper_trades: Mapped[list["PaperTrade"]] = relationship(
        "PaperTrade", back_populates="signal", cascade="all, delete-orphan"
    )
    market_snapshot: Mapped["MarketSnapshot"] = relationship(
        "MarketSnapshot", back_populates="signal", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Signal(id={self.id}, {self.signal_id}, {self.symbol}, {self.direction}, {self.status})>"


class PaperTrade(Base):
    """Paper trade model - virtual trades."""

    __tablename__ = "paper_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Signal reference
    signal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("signals.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Trade details
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    exit_price: Mapped[float] = mapped_column(Float, nullable=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.01)

    # Timing
    entry_time: Mapped[int] = mapped_column(Integer, nullable=False)
    exit_time: Mapped[int] = mapped_column(Integer, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TradeStatusEnum.OPEN.value,
        index=True
    )

    # PnL
    pnl: Mapped[float] = mapped_column(Float, nullable=True)
    pnl_percent: Mapped[float] = mapped_column(Float, nullable=True)
    commission: Mapped[float] = mapped_column(Float, nullable=True, default=0.0)

    # Results
    result: Mapped[str] = mapped_column(String(20), nullable=True)
    exit_reason: Mapped[str] = mapped_column(String(50), nullable=True)

    # Relationships
    signal: Mapped["Signal"] = relationship("Signal", back_populates="paper_trades")

    def __repr__(self) -> str:
        return f"<PaperTrade(id={self.id}, signal={self.signal_id}, status={self.status}, pnl={self.pnl})>"


class MarketSnapshot(Base):
    """Market snapshot when signal was generated."""

    __tablename__ = "market_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Signal reference
    signal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("signals.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Orderflow metrics
    cvd: Mapped[float] = mapped_column(Float, nullable=True)
    delta: Mapped[float] = mapped_column(Float, nullable=True)
    volume: Mapped[float] = mapped_column(Float, nullable=True)

    # Imbalance counts
    buy_imbalance_count: Mapped[int] = mapped_column(Integer, nullable=True)
    sell_imbalance_count: Mapped[int] = mapped_column(Integer, nullable=True)
    stacked_imbalance: Mapped[Boolean] = mapped_column(Boolean, nullable=True)

    # Price levels
    current_price: Mapped[float] = mapped_column(Float, nullable=False)
    vah: Mapped[float] = mapped_column(Float, nullable=True)
    val: Mapped[float] = mapped_column(Float, nullable=True)
    poc: Mapped[float] = mapped_column(Float, nullable=True)

    # Additional context
    volatility: Mapped[float] = mapped_column(Float, nullable=True)
    trend: Mapped[str] = mapped_column(String(20), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    signal: Mapped["Signal"] = relationship("Signal", back_populates="market_snapshot")

    def __repr__(self) -> str:
        return f"<MarketSnapshot(id={self.id}, signal={self.signal_id}, price={self.current_price})>"


class UserTrade(Base):
    """User's manual trades."""

    __tablename__ = "user_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Trade details
    timestamp: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Entry
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    entry_time: Mapped[int] = mapped_column(Integer, nullable=False)

    # Exit
    exit_price: Mapped[float] = mapped_column(Float, nullable=True)
    exit_time: Mapped[int] = mapped_column(Integer, nullable=True)

    # Position
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TradeStatusEnum.OPEN.value,
        index=True
    )

    # PnL
    pnl: Mapped[float] = mapped_column(Float, nullable=True)
    pnl_percent: Mapped[float] = mapped_column(Float, nullable=True)

    # Notes
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    trade_type: Mapped[str] = mapped_column(String(20), nullable=True)  # "manual" or "signal"

    def __repr__(self) -> str:
        return f"<UserTrade(id={self.id}, {self.symbol}, {self.direction}, status={self.status})>"


class SystemEvent(Base):
    """System events and logs."""

    __tablename__ = "system_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    timestamp: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="INFO")

    # Event data
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<SystemEvent(id={self.id}, type={self.event_type}, severity={self.severity})>"

