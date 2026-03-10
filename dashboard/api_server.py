"""
Dashboard API Server - FastAPI-based dashboard for the trading bot.

Provides REST API endpoints for:
- Signal management
- Trade history
- Performance statistics
- Market data
- System status
"""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import get_settings
from core.logging_config import get_logger

logger = get_logger("dashboard")


# Global references (will be set by main.py)
_simulator = None
_db_manager = None
_pnl_tracker = None

# Global bot state for dashboard
_bot_state = {
    "running": False,
    "connected": False,
    "current_strategy": "None",
    "active_pairs": [],
    "last_update": None,
    "market_data": {},
    "orderflow_metrics": {},
}


def set_dependencies(simulator: Any, db_manager: Any, pnl_tracker: Any) -> None:
    """
    Set global dependencies for the dashboard.

    Args:
        simulator: Paper trading simulator.
        db_manager: Database manager.
        pnl_tracker: PnL tracker.
    """
    global _simulator, _db_manager, _pnl_tracker
    _simulator = simulator
    _db_manager = db_manager
    _pnl_tracker = pnl_tracker


def update_bot_state(
    running: bool = None,
    connected: bool = None,
    current_strategy: str = None,
    active_pairs: list = None,
    market_data: dict = None,
    orderflow_metrics: dict = None
) -> None:
    """
    Update the global bot state for dashboard display.

    Args:
        running: Whether the bot is running.
        connected: WebSocket connection status.
        current_strategy: Currently active strategy.
        active_pairs: List of trading pairs.
        market_data: Current market data.
        orderflow_metrics: Current orderflow metrics.
    """
    global _bot_state
    import time
    
    if running is not None:
        _bot_state["running"] = running
    if connected is not None:
        _bot_state["connected"] = connected
    if current_strategy is not None:
        _bot_state["current_strategy"] = current_strategy
    if active_pairs is not None:
        _bot_state["active_pairs"] = active_pairs
    if market_data is not None:
        _bot_state["market_data"] = market_data
    if orderflow_metrics is not None:
        _bot_state["orderflow_metrics"] = orderflow_metrics
    
    _bot_state["last_update"] = int(time.time() * 1000)


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Application lifespan handler."""
    logger.info("Dashboard API starting up")
    yield
    logger.info("Dashboard API shutting down")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI app.
    """
    settings = get_settings()

    app = FastAPI(
        title="Crypto Trading Bot Dashboard",
        description="Local crypto order-flow trading signal platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    from dashboard.routes import router
    app.include_router(router)

    # Serve the dashboard HTML at root
    @app.get("/")
    async def root():
        """Root endpoint - serve the dashboard HTML."""
        from fastapi.responses import HTMLResponse
        import os
        
        # Get the path to the template
        template_path = os.path.join(
            os.path.dirname(__file__), 
            "templates", 
            "index.html"
        )
        
        try:
            with open(template_path, "r") as f:
                return HTMLResponse(content=f.read())
        except FileNotFoundError:
            return HTMLResponse(content="<h1>Dashboard template not found</h1>", status_code=500)

    # Also serve /docs for API documentation
    @app.get("/docs")
    async def docs():
        """API documentation redirect."""
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/api/docs")

    return app


# ==================== Pydantic Models ====================


class SignalResponse(BaseModel):
    """Signal response model."""

    id: str
    symbol: str
    direction: str
    entry_price: float
    stop_price: float
    tp1: float
    tp2: float
    confidence: float
    confidence_level: str
    reason: list[str]
    status: str
    timestamp: int


class TradeResponse(BaseModel):
    """Trade response model."""

    id: int
    symbol: str
    direction: str
    entry_price: float
    exit_price: float | None
    pnl: float | None
    pnl_percent: float | None
    status: str
    result: str | None
    entry_time: int
    exit_time: int | None


class StatsResponse(BaseModel):
    """Statistics response model."""

    total_signals: int
    approved_signals: int
    rejected_signals: int
    pending_signals: int
    approval_rate: float
    total_paper_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    avg_pnl: float


class PositionResponse(BaseModel):
    """Position response model."""

    id: int
    signal_id: str
    symbol: str
    direction: str
    entry_price: float
    quantity: float
    stop_price: float
    tp1: float
    tp2: float
    tp3: float
    unrealized_pnl: float
    entry_time: int


class ApprovalRequest(BaseModel):
    """Signal approval request."""

    signal_id: str
    approve: bool
    quantity: float | None = None
    reason: str | None = None


# ==================== API Routes ====================


def get_simulator():
    """Get the simulator instance."""
    if _simulator is None:
        raise HTTPException(status_code=503, detail="Simulator not initialized")
    return _simulator


def get_db_manager():
    """Get the database manager."""
    if _db_manager is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    return _db_manager


def get_pnl_tracker():
    """Get the PnL tracker."""
    if _pnl_tracker is None:
        raise HTTPException(status_code=503, detail="PnL tracker not initialized")
    return _pnl_tracker

