# Architecture Documentation

## Overview

The Crypto Orderflow Trading Bot is built with a modular, event-driven architecture designed for real-time market data processing and signal generation.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Main Entry Point                          │
│                         (main.py)                                │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐    ┌─────────────────┐    ┌──────────────────┐
│   Database    │    │  WebSocket      │    │    Dashboard     │
│   Manager    │    │  Client         │    │    Server        │
└───────────────┘    └─────────────────┘    └──────────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Trading Bot Core   │
                    └───────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐    ┌─────────────────┐    ┌──────────────────┐
│  Orderflow   │    │   Strategy      │    │   Paper Trading │
│  Engines     │    │   Engine        │    │   Simulator      │
└───────────────┘    └─────────────────┘    └──────────────────┘
```

## Components

### 1. Core Layer (`core/`)

#### WebSocket Client (`websocket_client.py`)
- Connects to Binance/Bybit exchanges
- Handles real-time data streams (trade, kline, ticker)
- Automatic reconnection with exponential backoff
- Message parsing and dispatching

#### Market Data Handler (`market_data_handler.py`)
- Stores and manages real-time market data
- Maintains ticker information
- Tracks closed candles for historical analysis

#### Logging (`logging_config.py`)
- Centralized logging configuration
- Rotating file handlers
- Structured logging with context

### 2. Orderflow Layer (`orderflow/`)

The orderflow engines process raw trade data to extract meaningful patterns:

#### Delta Engine (`delta_engine.py`)
- Calculates real-time delta (Buy Volume - Sell Volume)
- Tracks delta per time period
- Detects delta spikes and divergences
- Maintains delta history

#### CVD Engine (`cvd_engine.py`)
- Cumulative Volume Delta tracking
- Detects CVD divergences with price
- Identifies trend reversals
- Records CVD swing highs/lows

#### Footprint Engine (`footprint_engine.py`)
- Tracks volume at price levels
- Builds order flow imbalances
- Identifies absorption patterns

#### Imbalance Detector (`imbalance_detector.py`)
- Detects buy/sell imbalances
- Identifies stacked imbalances
- Measures imbalance strength

#### Absorption Detector (`absorption_detector.py`)
- Identifies absorption zones
- Detects failed breakouts
- Tracks institutional activity

#### Liquidity Engine (`liquidity_engine.py`)
- Identifies liquidity pools
- Tracks stop hunt zones
- Detects liquidity grabs

### 3. Strategy Layer (`strategy/`)

#### Zone Detector (`zone_detector.py`)
- Identifies support/resistance zones
- Calculates Value Area High/Low
- Tracks Point of Control
- Detects swing highs/lows

#### Initiation Detector (`initiation_detector.py`)
- Identifies institutional buying/selling
- Detects first strong move after consolidation
- Confirms trend continuation

#### Pullback Detector (`pullback_detector.py`)
- Identifies pullback opportunities
- Confirms retest of zones
- Validates entry timing

#### Signal Builder (`signal_builder.py`)
- Combines all strategy components
- Calculates confidence scores
- Generates trade signals
- Manages risk/reward calculations

### 4. AI Layer (`ai/`)

#### Signal Explainer (`signal_explainer.py`)
- Generates human-readable explanations
- Provides trade context
- NOT used for signal generation (educational only)

### 5. Paper Trading Layer (`paper_trading/`)

#### Simulator (`simulator.py`)
- Executes virtual trades
- Manages open positions
- Tracks entry/exit prices
- Calculates P&L

#### PnL Tracker (`pnl_tracker.py`)
- Calculates performance metrics
- Tracks win/loss ratio
- Generates statistics

#### Signal Approval Handler (`signal_approval_handler.py`)
- Manages signal approval workflow
- Handles manual approvals
- Coordinates with simulator

### 6. Database Layer (`database/`)

#### Models (`models.py`)
- SQLAlchemy ORM models
- Signal, Position, Trade, SystemEvent

#### DB Manager (`db_manager.py`)
- Database operations
- CRUD for all entities
- Event logging

### 7. Dashboard Layer (`dashboard/`)

#### API Server (`api_server.py`)
- FastAPI application
- Dependency injection
- State management

#### Routes (`routes.py`)
- REST API endpoints
- Real-time data endpoints
- Signal management

#### Templates (`templates/index.html`)
- Interactive web UI
- Real-time updates
- Signal display

## Data Flow

### 1. Market Data Ingestion
```
WebSocket → Trade/Kline/Ticker Message
           ↓
    Parse Message
           ↓
    Update Orderflow Engines (Delta, CVD)
           ↓
    Store in Market Data Handler
           ↓
    Update Dashboard State
```

### 2. Strategy Analysis
```
Every 100 trades → Trigger Analysis
                   ↓
    Get Current Data (Price, Delta, CVD)
                   ↓
    Get Historical Candles
                   ↓
    Run Zone Detection
                   ↓
    Run Absorption Detection
                   ↓
    Run Imbalance Detection
                   ↓
    Run Initiation Detection
                   ↓
    Check Signal Conditions
                   ↓
    Generate Signal (if conditions met)
```

### 3. Signal Management
```
Signal Generated → Save to Database
                  ↓
    Request Approval (pending status)
                  ↓
    User Approves → Open Paper Trade
    User Rejects  → Log as Rejected
                  ↓
    Paper Trade → Monitor for Exit
                  ↓
    Exit Triggered → Close Position
                    ↓
    Calculate P&L → Update Statistics
```

## Configuration

Settings are managed through `config/settings.yaml`:

- Exchange configuration (symbols, intervals)
- Strategy parameters (confidence thresholds)
- Risk management (position sizing, stops)
- Dashboard settings (host, port)

## State Management

### Bot State
- Running/Stopped status
- Connection status
- Active pairs
- Current strategy

### Market Data State
- Live prices
- 24h change
- Volume

### Orderflow State
- Current CVD
- Current Delta
- Historical metrics

## Error Handling

- WebSocket disconnection: Automatic reconnection
- Database errors: Graceful degradation
- Invalid data: Skip and log
- Strategy errors: Catch and continue

## Performance Considerations

- Async/await for I/O operations
- Efficient data structures (deques for history)
- Minimal database writes
- Batch updates to dashboard state
- Connection pooling

## Testing

The architecture supports:
- Unit tests for individual components
- Integration tests for data flow
- Paper trading for strategy validation
- Dashboard for visual verification

