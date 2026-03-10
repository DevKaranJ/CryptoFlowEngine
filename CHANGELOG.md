# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2024-01-XX

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

## [0.0.1] - 2024-01-01

### Added
- Project initialization
- Basic WebSocket client structure
- Initial database models

