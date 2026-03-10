# TODO - WebSocket Update

## Task: Update WebSocket settings to work correctly with Binance WebSocket streams

### Steps to Complete:

- [x] 1. Update Binance WebSocket URL to use combined streams endpoint (`/stream`)
- [x] 2. Add ping/pong handling for Binance's 20-second ping requirement
- [x] 3. Fix reconnection logic to properly re-subscribe to streams after reconnect
- [x] 4. Update message processing to handle combined stream format (`{"stream":"<streamName>","data":<rawPayload>}`)

### Changes Made:
- Updated websocket_client.py with proper Binance WebSocket configuration
- Updated settings.yaml to match Binance's ping requirements (20s interval, 30s timeout)
- Added explicit pong response handling for server pings
- Fixed reconnection subscription logic
- Updated message parsing for combined stream format

