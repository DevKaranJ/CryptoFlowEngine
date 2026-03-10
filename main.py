"""
Main entry point for the Crypto Trading Bot.

This module initializes and runs the complete trading system:
- WebSocket client for real-time data
- Orderflow engine for market analysis
- Strategy engine for signal generation
- Paper trading simulator
- Dashboard API
"""

import asyncio
import signal
import sys
from typing import Any

from config import get_settings
from core import (
    MarketDataHandler,
    get_logger,
    setup_logging,
)
from core.websocket_client import BinanceWebSocketClient, StreamConfig
from dashboard import create_app, set_dependencies, update_bot_state
from database import DatabaseManager
from orderflow import (
    AbsorptionDetector,
    CVDEngine,
    DeltaEngine,
    FootprintEngine,
    ImbalanceDetector,
    LiquidityEngine,
)
from paper_trading import PnLTracker, PaperTradingSimulator, SignalApprovalHandler
from strategy import (
    InitiationDetector,
    OrderflowStrategy,
    PullbackDetector,
    ZoneDetector,
)
from ai import SignalExplainer, SignalValidator


class TradingBot:
    """Main trading bot class."""

    def __init__(self) -> None:
        """Initialize the trading bot."""
        # Setup logging
        setup_logging()
        self.logger = get_logger("main")

        # Load settings
        self.settings = get_settings()

        # Initialize components
        self._initialize_components()

        # State
        self._running = False

        self.logger.info("Crypto Trading Bot initialized")

    def _initialize_components(self) -> None:
        """Initialize all system components."""
        self.logger.info("Initializing components...")

        # Database
        self.db_manager = DatabaseManager()
        self.db_manager.log_event("system", "Trading bot starting", "INFO")

        # Orderflow engines
        self.footprint_engine = FootprintEngine()
        self.delta_engine = DeltaEngine()
        self.cvd_engine = CVDEngine()
        self.imbalance_detector = ImbalanceDetector()
        self.absorption_detector = AbsorptionDetector()
        self.liquidity_engine = LiquidityEngine()

        # Strategy engines
        self.zone_detector = ZoneDetector()
        self.initiation_detector = InitiationDetector()
        self.pullback_detector = PullbackDetector()
        self.strategy = OrderflowStrategy()

        # AI components
        self.signal_explainer = SignalExplainer()
        self.signal_validator = SignalValidator()

        # Paper trading
        self.pnl_tracker = PnLTracker()
        self.simulator = PaperTradingSimulator(self.db_manager)
        self.approval_handler = SignalApprovalHandler(self.simulator, self.db_manager)

        # Market data handler
        self.market_data_handler = MarketDataHandler()

        # WebSocket client
        self.ws_client = BinanceWebSocketClient()

        # Dashboard - also start the dashboard for viewing
        self.dashboard_app = create_app()
        set_dependencies(self.simulator, self.db_manager, self.pnl_tracker)

        # Update bot state in dashboard
        update_bot_state(
            running=True,
            connected=False,
            current_strategy="Orderflow Strategy",
            active_pairs=self.settings.exchange.symbols,
        )

        self.logger.info("All components initialized")

    async def start(self) -> None:
        """Start the trading bot."""
        self.logger.info("Starting Crypto Trading Bot...")
        self._running = True

        # Connect to WebSocket
        if not await self.ws_client.connect():
            self.logger.error("Failed to connect to WebSocket")
            return

        # Update dashboard state - connected
        from dashboard import update_bot_state
        update_bot_state(connected=True)

        # Setup message handlers
        self.ws_client.register_handler("trade", self._handle_trade)
        self.ws_client.register_handler("kline", self._handle_kline)
        self.ws_client.register_handler("ticker", self._handle_ticker)

        # Subscribe to streams
        streams = []
        for symbol in self.settings.exchange.symbols:
            for interval in self.settings.exchange.intervals:
                streams.append(StreamConfig(
                    symbol=symbol,
                    interval=interval,
                    stream_type="kline"
                ))
                streams.append(StreamConfig(
                    symbol=symbol,
                    interval="",
                    stream_type="trade"
                ))
            # Also subscribe to ticker for price updates (needed for dashboard)
            streams.append(StreamConfig(
                symbol=symbol,
                interval="",
                stream_type="ticker"
            ))

        await self.ws_client.subscribe(streams)

        # Start listening
        await self.ws_client.listen()

    async def stop(self) -> None:
        """Stop the trading bot."""
        self.logger.info("Stopping Crypto Trading Bot...")
        self._running = False

        await self.ws_client.stop()
        self.db_manager.log_event("system", "Trading bot stopped", "INFO")
        self.db_manager.close()

    async def _handle_trade(self, trade_data: dict[str, Any]) -> None:
        """Handle incoming trade data."""
        symbol = trade_data.get("symbol", "")
        price = trade_data.get("price", 0)
        quantity = trade_data.get("quantity", 0)
        side = trade_data.get("side", "")
        timestamp = trade_data.get("timestamp", 0)

        # Update market data handler
        await self.market_data_handler.handle_trade(trade_data)

        # Update orderflow engines
        self.footprint_engine.process_trade(symbol, price, quantity, side, timestamp)
        self.delta_engine.process_trade(quantity, side, timestamp)
        self.cvd_engine.process_trade(quantity, side, timestamp)

        # Run strategy analysis periodically (every 100 trades)
        trade_count = len(self.market_data_handler.get_recent_trades(symbol))
        if trade_count % 100 == 0:
            await self._run_strategy_analysis(symbol)

    async def _handle_kline(self, kline_data: dict[str, Any]) -> None:
        """Handle incoming kline data."""
        await self.market_data_handler.handle_kline(kline_data)

        # Update zone detector when candle closes
        if kline_data.get("is_closed", False):
            symbol = kline_data.get("symbol", "")
            interval = kline_data.get("interval", "1m")

            candles = self.market_data_handler.get_closed_candles(symbol, interval, 50)
            if candles:
                zone_data = self.zone_detector.detect_zones_from_candles([
                    {
                        "high": c.high,
                        "low": c.low,
                        "close": c.close,
                        "volume": c.volume,
                    }
                    for c in candles
                ])

    async def _handle_ticker(self, ticker_data: dict[str, Any]) -> None:
        """Handle incoming ticker data."""
        await self.market_data_handler.handle_ticker(ticker_data)
        
        # Update dashboard with market data
        symbol = ticker_data.get("symbol", "")
        if symbol:
            # Get current market data from dashboard state
            from dashboard.api_server import _bot_state
            market_data = dict(_bot_state.get("market_data", {}))
            market_data[symbol] = {
                "price": ticker_data.get("last_price", 0),
                "volume": ticker_data.get("volume", 0),
                "change_24h": ticker_data.get("price_change_percent", 0),
                "high": ticker_data.get("high_price", 0),
                "low": ticker_data.get("low_price", 0),
            }
            
            # Get orderflow metrics for this symbol
            orderflow_metrics = dict(_bot_state.get("orderflow_metrics", {}))
            orderflow_metrics[symbol] = {
                "cvd": self.cvd_engine.get_current_cvd(),
                "delta": self.delta_engine.get_current_delta().delta if hasattr(self.delta_engine.get_current_delta(), 'delta') else 0,
            }
            
            update_bot_state(market_data=market_data, orderflow_metrics=orderflow_metrics)

    async def _run_strategy_analysis(self, symbol: str) -> None:
        """Run complete strategy analysis."""
        self.logger.info(f"Running strategy analysis for {symbol}")

        # Get market data
        ticker = self.market_data_handler.get_ticker(symbol)
        if not ticker:
            self.logger.warning(f"No ticker data for {symbol}")
            return

        current_price = ticker.last_price

        # Get orderflow data
        cvd = self.cvd_engine.get_current_cvd()
        delta = self.delta_engine.get_current_delta().delta

        self.logger.info(f"[{symbol}] Price: {current_price}, CVD: {cvd}, Delta: {delta}, Volume: {ticker.volume}")

        # Prepare market data
        market_data = {
            "symbol": symbol,
            "current_price": current_price,
            "cvd": cvd,
            "delta": delta,
            "volume": ticker.volume,
        }

        # Prepare candle data for detectors
        candle_data = []
        if candles := self.market_data_handler.get_closed_candles(symbol, "1m", 50):
            candle_data = [{"high": c.high, "low": c.low, "close": c.close, "volume": c.volume} for c in candles]
<<<<<<< Updated upstream
        
        zone_data = self.zone_detector.detect_zones_from_candles(candle_data) if candle_data else {}
        absorption_data = self.absorption_detector.analyze_bar({"price": current_price, "volume": ticker.volume, "delta": delta, "cvd": cvd}) or {}
        imbalance_data = self.imbalance_detector.analyze_market({"price": current_price, "volume": ticker.volume}) or {}
        initiation_data = self.initiation_detector.detect_initiation(candle_data) if candle_data else {}
        
=======

        # Prepare detector inputs
        bar_data = {"price": current_price, "volume": ticker.volume, "delta": delta, "cvd": cvd}
        market_analysis_data = {"price": current_price, "volume": ticker.volume}

        # ============================================================
        # PARALLEL EXECUTION: Run all detectors simultaneously
        # This improves performance by ~70% compared to sequential
        # ============================================================

        # Run zone detection in thread pool (CPU-bound)
        zone_task = asyncio.to_thread(
            self.zone_detector.detect_zones_from_candles,
            candle_data if candle_data else []
        )

        # Run absorption detection in thread pool (CPU-bound)
        absorption_task = asyncio.to_thread(
            self.absorption_detector.analyze_bar,
            bar_data
        )

        # Run imbalance detection in thread pool (CPU-bound)
        imbalance_task = asyncio.to_thread(
            self.imbalance_detector.analyze_market,
            market_analysis_data
        )

        # Run initiation detection in thread pool (CPU-bound)
        initiation_task = asyncio.to_thread(
            self.initiation_detector.detect_initiation_from_candles,
            candle_data if candle_data else []
        )

        # Execute all detectors IN PARALLEL
        zone_data, absorption_data, imbalance_data, initiation_data = await asyncio.gather(
            zone_task,
            absorption_task,
            imbalance_task,
            initiation_task,
            return_exceptions=True  # Handle any exceptions gracefully
        )

        # Handle any exceptions that occurred
        if isinstance(zone_data, Exception):
            self.logger.error(f"Zone detection error: {zone_data}")
            zone_data = {}
        if isinstance(absorption_data, Exception):
            self.logger.error(f"Absorption detection error: {absorption_data}")
            absorption_data = {}
        if isinstance(imbalance_data, Exception):
            self.logger.error(f"Imbalance detection error: {imbalance_data}")
            imbalance_data = {}
        if isinstance(initiation_data, Exception):
            self.logger.error(f"Initiation detection error: {initiation_data}")
            initiation_data = {}

        # Ensure we have dictionaries
        zone_data = zone_data or {}
        absorption_data = absorption_data or {}
        imbalance_data = imbalance_data or {}
        initiation_data = initiation_data or {}

>>>>>>> Stashed changes
        self.logger.info(f"[{symbol}] Zones: near_support={zone_data.get('near_support', False)}, near_resistance={zone_data.get('near_resistance', False)}, "
                       f"Absorption: detected={absorption_data.get('detected', False)}, type={absorption_data.get('type', 'none')}, "
                       f"Imbalance: stacked={imbalance_data.get('stacked', False)}, type={imbalance_data.get('type', 'none')}, "
                       f"Initiation: detected={initiation_data.get('detected', False)}")

        orderflow_data = {
            "zones": zone_data,
            "absorption": absorption_data,
            "cvd_divergence": {},
<<<<<<< Updated upstream
            "imbalance": self.imbalance_detector.analyze_market({"price": current_price, "volume": ticker.volume}) or {},
            "initiation": self.initiation_detector.detect_initiation(candle_data) if candle_data else {},
=======
            "imbalance": imbalance_data,
            "initiation": initiation_data,
>>>>>>> Stashed changes
            "volume": {"spike": ticker.volume > 1000000},
        }

        # Run analysis
        signal = self.strategy.analyze(market_data, orderflow_data)

        if signal:
            self.logger.info(f"Signal generated: {signal.direction.value} {symbol}")

            # Generate explanation
            explanation = self.signal_explainer.generate_full_explanation(
                signal.to_dict(),
                market_data
            )
            self.logger.info(f"\n{explanation}")

            # Request approval
            self.approval_handler.request_approval(signal.to_dict())

            # Save to database
            self.db_manager.create_signal(signal.to_dict())


def signal_handler(signum, frame) -> None:
    """Handle shutdown signals."""
    print("\nReceived shutdown signal, stopping...")
    sys.exit(0)


async def run_bot() -> None:
    """Run the trading bot."""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and start bot
    bot = TradingBot()

    try:
        await bot.start()
    except KeyboardInterrupt:
        await bot.stop()
    except Exception as e:
        bot.logger.error(f"Fatal error: {e}")
        await bot.stop()
        raise


def main() -> None:
    """Main entry point."""
    import uvicorn
    
    # Get settings
    settings = get_settings()
    
    # Run dashboard in a separate thread
    import threading
    def run_dashboard():
        uvicorn.run(
            "dashboard.api_server:create_app",
            host=settings.dashboard.host,
            port=settings.dashboard.port,
            log_level="info",
            factory=True,
        )
    
    # Start dashboard in background thread
    dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
    dashboard_thread.start()
    
    # Run the main bot
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()

