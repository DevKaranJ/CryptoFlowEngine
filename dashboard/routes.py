"""
Dashboard API Routes.

API endpoints for:
- Signals
- Trades
- Positions
- Statistics
- System
- Bot Status (real-time)
"""

from typing import Any

from fastapi import APIRouter, HTTPException

from dashboard.api_server import (
    ApprovalRequest,
    get_db_manager,
    get_pnl_tracker,
    get_simulator,
    _bot_state,
)

router = APIRouter(prefix="/api", tags=["Dashboard"])


# ==================== SIGNALS ====================


@router.get("/signals")
async def get_signals(limit: int = 50, status: str | None = None):
    """
    Get trading signals.

    Args:
        limit: Maximum number of signals to return.
        status: Filter by status (pending, approved, rejected).

    Returns:
        List of signals.
    """
    db = get_db_manager()

    try:
        signals = db.get_signals_by_symbol("", limit * 10)  # Get all then filter

        if status:
            signals = [s for s in signals if s.status == status]

        return {
            "signals": [
                {
                    "id": s.signal_id,
                    "symbol": s.symbol,
                    "direction": s.direction,
                    "entry_price": s.entry_price,
                    "stop_price": s.stop_price,
                    "tp1": s.tp1,
                    "tp2": s.tp2,
                    "confidence": s.confidence,
                    "confidence_level": s.confidence_level,
                    "reason": s.reason.split(", ") if s.reason else [],
                    "status": s.status,
                    "timestamp": s.timestamp,
                }
                for s in signals[:limit]
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/{signal_id}")
async def get_signal(signal_id: str):
    """
    Get a specific signal.

    Args:
        signal_id: Signal ID.

    Returns:
        Signal details.
    """
    db = get_db_manager()

    try:
        signal = db.get_signal_by_id(signal_id)
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")

        return {
            "id": signal.signal_id,
            "symbol": signal.symbol,
            "direction": signal.direction,
            "entry_price": signal.entry_price,
            "stop_price": signal.stop_price,
            "tp1": signal.tp1,
            "tp2": signal.tp2,
            "tp3": signal.tp3,
            "confidence": signal.confidence,
            "confidence_level": signal.confidence_level,
            "reason": signal.reason.split(", ") if signal.reason else [],
            "status": signal.status,
            "strategy": signal.strategy,
            "timeframe": signal.timeframe,
            "timestamp": signal.timestamp,
            "user_decision": signal.user_decision,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/signals/{signal_id}/approve")
async def approve_signal(signal_id: str, request: ApprovalRequest):
    """
    Approve or reject a signal.

    Args:
        signal_id: Signal ID.
        request: Approval request.

    Returns:
        Approval result.
    """
    simulator = get_simulator()

    try:
        if request.approve:
            position = simulator.approve_signal(signal_id, request.quantity)
            if position:
                return {
                    "success": True,
                    "message": "Signal approved",
                    "position_id": position.id,
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to open position",
                }
        else:
            simulator.reject_signal(signal_id, request.reason or "Manual rejection")
            return {
                "success": True,
                "message": "Signal rejected",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TRADES ====================


@router.get("/trades")
async def get_trades(limit: int = 50, status: str | None = None):
    """
    Get paper trades.

    Args:
        limit: Maximum number of trades.
        status: Filter by status (open, closed).

    Returns:
        List of trades.
    """
    simulator = get_simulator()

    try:
        if status == "open":
            trades = simulator.get_open_positions()
            return {
                "trades": [
                    {
                        "id": t.id,
                        "signal_id": t.signal_id,
                        "symbol": t.symbol,
                        "direction": t.direction,
                        "entry_price": t.entry_price,
                        "quantity": t.quantity,
                        "stop_price": t.stop_price,
                        "tp1": t.tp1,
                        "tp2": t.tp2,
                        "status": t.status,
                        "entry_time": t.entry_time,
                    }
                    for t in trades
                ]
            }
        else:
            trades = simulator.get_trade_history(limit)
            return {
                "trades": [
                    {
                        "id": t.position_id,
                        "signal_id": t.signal_id,
                        "symbol": t.symbol,
                        "direction": t.direction,
                        "entry_price": t.entry_price,
                        "exit_price": t.exit_price,
                        "quantity": t.quantity,
                        "pnl": t.pnl,
                        "pnl_percent": t.pnl_percent,
                        "result": t.result,
                        "entry_time": t.entry_time,
                        "exit_time": t.exit_time,
                    }
                    for t in trades
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trades/{trade_id}")
async def get_trade(trade_id: int):
    """
    Get a specific trade.

    Args:
        trade_id: Trade ID.

    Returns:
        Trade details.
    """
    simulator = get_simulator()

    try:
        trade = simulator.get_position(trade_id)
        if not trade:
            # Check history
            history = simulator.get_trade_history(100)
            trade = next((t for t in history if t.position_id == trade_id), None)
            if not trade:
                raise HTTPException(status_code=404, detail="Trade not found")

        return {
            "id": trade.id if hasattr(trade, "id") else trade.position_id,
            "symbol": trade.symbol,
            "direction": trade.direction,
            "entry_price": trade.entry_price,
            "exit_price": trade.exit_price if hasattr(trade, "exit_price") else None,
            "quantity": trade.quantity,
            "pnl": trade.pnl if hasattr(trade, "pnl") else None,
            "status": trade.status,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== STATISTICS ====================


@router.get("/statistics")
async def get_statistics():
    """
    Get comprehensive statistics.

    Returns:
        Statistics data.
    """
    db = get_db_manager()
    pnl_tracker = get_pnl_tracker()

    try:
        # Signal stats
        signal_stats = db.get_signal_statistics()

        # PnL stats
        pnl_stats = pnl_tracker.get_performance_metrics()
        daily_pnl = pnl_tracker.get_daily_stats()

        return {
            "signals": {
                "total": signal_stats["total"],
                "approved": signal_stats["approved"],
                "rejected": signal_stats["rejected"],
                "pending": signal_stats["pending"],
                "approval_rate": signal_stats.get("approval_rate", 0),
            },
            "trades": {
                "total": pnl_stats.total_trades,
                "winning": pnl_stats.winning_trades,
                "losing": pnl_stats.losing_trades,
                "win_rate": pnl_stats.win_rate,
                "total_pnl": pnl_stats.total_pnl,
                "avg_pnl": pnl_stats.avg_pnl,
                "profit_factor": pnl_stats.profit_factor,
            },
            "daily": daily_pnl,
            "balance": get_simulator().get_balance(),
            "equity": get_simulator().get_total_equity(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/daily")
async def get_daily_stats():
    """
    Get daily statistics.

    Returns:
        Daily stats.
    """
    pnl_tracker = get_pnl_tracker()

    try:
        return pnl_tracker.get_daily_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/symbols")
async def get_symbol_stats():
    """
    Get statistics by symbol.

    Returns:
        Per-symbol stats.
    """
    pnl_tracker = get_pnl_tracker()

    try:
        # Get unique symbols from trades
        trades = pnl_tracker.get_recent_trades(100)
        symbols = list(set(t.symbol for t in trades))

        return {
            symbol: pnl_tracker.get_symbol_stats(symbol)
            for symbol in symbols
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== POSITIONS ====================


@router.get("/positions")
async def get_positions():
    """
    Get all open positions.

    Returns:
        List of open positions.
    """
    simulator = get_simulator()

    try:
        positions = simulator.get_open_positions()
        return {
            "positions": [
                {
                    "id": p.id,
                    "signal_id": p.signal_id,
                    "symbol": p.symbol,
                    "direction": p.direction,
                    "entry_price": p.entry_price,
                    "quantity": p.quantity,
                    "stop_price": p.stop_price,
                    "tp1": p.tp1,
                    "tp2": p.tp2,
                    "tp3": p.tp3,
                    "entry_time": p.entry_time,
                }
                for p in positions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/positions/{position_id}/close")
async def close_position(position_id: int, exit_price: float, reason: str = "manual"):
    """
    Close a position.

    Args:
        position_id: Position ID to close.
        exit_price: Exit price.
        reason: Close reason.

    Returns:
        Close result.
    """
    simulator = get_simulator()

    try:
        result = simulator.close_position(position_id, exit_price, reason=reason)
        if result:
            return {
                "success": True,
                "pnl": result.pnl,
                "pnl_percent": result.pnl_percent,
                "result": result.result,
            }
        else:
            raise HTTPException(status_code=404, detail="Position not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SYSTEM ====================


@router.get("/status")
async def get_status():
    """
    Get system status.

    Returns:
        System status.
    """
    simulator = get_simulator()

    return {
        "status": "running",
        "balance": simulator.get_balance(),
        "equity": simulator.get_total_equity(),
        "open_positions": len(simulator.get_open_positions()),
    }


@router.post("/simulator/reset")
async def reset_simulator():
    """
    Reset the paper trading simulator.

    Returns:
        Reset result.
    """
    simulator = get_simulator()
    pnl_tracker = get_pnl_tracker()

    try:
        simulator.reset()
        pnl_tracker.reset()
        return {
            "success": True,
            "message": "Simulator reset successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== BOT STATUS (REAL-TIME) ====================


@router.get("/bot/status")
async def get_bot_status():
    """
    Get real-time bot status.

    Returns:
        Bot status including connection, running state, active pairs.
    """
    return _bot_state


@router.get("/bot/market-data")
async def get_market_data():
    """
    Get current market data for all pairs.

    Returns:
        Market data for each trading pair.
    """
    return {
        "market_data": _bot_state.get("market_data", {}),
        "orderflow_metrics": _bot_state.get("orderflow_metrics", {}),
    }


@router.get("/bot/analysis/{symbol}")
async def get_symbol_analysis(symbol: str):
    """
    Get detailed analysis for a specific symbol.

    Returns:
        Complete analysis data for the symbol.
    """
    simulator = get_simulator()
    pnl_tracker = get_pnl_tracker()
    db = get_db_manager()
    
    # Get orderflow data
    orderflow_metrics = _bot_state.get("orderflow_metrics", {}).get(symbol, {})
    market_data = _bot_state.get("market_data", {}).get(symbol, {})
    
    # Get recent signals for this symbol
    signals = db.get_signals_by_symbol(symbol, 10)
    
    return {
        "symbol": symbol,
        "market_data": market_data,
        "orderflow": {
            "cvd": orderflow_metrics.get("cvd", 0),
            "delta": orderflow_metrics.get("delta", 0),
        },
        "recent_signals": [
            {
                "id": s.signal_id,
                "direction": s.direction,
                "entry_price": s.entry_price,
                "confidence": s.confidence,
                "status": s.status,
                "timestamp": s.timestamp,
            }
            for s in signals
        ],
    }


@router.get("/bot/logs")
async def get_bot_logs(limit: int = 50):
    """
    Get recent bot logs.

    Args:
        limit: Maximum number of logs to return.

    Returns:
        List of recent system events.
    """
    db = get_db_manager()
    
    try:
        with db.get_session() as session:
            from sqlalchemy import select
            from database.models import SystemEvent
            
            stmt = (
                select(SystemEvent)
                .order_by(SystemEvent.timestamp.desc())
                .limit(limit)
            )
            events = session.scalars(stmt).all()
            
            return {
                "logs": [
                    {
                        "id": e.id,
                        "timestamp": e.timestamp,
                        "type": e.event_type,
                        "severity": e.severity,
                        "message": e.message,
                        "details": e.details,
                    }
                    for e in events
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bot/strategies")
async def get_active_strategies():
    """
    Get information about active strategies.

    Returns:
        List of strategies and their status.
    """
    from config import get_settings
    settings = get_settings()
    
    strategies = [
        {
            "name": "Orderflow Reversal",
            "description": "Detects orderflow imbalances and reversals",
            "pairs": settings.exchange.symbols,
            "timeframes": settings.exchange.intervals,
            "status": "active" if _bot_state.get("running") else "inactive",
        },
        {
            "name": "Zone Detection",
            "description": "Identifies support/resistance zones",
            "pairs": settings.exchange.symbols,
            "timeframes": settings.exchange.intervals,
            "status": "active" if _bot_state.get("running") else "inactive",
        },
        {
            "name": "Initiation Detection",
            "description": "Detects institutional buying/selling initiation",
            "pairs": settings.exchange.symbols,
            "status": "active" if _bot_state.get("running") else "inactive",
        },
    ]
    
    return {
        "current_strategy": _bot_state.get("current_strategy", "None"),
        "strategies": strategies,
    }

