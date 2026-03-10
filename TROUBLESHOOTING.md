# Troubleshooting Guide

This guide covers common issues and their solutions.

## Table of Contents
1. [Connection Issues](#connection-issues)
2. [Dashboard Problems](#dashboard-problems)
3. [Data Issues](#data-issues)
4. [Performance Issues](#performance-issues)
5. [Database Issues](#database-issues)

---

## Connection Issues

### WebSocket Connection Failed

**Symptoms:**
- Console shows "Failed to connect to WebSocket"
- Dashboard shows "Disconnected" status

**Solutions:**
1. Check internet connection
2. Verify firewall isn't blocking the connection
3. Try using testnet: `exchange.testnet: true` in settings.yaml
4. Check if Binance is experiencing outages

### Can't Connect to Binance API

**Symptoms:**
- Connection errors in logs
- No market data received

**Solutions:**
1. Verify you're not rate-limited
2. Check if API keys are required (not needed for public data)
3. Try switching to testnet in config
4. Check network proxy settings

---

## Dashboard Problems

### Dashboard Shows "Waiting for data..."

**Explanation:**
This is normal behavior before the WebSocket connects. The dashboard shows default pairs with placeholder data.

**Solutions:**
1. Wait for the bot to fully start
2. Check console for connection status
3. Verify WebSocket is receiving data
4. Check browser console for errors (F12)

### Dashboard Not Loading

**Symptoms:**
- Blank page or 500 error

**Solutions:**
1. Check if port 8000 is available
2. Restart the dashboard: `python run_dashboard.py`
3. Check logs for errors
4. Verify templates/index.html exists

### API Endpoints Return Errors

**Symptoms:**
- 500 errors on API calls
- "Simulator not initialized" error

**Solutions:**
1. Make sure bot is started via `python main.py` (not just dashboard)
2. Check database is accessible
3. Verify all dependencies are installed

---

## Data Issues

### No Signals Being Generated

**Explanation:**
The strategy runs analysis every 100 trades. If no trades occur, no signals will be generated.

**Solutions:**
1. Verify WebSocket is receiving trade data
2. Check console for analysis output
3. Ensure trading pairs are active on exchange
4. Verify strategy parameters in settings.yaml

### Prices Show $0 or null

**Solutions:**
1. Check WebSocket connection status
2. Verify symbol is correct (e.g., BTCUSDT)
3. Check if ticker stream is working
4. Restart the bot

### Orderflow Metrics Showing null

**Explanation:**
Delta, CVD, and other orderflow metrics need trade data to calculate.

**Solutions:**
1. Wait for trades to accumulate
2. Check if trades are being processed
3. Verify delta/cvd engines are receiving data

---

## Performance Issues

### High CPU Usage

**Solutions:**
1. Reduce number of trading pairs
2. Increase analysis interval (modify in main.py)
3. Check for infinite loops in logs
4. Restart the bot

### Memory Leaks

**Solutions:**
1. Restart the bot periodically
2. Check database size (may need cleanup)
3. Reduce history buffer sizes

### Slow Dashboard Updates

**Solutions:**
1. Reduce refresh interval in dashboard
2. Check network latency
3. Close unused browser tabs

---

## Database Issues

### Database Locked Error

**Solutions:**
1. Close other connections to database
2. Restart the bot
3. Check file permissions

### Database Not Found

**Solutions:**
1. Create data directory: `mkdir data`
2. Check DATABASE_URL in config
3. Restart the bot to create new database

### Corrupted Database

**Solutions:**
1. Backup the database file
2. Delete the database file
3. Restart the bot (will create new database)

---

## Common Error Messages

### "Simulator not initialized"
- Bot not started properly
- Start with `python main.py`

### "Database not initialized"  
- Database connection failed
- Check DATABASE_URL setting

### "PnL tracker not initialized"
- Paper trading system not started
- Start with `python main.py`

### "Signal not found"
- Invalid signal ID
- Check signal list in dashboard

### "Position not found"
- Position already closed
- Check positions in dashboard

---

## Getting Help

If you're still experiencing issues:

1. Check the logs in `logs/` directory
2. Enable debug logging in settings.yaml
3. Visit the API docs: http://localhost:8000/docs
4. Check system logs: http://localhost:8000/api/bot/logs

---

## Debug Mode

To enable detailed debugging:

1. Edit `config/settings.yaml`:
```yaml
logging:
  level: DEBUG
```

2. Or set environment variable:
```bash
export LOG_LEVEL=DEBUG
```

3. Restart the bot

This will show:
- All WebSocket messages
- Detailed orderflow calculations
- Strategy analysis steps
- Database queries

