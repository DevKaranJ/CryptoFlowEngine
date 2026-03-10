"""
Configuration module for the crypto trading bot.

This module handles loading and validating configuration from YAML files
and environment variables.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent


class ExchangeConfig(BaseSettings):
    """Exchange configuration settings."""

    name: str = Field(default="binance", description="Exchange name: binance or bybit")
    testnet: bool = Field(default=False, description="Use testnet")
    symbols: list[str] = Field(default=["BTCUSDT"], description="Trading symbols")
    intervals: list[str] = Field(default=["1m", "5m", "15m"], description="Candle intervals")


class WebSocketConfig(BaseSettings):
    """WebSocket connection settings."""

    reconnect_delay: int = Field(default=5, description="Delay between reconnects in seconds")
    max_reconnect_attempts: int = Field(default=10, description="Maximum reconnection attempts")
    ping_interval: int = Field(default=30, description="Ping interval in seconds")
    ping_timeout: int = Field(default=10, description="Ping timeout in seconds")


class OrderflowConfig(BaseSettings):
    """Orderflow engine settings."""

    footprint_window: int = Field(default=50, description="Number of price levels to track")
    imbalance_threshold: float = Field(default=3.0, description="Buy/Sell ratio for imbalance")
    stacked_imbalance_levels: int = Field(default=3, description="Consecutive levels for stacked imbalance")
    absorption_threshold: float = Field(default=0.7, description="Price close vs open for absorption")
    volume_spike_multiplier: float = Field(default=1.5, description="Volume spike detection multiplier")


class StrategyConfig(BaseSettings):
    """Strategy engine settings."""

    zone_lookback_candles: int = Field(default=100, description="Candles to look back for zones")
    zone_strength_threshold: int = Field(default=2, description="Zone strength threshold")
    min_confidence: int = Field(default=50, description="Minimum signal confidence")
    strong_confidence: int = Field(default=70, description="Strong signal confidence")
    pullback_candles: int = Field(default=3, description="Max candles to wait for pullback")


class RiskConfig(BaseSettings):
    """Risk management settings."""

    max_position_size: float = Field(default=0.1, description="Max % of balance per trade")
    default_risk_percent: float = Field(default=1.0, description="Risk per trade in %")
    min_risk_reward: float = Field(default=2.0, description="Minimum risk:reward ratio")
    max_daily_trades: int = Field(default=10, description="Maximum daily trades")


class PaperTradingConfig(BaseSettings):
    """Paper trading settings."""

    enabled: bool = Field(default=True, description="Enable paper trading")
    initial_balance: float = Field(default=10000, description="Initial paper trading balance")
    commission: float = Field(default=0.001, description="Commission rate (0.1%)")


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    path: str = Field(default="data/trading_bot.db", description="SQLite database path")
    backup_enabled: bool = Field(default=True, description="Enable database backup")
    backup_interval: int = Field(default=3600, description="Backup interval in seconds")


class DashboardConfig(BaseSettings):
    """Dashboard API settings."""

    host: str = Field(default="127.0.0.1", description="Dashboard host")
    port: int = Field(default=8000, description="Dashboard port")
    reload: bool = Field(default=False, description="Enable auto-reload")


class LoggingConfig(BaseSettings):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Log level")
    format: str = Field(
        default="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        description="Log format"
    )
    file: str = Field(default="logs/trading_bot.log", description="Log file path")
    max_bytes: int = Field(default=10485760, description="Max log file size (10MB)")
    backup_count: int = Field(default=5, description="Number of backup files")


class Settings(BaseSettings):
    """Main application settings."""

    exchange: ExchangeConfig = Field(default_factory=ExchangeConfig)
    websocket: WebSocketConfig = Field(default_factory=WebSocketConfig)
    orderflow: OrderflowConfig = Field(default_factory=OrderflowConfig)
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    paper_trading: PaperTradingConfig = Field(default_factory=PaperTradingConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    class Config:
        env_prefix = "CRYPTOBOT_"
        env_nested_delimiter = "__"


def load_settings(config_path: str | None = None) -> Settings:
    """
    Load settings from YAML file and environment variables.

    Args:
        config_path: Path to the config YAML file. If None, uses default.

    Returns:
        Settings object with loaded configuration.
    """
    if config_path is None:
        config_path = str(PROJECT_ROOT / "config" / "settings.yaml")

    config_file = Path(config_path)

    if not config_file.exists():
        # Return default settings if config file doesn't exist
        return Settings()

    with open(config_file, "r") as f:
        config_data: dict[str, Any] = yaml.safe_load(f)

    # Convert nested dicts to pydantic models
    settings_dict: dict[str, Any] = {}

    if "exchange" in config_data:
        settings_dict["exchange"] = ExchangeConfig(**config_data["exchange"])
    if "websocket" in config_data:
        settings_dict["websocket"] = WebSocketConfig(**config_data["websocket"])
    if "orderflow" in config_data:
        settings_dict["orderflow"] = OrderflowConfig(**config_data["orderflow"])
    if "strategy" in config_data:
        settings_dict["strategy"] = StrategyConfig(**config_data["strategy"])
    if "risk" in config_data:
        settings_dict["risk"] = RiskConfig(**config_data["risk"])
    if "paper_trading" in config_data:
        settings_dict["paper_trading"] = PaperTradingConfig(**config_data["paper_trading"])
    if "database" in config_data:
        settings_dict["database"] = DatabaseConfig(**config_data["database"])
    if "dashboard" in config_data:
        settings_dict["dashboard"] = DashboardConfig(**config_data["dashboard"])
    if "logging" in config_data:
        settings_dict["logging"] = LoggingConfig(**config_data["logging"])

    return Settings(**settings_dict)


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """
    Get the global settings instance.

    Returns:
        The global Settings object.
    """
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from config file.

    Returns:
        Reloaded Settings object.
    """
    global _settings
    _settings = load_settings()
    return _settings

