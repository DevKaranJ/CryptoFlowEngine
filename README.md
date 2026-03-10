# Crypto Order-Flow Trading Bot

A professional-grade local crypto order-flow trading signal platform written in Python. Designed for real-time market analysis using WebSocket data and advanced order-flow strategies.

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
trading_bot/
├── core/              # WebSocket, market data handling
├── orderflow/         # Footprint, Delta, CVD, Imbalance, Absorption
├── strategy/          # Zone, Initiation, Pullback, Signal Builder
├── ai/               # Signal Explainer (NOT signal generation)
├── paper_trading/    # Simulator, PnL Tracker
├── database/         # SQLAlchemy models
├── dashboard/        # FastAPI server
├── config/           # Configuration
└── main.py           # Entry point
```

## Signal Workflow

```
WebSocket Data → Orderflow Engine → Strategy Engine → Signal Generation → AI Explanation → User Approval → Paper Trade → Logging
```

## Installation

### Prerequisites

- Python 3.11+
- pip or poetry

### Install Dependencies

```bash
pip install -e .
```

Or with Docker:

```bash
docker-compose up -d
```

## Configuration

Edit `config/settings.yaml` to customize:

- Exchange settings (Binance/Bybit)
- Symbols and intervals
- Orderflow parameters
- Risk management
- Paper trading settings

## Usage

### Running the Bot

```bash
python main.py
```

### Running with Docker

```bash
docker-compose up -d
```

### Dashboard

Access the dashboard at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

## Strategy

The bot implements an order-flow reversal strategy:

1. **Zone Detection**: VAH, VAL, POC, swing highs/lows
2. **Absorption**: Aggressive side fails to move price
3. **CVD Divergence**: Delta/CVD diverges from price
4. **Stacked Imbalance**: Multiple levels with same imbalance
5. **Initiation Candle**: First strong candle after absorption
6. **Pullback**: Wait for retest before entry

## Signal Confidence Scoring

- Zone confluence: +25 points
- Absorption: +20 points
- CVD divergence: +20 points
- Stacked imbalance: +20 points
- Volume spike: +15 points

**Total**: 100 points
- >70 = Strong trade
- 50-70 = Medium
- <50 = Ignore

## Paper Trading

Even if you reject a trade signal, the bot executes a paper trade internally to build a dataset for strategy evaluation.

## Disclaimer

This is NOT financial advice. Always do your own research before trading. Use at your own risk.

## License

MIT License

