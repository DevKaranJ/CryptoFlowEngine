"""
WebSocket client for connecting to cryptocurrency exchanges.

This module provides async WebSocket connections to Binance and Bybit
for real-time market data streaming.
"""

import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

import websockets
from websockets.client import WebSocketClientProtocol

from config import get_settings
from core.logging_config import get_logger

logger = get_logger("websocket")


class Exchange(str, Enum):
    """Supported exchanges."""

    BINANCE = "binance"
    BYBIT = "bybit"


@dataclass
class StreamConfig:
    """Configuration for a data stream."""

    symbol: str
    interval: str
    stream_type: str  # trade, ticker, kline, depth


class WebSocketClient(ABC):
    """Abstract base class for exchange WebSocket clients."""

    def __init__(self, exchange: Exchange) -> None:
        """
        Initialize the WebSocket client.

        Args:
            exchange: The exchange to connect to.
        """
        self.exchange = exchange
        self.settings = get_settings()
        self._ws: WebSocketClientProtocol | None = None
        self._running = False
        self._reconnect_attempts = 0
        self._message_handlers: dict[str, list[Callable]] = {
            "trade": [],
            "ticker": [],
            "kline": [],
            "depth": [],
        }

    @abstractmethod
    def get_websocket_url(self) -> str:
        """Get the WebSocket connection URL for the exchange."""
        pass

    @abstractmethod
    def format_symbol(self, symbol: str) -> str:
        """Format the symbol for the exchange."""
        pass

    @abstractmethod
    def parse_trade(self, data: dict[str, Any]) -> dict[str, Any]:
        """Parse a trade message from the exchange."""
        pass

    @abstractmethod
    def parse_ticker(self, data: dict[str, Any]) -> dict[str, Any]:
        """Parse a ticker message from the exchange."""
        pass

    @abstractmethod
    def parse_kline(self, data: dict[str, Any]) -> dict[str, Any]:
        """Parse a kline (candle) message from the exchange."""
        pass

    def register_handler(self, stream_type: str, handler: Callable) -> None:
        """
        Register a handler for a specific stream type.

        Args:
            stream_type: Type of stream (trade, ticker, kline, depth).
            handler: Async callback function to handle messages.
        """
        if stream_type in self._message_handlers:
            self._message_handlers[stream_type].append(handler)
            logger.info(f"Registered handler for {stream_type} stream")
        else:
            logger.warning(f"Unknown stream type: {stream_type}")

    async def connect(self) -> bool:
        """
        Establish WebSocket connection to the exchange.

        Returns:
            True if connection successful, False otherwise.
        """
        try:
            url = self.get_websocket_url()
            logger.info(f"Connecting to {self.exchange.value} WebSocket at {url}")
            self._ws = await websockets.connect(
                url,
                ping_interval=self.settings.websocket.ping_interval,
                ping_timeout=self.settings.websocket.ping_timeout,
            )
            self._reconnect_attempts = 0
            logger.info(f"Connected to {self.exchange.value} WebSocket")
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False

    async def disconnect(self) -> None:
        """Close the WebSocket connection."""
        if self._ws:
            await self._ws.close()
            logger.info("WebSocket disconnected")

    async def subscribe(self, streams: list[StreamConfig]) -> None:
        """
        Subscribe to WebSocket streams.

        Args:
            streams: List of stream configurations to subscribe to.
        """
        if not self._ws:
            logger.error("Cannot subscribe: not connected")
            return

        subscribe_msg = self._build_subscribe_message(streams)
        await self._ws.send(json.dumps(subscribe_msg))
        logger.info(f"Subscribed to {len(streams)} streams")

    def _build_subscribe_message(self, streams: list[StreamConfig]) -> dict[str, Any]:
        """Build the subscription message for the exchange."""
        params = []
        for stream in streams:
            stream_name = f"{self.format_symbol(stream.symbol)}@{stream.stream_type}"
            if stream.stream_type == "kline":
                stream_name += f"_{stream.interval}"
            params.append(stream_name)
            logger.debug(f"Stream name: {stream_name}")

        subscribe_msg = {
            "method": "SUBSCRIBE",
            "params": params,
            "id": 1
        }
        logger.info(f"Subscribe message: {subscribe_msg}")
        return subscribe_msg

    async def listen(self) -> None:
        """Listen for and process WebSocket messages."""
        self._running = True
        logger.info("Starting WebSocket message listener")

        try:
            async for message in self._ws:
                if not self._running:
                    break
                await self._process_message(message)
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            await self._handle_reconnect()
        except Exception as e:
            logger.error(f"Error in listen loop: {e}")
            await self._handle_reconnect()

    async def _process_message(self, message: str) -> None:
        """
        Process incoming WebSocket message.

        Args:
            message: Raw WebSocket message string.
        """
        try:
            data = json.loads(message)

            # Handle subscription responses
            if "result" in data and data.get("result") is None:
                return

            # Determine message type and dispatch to handlers
            if "e" in data:
                event_type = data["e"]
                if event_type == "trade":
                    trade_data = self.parse_trade(data)
                    for handler in self._message_handlers["trade"]:
                        await handler(trade_data)
                elif event_type == "24hrTicker":
                    ticker_data = self.parse_ticker(data)
                    for handler in self._message_handlers["ticker"]:
                        await handler(ticker_data)
                elif event_type == "kline":
                    kline_data = self.parse_kline(data)
                    for handler in self._message_handlers["kline"]:
                        await handler(kline_data)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def _handle_reconnect(self) -> None:
        """Handle reconnection logic with exponential backoff."""
        if self._reconnect_attempts >= self.settings.websocket.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            return

        self._reconnect_attempts += 1
        delay = self.settings.websocket.reconnect_delay * (2 ** (self._reconnect_attempts - 1))
        logger.info(f"Reconnecting in {delay} seconds (attempt {self._reconnect_attempts})")

        await asyncio.sleep(delay)

        if await self.connect():
            logger.info("Reconnected successfully")
            # Re-subscribe to streams would go here
        else:
            logger.error("Reconnection failed")

    async def stop(self) -> None:
        """Stop the WebSocket listener."""
        self._running = False
        await self.disconnect()


class BinanceWebSocketClient(WebSocketClient):
    """WebSocket client for Binance exchange."""

    def __init__(self) -> None:
        """Initialize Binance WebSocket client."""
        super().__init__(Exchange.BINANCE)
        self._subscriptions: list[StreamConfig] = []  # Store subscriptions for reconnect

    def get_websocket_url(self) -> str:
        """
        Get Binance WebSocket URL.
        
        Uses combined streams endpoint (/stream) which wraps payloads in format:
        {"stream":"<streamName>","data":<rawPayload>}
        
        This is more reliable and follows Binance's recommended approach.
        """
        if self.settings.exchange.testnet:
            return "wss://testnet.binance.vision/ws"
        # Use combined streams endpoint for better reliability
        return "wss://stream.binance.com:9443/stream"

    def format_symbol(self, symbol: str) -> str:
        """Format symbol for Binance (lowercase)."""
        return symbol.lower()

    async def subscribe(self, streams: list[StreamConfig]) -> None:
        """
        Subscribe to WebSocket streams.
        
        Stores subscriptions for reconnection purposes.
        
        Args:
            streams: List of stream configurations to subscribe to.
        """
        # Store subscriptions for reconnect
        self._subscriptions = streams
        await super().subscribe(streams)

    async def _handle_reconnect(self) -> None:
        """Handle reconnection logic with exponential backoff."""
        if self._reconnect_attempts >= self.settings.websocket.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            return

        self._reconnect_attempts += 1
        delay = self.settings.websocket.reconnect_delay * (2 ** (self._reconnect_attempts - 1))
        logger.info(f"Reconnecting in {delay} seconds (attempt {self._reconnect_attempts})")

        await asyncio.sleep(delay)

        if await self.connect():
            logger.info("Reconnected successfully")
            # Re-subscribe to previously subscribed streams
            if self._subscriptions:
                logger.info(f"Re-subscribing to {len(self._subscriptions)} streams")
                await self.subscribe(self._subscriptions)
        else:
            logger.error("Reconnection failed")

    async def _process_message(self, message: str) -> None:
        """
        Process incoming WebSocket message.
        
        Handles both raw and combined stream formats:
        - Raw: {"e": "trade", "s": "BTCUSDT", ...}
        - Combined: {"stream": "btcusdt@trade", "data": {"e": "trade", "s": "BTCUSDT", ...}}

        Args:
            message: Raw WebSocket message string.
        """
        try:
            data = json.loads(message)

            # Handle subscription responses
            if "result" in data and data.get("result") is None:
                logger.debug(f"Subscription confirmed: {data.get('id')}")
                return
            
            # Check for errors
            if "error" in data:
                logger.error(f"WebSocket error: {data['error']}")
                return

            # Log raw message for debugging
            logger.debug(f"Received message: {message[:200]}...")

            # Handle combined stream format (from /stream endpoint)
            if "stream" in data and "data" in data:
                event_data = data["data"]
                stream_name = data["stream"]
                logger.debug(f"Combined stream: {stream_name}")
                await self._dispatch_event(event_data, stream_name)
            # Handle raw stream format (from /ws endpoint)
            elif "e" in data:
                logger.debug(f"Raw stream event: {data['e']}")
                await self._dispatch_event(data, "")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def _dispatch_event(self, data: dict[str, Any], stream_name: str) -> None:
        """
        Dispatch event to appropriate handlers based on event type.
        
        Args:
            data: The event data payload.
            stream_name: The stream name (for logging/debugging).
        """
        try:
            if "e" not in data:
                return
                
            event_type = data["e"]
            
            if event_type == "trade":
                trade_data = self.parse_trade(data)
                for handler in self._message_handlers["trade"]:
                    await handler(trade_data)
            elif event_type == "24hrTicker":
                ticker_data = self.parse_ticker(data)
                for handler in self._message_handlers["ticker"]:
                    await handler(ticker_data)
            elif event_type == "kline":
                kline_data = self.parse_kline(data)
                for handler in self._message_handlers["kline"]:
                    await handler(kline_data)
            elif event_type == "pong":
                # Handle pong response to our ping
                logger.debug(f"Received pong: {data}")
            else:
                logger.debug(f"Unknown event type: {event_type}")

        except Exception as e:
            logger.error(f"Error dispatching event: {e}")

    async def send_pong(self, payload: bytes = b"") -> None:
        """
        Send pong response to server ping.
        
        Binance sends a ping frame every 20 seconds. We must respond with
        a pong frame with the same payload within 1 minute to avoid disconnection.
        
        Note: The websockets library handles ping/pong automatically for WebSocket
        frames, but we can also send application-level pongs if needed.
        
        Args:
            payload: The payload from the ping (usually empty).
        """
        if self._ws:
            try:
                # Send pong with the same payload
                await self._ws.pong(payload)
                logger.debug("Sent pong response")
            except Exception as e:
                logger.error(f"Failed to send pong: {e}")

    def parse_trade(self, data: dict[str, Any]) -> dict[str, Any]:
        """Parse Binance trade message."""
        return {
            "symbol": data["s"],
            "price": float(data["p"]),
            "quantity": float(data["q"]),
            "side": "buy" if data["m"] is False else "sell",  # m=false means buy
            "timestamp": data["T"],
            "trade_id": data["t"],
        }

    def parse_ticker(self, data: dict[str, Any]) -> dict[str, Any]:
        """Parse Binance ticker message."""
        return {
            "symbol": data["s"],
            "last_price": float(data["c"]),
            "price_change": float(data["p"]),
            "price_change_percent": float(data["P"]),
            "high_price": float(data["h"]),
            "low_price": float(data["l"]),
            "volume": float(data["v"]),
            "quote_volume": float(data["q"]),
            "timestamp": data["E"],
        }

    def parse_kline(self, data: dict[str, Any]) -> dict[str, Any]:
        """Parse Binance kline (candle) message."""
        kline = data["k"]
        return {
            "symbol": kline["s"],
            "interval": kline["i"],
            "open_time": kline["t"],
            "open": float(kline["o"]),
            "high": float(kline["h"]),
            "low": float(kline["l"]),
            "close": float(kline["c"]),
            "volume": float(kline["v"]),
            "close_time": kline["T"],
            "is_closed": kline["x"],
        }


class BybitWebSocketClient(WebSocketClient):
    """WebSocket client for Bybit exchange."""

    def __init__(self) -> None:
        """Initialize Bybit WebSocket client."""
        super().__init__(Exchange.BYBIT)

    def get_websocket_url(self) -> str:
        """Get Bybit WebSocket URL."""
        if self.settings.exchange.testnet:
            return "wss://api-testnet.bybit.com/v5/public/spot"
        return "wss://stream.bybit.com/v5/public/spot"

    def format_symbol(self, symbol: str) -> str:
        """Format symbol for Bybit."""
        return symbol

    def parse_trade(self, data: dict[str, Any]) -> dict[str, Any]:
        """Parse Bybit trade message."""
        return {
            "symbol": data["s"],
            "price": float(data["p"]),
            "quantity": float(data["q"]),
            "side": data["S"].lower(),
            "timestamp": int(data["ts"]),
            "trade_id": data["i"],
        }

    def parse_ticker(self, data: dict[str, Any]) -> dict[str, Any]:
        """Parse Bybit ticker message."""
        return {
            "symbol": data["s"],
            "last_price": float(data["c"]),
            "price_change": float(data["c"]) - float(data["o"]),
            "price_change_percent": ((float(data["c"]) - float(data["o"])) / float(data["o"])) * 100,
            "high_price": float(data["h"]),
            "low_price": float(data["l"]),
            "volume": float(data["v"]),
            "quote_volume": float(data["q"]),
            "timestamp": data["t"],
        }

    def parse_kline(self, data: dict[str, Any]) -> dict[str, Any]:
        """Parse Bybit kline (candle) message."""
        kline = data["k"]
        return {
            "symbol": kline["s"],
            "interval": kline["i"],
            "open_time": int(kline["t"]),
            "open": float(kline["o"]),
            "high": float(kline["h"]),
            "low": float(kline["l"]),
            "close": float(kline["c"]),
            "volume": float(kline["v"]),
            "close_time": int(kline["T"]),
            "is_closed": kline["x"],
        }


def create_websocket_client(exchange: Exchange = Exchange.BINANCE) -> WebSocketClient:
    """
    Factory function to create a WebSocket client.

    Args:
        exchange: The exchange to connect to.

    Returns:
        A WebSocketClient instance for the specified exchange.
    """
    clients = {
        Exchange.BINANCE: BinanceWebSocketClient,
        Exchange.BYBIT: BybitWebSocketClient,
    }

    client_class = clients.get(exchange)
    if not client_class:
        raise ValueError(f"Unsupported exchange: {exchange}")

    return client_class()

