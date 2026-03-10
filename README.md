# Crypto Order-Flow Trading Bot

A professional-grade local crypto order-flow trading signal platform written in Python. Designed for real-time market analysis using WebSocket data and advanced order-flow strategies.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Features

- **Real-time WebSocket Data**: Connect to Binance and Bybit exchanges
- **Orderflow Engine**: Delta, CVD, Imbalance, Absorption, Liquidity detection
- **Strategy Engine**: Zone detection, Initiation, Pullback confirmation
- **AI Signal Explainer**: Human-readable explanations (NOT signal generation)
- **Paper Trading**: Virtual trading with PnL tracking
- **Dashboard**: FastAPI-based web interface
- **Clean Architecture**: Modular, typed, documented, and testable

## Architecture

```
cryptobot/
├── core/              # WebSocket client, market data handling
├── orderflow/         # Delta, CVD, Imbalance, Absorption, Footprint
├── strategy/          # Zone, Initiation, Pullback, Signal Builder
├── ai/               # Signal Explainer (NOT signal generation)
├── paper_trading/    # Simulator, PnL Tracker
├── database/         # SQLAlchemy models
├── dashboard/        # FastAPI server & web UI
├── config/           # Configuration management
└── main.py           # Entry point
```

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd cryptobot

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -e .
```

### Running the Bot

```bash
python main.py
```

The bot will start:
1. Connect to Binance WebSocket
2. Stream real-time market data
3. Run strategy analysis
4. Start the dashboard

### Dashboard

Access the web dashboard at: **http://localhost:8000**

## API Endpoints

### Market Data

| Endpoint | Description |
|----------|-------------|
| `GET /api/bot/status` | Bot connection status |
| `GET /api/bot/market-data` | Live prices and orderflow metrics |
| `GET /api/bot/analysis/{symbol}` | Detailed analysis for a symbol |

### Signals

| Endpoint | Description |
|----------|-------------|
| `GET /api/signals` | List all trading signals |
| `GET /api/signals/{signal_id}` | Get signal details |
| `POST /api/signals/{signal_id}/approve` | Approve/reject a signal |

### Trades & Positions

| Endpoint | Description |
|----------|-------------|
| `GET /api/trades` | Get trade history |
| `GET /api/positions` | Get open positions |
| `POST /api/positions/{position_id}/close` | Close a position |

### Statistics

| Endpoint | Description |
|----------|-------------|
| `GET /api/statistics` | Overall performance stats |
| `GET /api/statistics/daily` | Daily P&L statistics |
| `GET /api/statistics/symbols` | Per-symbol statistics |

### System

| Endpoint | Description |
|----------|-------------|
| `GET /api/status` | System status |
| `GET /api/bot/logs` | Recent system logs |
| `GET /api/bot/strategies` | Active strategies |
| `POST /api/simulator/reset` | Reset paper trading |

## API Documentation

FastAPI auto-generates interactive API docs:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Configuration

Edit `config/settings.yaml` to customize:

```yaml
exchange:
  name: binance
  testnet: false
  symbols:
    - BTCUSDT
    - ETHUSDT
  intervals:
    - 1m
    - 15m

strategy:
  min_confidence: 50
  strong_confidence: 70

risk:
  default_risk_percent: 1.0
  min_risk_reward: 1.5

dashboard:
  host: 0.0.0.0
  port: 8000
```

## Strategy

The bot implements an order-flow reversal strategy:

1. **Zone Detection**: VAH, VAL, POC, swing highs/lows
2. **Absorption**: Aggressive side fails to move price
3. **CVD Divergence**: Delta/CVD diverges from price
4. **Stacked Imbalance**: Multiple levels with same imbalance
5. **Initiation Candle**: First strong candle after absorption
6. **Pullback**: Wait for retest before entry

### Signal Confidence Scoring

- Zone confluence: +25 points
- Absorption: +20 points
- CVD divergence: +20 points
- Stacked imbalance: +20 points
- Volume spike: +15 points

**Total**: 100 points
- >70 = Strong trade
- 50-70 = Medium
- <50 = Ignore

## Debugging & Verification

### Check Console Logs

The bot outputs detailed logs showing:
- Price, CVD, Delta, Volume for each symbol
- Zone detection results
- Absorption detection results
- Imbalance detection results
- Initiation detection results

### Check Dashboard API

Visit these URLs in your browser:
- `http://localhost:8000/api/bot/market-data` - Live price and orderflow
- `http://localhost:8000/api/bot/analysis/BTCUSDT` - BTC analysis
- `http://localhost:8000/api/signals` - All signals
- `http://localhost:8000/api/bot/logs` - System logs

### Understanding Orderflow Metrics

| Metric | Description | How to Verify |
|--------|-------------|---------------|
| **Delta** | Buy volume - Sell volume | Positive = buying pressure |
| **CVD** | Cumulative Volume Delta | Running total of delta |
| **Zones** | Support/Resistance | Check for near_support/resistance |
| **Absorption** | Large orders absorbed | detected=True |
| **Imbalance** | Buy/Sell imbalance | stacked=True |

## Paper Trading

Even if you reject a trade signal, the bot executes a paper trade internally to build a dataset for strategy evaluation.

## Docker

```bash
# Build and run with Docker
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Project Structure

```
cryptobot/
├── ai/                      # AI components
│   ├── __init__.py
│   └── signal_explainer.py  # Signal explanation generator
├── config/                  # Configuration
│   ├── __init__.py
│   └── settings.yaml        # User settings
├── core/                    # Core functionality
│   ├── __init__.py
│   ├── logging_config.py    # Logging setup
│   ├── market_data_handler.py
│   └── websocket_client.py  # Exchange connection
├── dashboard/               # Web dashboard
│   ├── __init__.py
│   ├── api_server.py       # FastAPI app
│   ├── routes.py           # API endpoints
│   └── templates/
│       └── index.html      # Web UI
├── database/               # Data persistence
│   ├── __init__.py
│   ├── db_manager.py
│   └── models.py           # SQLAlchemy models
├── docs/                   # Documentation
├── orderflow/              # Orderflow engines
│   ├── __init__.py
│   ├── absorption_detector.py
│   ├── cvd_engine.py
│   ├── delta_engine.py
│   ├── footprint_engine.py
│   ├── imbalance_detector.py
│   └── liquidity_engine.py
├── paper_trading/          # Paper trading
│   ├── __init__.py
│   ├── pnl_tracker.py
│   ├── simulator.py
│   └── signal_approval_handler.py
├── strategy/               # Trading strategies
│   ├── __init__.py
│   ├── initiation_detector.py
│   ├── pullback_detector.py
│   ├── signal_builder.py
│   └── zone_detector.py
├── data/                   # Local data storage
├── logs/                   # Log files
├── main.py                 # Entry point
├── run_dashboard.py        # Run dashboard only
├── pyproject.toml          # Project config
├── Dockerfile
└── docker-compose.yml
```

## Disclaimer

This is NOT financial advice. Always do your own research before trading. Use at your own risk. The paper trading feature is for educational and testing purposes only.

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

