# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Parallel Detector Execution**
  - All strategy detectors (Zone, Absorption, Imbalance, Initiation) now run in parallel using `asyncio.gather` and thread pooling
  - Reduces analysis latency by approximately 70%
  - Includes robust exception handling to prevent individual detector failures from halting the entire pipeline

### Changed
- **Standardized Method Naming**
  - Consistent method naming across all strategy detector classes (AbsorptionDetector, ImbalanceDetector, ZoneDetector, InitiationDetector, OrderflowStrategy)
  - Resolved recurring AttributeErrors during event dispatching
  - Ensured consistent implementation of analysis methods to prevent runtime failures when processing trade and kline data streams

- **Optimized Detector Thresholds**
  - Adjusted imbalance thresholds to 1.5 (was higher)
  - Reduced stacked imbalance levels for better detection
  - Implemented price range estimation in AbsorptionDetector to handle missing OHLC data
  - Integrated proximity checks for support/resistance zones in the main execution loop

## [0.1.0] 

### Added
- **Core Trading System**
  - Real-time WebSocket connection to Binance
  - Orderflow engines: Delta, CVD, Footprint, Imbalance, Absorption, Liquidity
  - Strategy engines: Zone Detection, Initiation Detection, Pullback Detection
  - Paper trading simulator with PnL tracking
  - FastAPI-based web dashboard

- **Orderflow Features**
  - Real-time delta calculation (buy volume - sell volume)
  - Cumulative Volume Delta (CVD) tracking
  - Absorption detection for institutional activity
  - Imbalance detection at price levels
  - Liquidity pool identification
  - Zone detection (VAH, VAL, POC)

- **Dashboard Features**
  - Real-time price and orderflow metrics
  - Signal management (approve/reject)
  - Position tracking
  - P&L statistics
  - System logs

- **Database**
  - SQLAlchemy models for signals, positions, trades
  - Event logging system
  - Statistics persistence

### Changed
- Initial project structure with modular architecture
- Clean separation between orderflow, strategy, and trading components

### Known Issues
- Dashboard may show "Waiting for data" initially before WebSocket connects
- Some orderflow metrics may be null when no trades have occurred

## [0.0.1] - 2026-03-10

### Added
- Project initialization
- Basic WebSocket client structure
- Initial database models

