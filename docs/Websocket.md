WebSocket Streams for Binance
General WSS information
The base endpoint is: wss://stream.binance.com:9443 or wss://stream.binance.com:443.
Streams can be accessed either in a single raw stream or in a combined stream.
Raw streams are accessed at /ws/<streamName>
Combined streams are accessed at /stream?streams=<streamName1>/<streamName2>/<streamName3>
Combined stream events are wrapped as follows: {"stream":"<streamName>","data":<rawPayload>}
All symbols for streams are lowercase
A single connection to stream.binance.com is only valid for 24 hours; expect to be disconnected at the 24 hour mark
The WebSocket server will send a ping frame every 20 seconds.
If the WebSocket server does not receive a pong frame back from the connection within a minute the connection will be disconnected.
When you receive a ping, you must send a pong with a copy of ping's payload as soon as possible.
Unsolicited pong frames are allowed, but will not prevent disconnection. It is recommended that the payload for these pong frames are empty.
The base endpoint wss://data-stream.binance.vision can be subscribed to receive only market data messages.
User data stream is NOT available from this URL.
All time and timestamp related fields are milliseconds by default. To receive the information in microseconds, please add the parameter timeUnit=MICROSECOND or timeUnit=microsecond in the URL.
For example: /stream?streams=btcusdt@trade&timeUnit=MICROSECOND
If your request contains a symbol name containing non-ASCII characters, then the stream events may contain non-ASCII characters encoded in UTF-8.
[All Market Mini Tickers Stream](#all-market-mini-tickers-stream and All Market Rolling Window Statistics Streams events may contain non-ASCII characters encoded in UTF-8.
WebSocket Limits
WebSocket connections have a limit of 5 incoming messages per second. A message is considered:
A PING frame
A PONG frame
A JSON controlled message (e.g. subscribe, unsubscribe)
A connection that goes beyond the limit will be disconnected; IPs that are repeatedly disconnected may be banned.
A single connection can listen to a maximum of 1024 streams.
There is a limit of 300 connections per attempt every 5 minutes per IP.
Live Subscribing/Unsubscribing to streams
The following data can be sent through the WebSocket instance in order to subscribe/unsubscribe from streams. Examples can be seen below.
The id is used as an identifier to uniquely identify the messages going back and forth. The following formats are accepted:
64-bit signed integer
alphanumeric strings; max length 36
null
In the response, if the result received is null this means the request sent was a success for non-query requests (e.g. Subscribing/Unsubscribing).
Subscribe to a stream
Request

{
    "method": "SUBSCRIBE",
    "params": ["btcusdt@aggTrade", "btcusdt@depth"],
    "id": 1
}

Response

{
    "result": null,
    "id": 1
}

Unsubscribe to a stream
Request

{
    "method": "UNSUBSCRIBE",
    "params": ["btcusdt@depth"],
    "id": 312
}

Response

{
    "result": null,
    "id": 312
}

Listing Subscriptions
Request

{
    "method": "LIST_SUBSCRIPTIONS",
    "id": 3
}

Response

{
    "result": ["btcusdt@aggTrade"],
    "id": 3
}

Setting Properties
Currently, the only property that can be set is whether combined stream payloads are enabled or not. The combined property is set to false when connecting using /ws/ ("raw streams") and true when connecting using /stream/.

Request

{
    "method": "SET_PROPERTY",
    "params": ["combined", true],
    "id": 5
}

Response

{
    "result": null,
    "id": 5
}

Retrieving Properties
Request

{
    "method": "GET_PROPERTY",
    "params": ["combined"],
    "id": 2
}

Response

{
    "result": true, // Indicates that combined is set to true.
    "id": 2
}

Error Messages
Error Message	Description
{"code": 0, "msg": "Unknown property","id": %s}	Parameter used in the SET_PROPERTY or GET_PROPERTY was invalid
{"code": 1, "msg": "Invalid value type: expected Boolean"}	Value should only be true or false
{"code": 2, "msg": "Invalid request: property name must be a string"}	Property name provided was invalid
{"code": 2, "msg": "Invalid request: request ID must be an unsigned integer"}	Parameter id had to be provided or the value provided in the id parameter is an unsupported type
{"code": 2, "msg": "Invalid request: unknown variant %s, expected one of SUBSCRIBE, UNSUBSCRIBE, LIST_SUBSCRIPTIONS, SET_PROPERTY, GET_PROPERTY at line 1 column 28"}	Possible typo in the provided method or provided method was neither of the expected values
{"code": 2, "msg": "Invalid request: too many parameters"}	Unnecessary parameters provided in the data
{"code": 2, "msg": "Invalid request: property name must be a string"}	Property name was not provided
{"code": 2, "msg": "Invalid request: missing field method at line 1 column 73"}	method was not provided in the data
{"code":3,"msg":"Invalid JSON: expected value at line %s column %s"}	JSON data sent has incorrect syntax.
Detailed Stream information
Reference Price Streams
Stream Name: <symbol>@referencePrice

Update Speed: 1000ms

Payload:

{
  "e": "referencePrice",  // eventType
  "s": "BAZUSD",          // symbol
  "r": "1.00",            // reference price (null if no reference price)
  "t": 1770313263917      // engine timestamp when reference price was valid
}

Aggregate Trade Streams
The Aggregate Trade Streams push trade information that is aggregated for a single taker order.

Stream Name: <symbol>@aggTrade

Update Speed: Real-time

Payload:

{
    "e": "aggTrade",        // Event type
    "E": 1672515782136,     // Event time
    "s": "BNBBTC",          // Symbol
    "a": 12345,             // Aggregate trade ID
    "p": "0.001",           // Price
    "q": "100",             // Quantity
    "f": 100,               // First trade ID
    "l": 105,               // Last trade ID
    "T": 1672515782136,     // Trade time
    "m": true,              // Is the buyer the market maker?
    "M": true               // Ignore
}

Trade Streams
The Trade Streams push raw trade information; each trade has a unique buyer and seller.

Stream Name: <symbol>@trade

Update Speed: Real-time

Payload:

{
    "e": "trade",           // Event type
    "E": 1672515782136,     // Event time
    "s": "BNBBTC",          // Symbol
    "t": 12345,             // Trade ID
    "p": "0.001",           // Price
    "q": "100",             // Quantity
    "T": 1672515782136,     // Trade time
    "m": true,              // Is the buyer the market maker?
    "M": true               // Ignore
}

Kline/Candlestick Streams for UTC
The Kline/Candlestick Stream push updates to the current klines/candlestick every second in UTC+0 timezone

Kline/Candlestick chart intervals:

s-> seconds; m -> minutes; h -> hours; d -> days; w -> weeks; M -> months

1s
1m
3m
5m
15m
30m
1h
2h
4h
6h
8h
12h
1d
3d
1w
1M
Stream Name: <symbol>@kline_<interval>

Update Speed: 1000ms for 1s, 2000ms for the other intervals

Payload:

{
    "e": "kline",               // Event type
    "E": 1672515782136,         // Event time
    "s": "BNBBTC",              // Symbol
    "k": {
        "t": 1672515780000,     // Kline start time
        "T": 1672515839999,     // Kline close time
        "s": "BNBBTC",          // Symbol
        "i": "1m",              // Interval
        "f": 100,               // First trade ID
        "L": 200,               // Last trade ID
        "o": "0.0010",          // Open price
        "c": "0.0020",          // Close price
        "h": "0.0025",          // High price
        "l": "0.0015",          // Low price
        "v": "1000",            // Base asset volume
        "n": 100,               // Number of trades
        "x": false,             // Is this kline closed?
        "q": "1.0000",          // Quote asset volume
        "V": "500",             // Taker buy base asset volume
        "Q": "0.500",           // Taker buy quote asset volume
        "B": "123456"           // Ignore
    }
}

Kline/Candlestick Streams with timezone offset
The Kline/Candlestick Stream push updates to the current klines/candlestick every second in UTC+8 timezone

Kline/Candlestick chart intervals:

Supported intervals: See Kline/Candlestick chart intervals

UTC+8 timezone offset:

Kline intervals open and close in the UTC+8 timezone. For example the 1d klines will open at the beginning of the UTC+8 day, and close at the end of the UTC+8 day.
Note that E (event time), t (start time) and T (close time) in the payload are Unix timestamps, which are always interpreted in UTC.
Stream Name: <symbol>@kline_<interval>@+08:00

Update Speed: 1000ms for 1s, 2000ms for the other intervals

Payload:

{
    "e": "kline",               // Event type
    "E": 1672515782136,         // Event time
    "s": "BNBBTC",              // Symbol
    "k": {
        "t": 1672515780000,     // Kline start time
        "T": 1672515839999,     // Kline close time
        "s": "BNBBTC",          // Symbol
        "i": "1m",              // Interval
        "f": 100,               // First trade ID
        "L": 200,               // Last trade ID
        "o": "0.0010",          // Open price
        "c": "0.0020",          // Close price
        "h": "0.0025",          // High price
        "l": "0.0015",          // Low price
        "v": "1000",            // Base asset volume
        "n": 100,               // Number of trades
        "x": false,             // Is this kline closed?
        "q": "1.0000",          // Quote asset volume
        "V": "500",             // Taker buy base asset volume
        "Q": "0.500",           // Taker buy quote asset volume
        "B": "123456"           // Ignore
    }
}

Individual Symbol Mini Ticker Stream
24hr rolling window mini-ticker statistics. These are NOT the statistics of the UTC day, but a 24hr rolling window for the previous 24hrs.

Stream Name: <symbol>@miniTicker

Update Speed: 1000ms

Payload:

{
    "e": "24hrMiniTicker",     // Event type
    "E": 1672515782136,        // Event time
    "s": "BNBBTC",             // Symbol
    "c": "0.0025",             // Close price
    "o": "0.0010",             // Open price
    "h": "0.0025",             // High price
    "l": "0.0010",             // Low price
    "v": "10000",              // Total traded base asset volume
    "q": "18"                  // Total traded quote asset volume
}

All Market Mini Tickers Stream
24hr rolling window mini-ticker statistics for all symbols that changed in an array. These are NOT the statistics of the UTC day, but a 24hr rolling window for the previous 24hrs. Note that only tickers that have changed will be present in the array.

Stream Name: !miniTicker@arr

Update Speed: 1000ms

Payload:

[
    {
        // Same as <symbol>@miniTicker payload
    }
]

Individual Symbol Ticker Streams
24hr rolling window ticker statistics for a single symbol. These are NOT the statistics of the UTC day, but a 24hr rolling window for the previous 24hrs.

Stream Name: <symbol>@ticker

Update Speed: 1000ms

Payload:

{
    "e": "24hrTicker",      // Event type
    "E": 1672515782136,     // Event time
    "s": "BNBBTC",          // Symbol
    "p": "0.0015",          // Price change
    "P": "250.00",          // Price change percent
    "w": "0.0018",          // Weighted average price
    "x": "0.0009",          // First trade(F)-1 price (first trade before the 24hr rolling window)
    "c": "0.0025",          // Last price
    "Q": "10",              // Last quantity
    "b": "0.0024",          // Best bid price
    "B": "10",              // Best bid quantity
    "a": "0.0026",          // Best ask price
    "A": "100",             // Best ask quantity
    "o": "0.0010",          // Open price
    "h": "0.0025",          // High price
    "l": "0.0010",          // Low price
    "v": "10000",           // Total traded base asset volume
    "q": "18",              // Total traded quote asset volume
    "O": 0,                 // Statistics open time
    "C": 86400000,          // Statistics close time
    "F": 0,                 // First trade ID
    "L": 18150,             // Last trade Id
    "n": 18151              // Total number of trades
}

Individual Symbol Rolling Window Statistics Streams
Rolling window ticker statistics for a single symbol, computed over multiple windows.

Stream Name: <symbol>@ticker_<window_size>

Window Sizes: 1h,4h,1d

Update Speed: 1000ms

Note: This stream is different from the <symbol>@ticker stream. The open time "O" always starts on a minute, while the closing time "C" is the current time of the update. As such, the effective window might be up to 59999ms wider than <window_size>.

Payload:

{
    "e": "1hTicker",        // Event type
    "E": 1672515782136,     // Event time
    "s": "BNBBTC",          // Symbol
    "p": "0.0015",          // Price change
    "P": "250.00",          // Price change percent
    "o": "0.0010",          // Open price
    "h": "0.0025",          // High price
    "l": "0.0010",          // Low price
    "c": "0.0025",          // Last price
    "w": "0.0018",          // Weighted average price
    "v": "10000",           // Total traded base asset volume
    "q": "18",              // Total traded quote asset volume
    "O": 0,                 // Statistics open time
    "C": 1675216573749,     // Statistics close time
    "F": 0,                 // First trade ID
    "L": 18150,             // Last trade Id
    "n": 18151              // Total number of trades
}

All Market Rolling Window Statistics Streams
Rolling window ticker statistics for all market symbols, computed over multiple windows. Note that only tickers that have changed will be present in the array.

Stream Name: !ticker_<window-size>@arr

Window Size: 1h,4h,1d

Update Speed: 1000ms

Payload:

[
    {
        // Same as <symbol>@ticker_<window_size> payload,
        // one for each symbol updated within the interval.
    }
]

Individual Symbol Book Ticker Streams
Pushes any update to the best bid or ask's price or quantity in real-time for a specified symbol. Multiple <symbol>@bookTicker streams can be subscribed to over one connection.

Stream Name: <symbol>@bookTicker

Update Speed: Real-time

Payload:

{
    "u": 400900217,         // order book updateId
    "s": "BNBUSDT",         // symbol
    "b": "25.35190000",     // best bid price
    "B": "31.21000000",     // best bid qty
    "a": "25.36520000",     // best ask price
    "A": "40.66000000"      // best ask qty
}

Average Price
Average price streams push changes in the average price over a fixed time interval.

Stream Name: <symbol>@avgPrice

Update Speed: 1000ms

Payload:

{
    "e": "avgPrice",           // Event type
    "E": 1693907033000,        // Event time
    "s": "BTCUSDT",            // Symbol
    "i": "5m",                 // Average price interval
    "w": "25776.86000000",     // Average price
    "T": 1693907032213         // Last trade time
}

Partial Book Depth Streams
Top <levels> bids and asks, pushed every second. Valid <levels> are 5, 10, or 20.

Stream Names: <symbol>@depth<levels> OR <symbol>@depth<levels>@100ms

Update Speed: 1000ms or 100ms

Payload:

{
    "lastUpdateId": 160,     // Last update ID
    "bids": [                // Bids to be updated
        [
            "0.0024",        // Price level to be updated
            "10"             // Quantity
        ]
    ],
    "asks": [                // Asks to be updated
        [
            "0.0026",        // Price level to be updated
            "100"            // Quantity
        ]
    ]
}

Diff. Depth Stream
Order book price and quantity depth updates used to locally manage an order book.

Stream Name: <symbol>@depth OR <symbol>@depth@100ms

Update Speed: 1000ms or 100ms

Payload:

{
    "e": "depthUpdate",     // Event type
    "E": 1672515782136,     // Event time
    "s": "BNBBTC",          // Symbol
    "U": 157,               // First update ID in event
    "u": 160,               // Final update ID in event
    "b": [                  // Bids to be updated
        [
            "0.0024",       // Price level to be updated
            "10"            // Quantity
        ]
    ],
    "a": [                  // Asks to be updated
        [
            "0.0026",       // Price level to be updated
            "100"           // Quantity
        ]
    ]
}

How to manage a local order book correctly
Open a WebSocket connection to wss://stream.binance.com:9443/ws/bnbbtc@depth.
Buffer the events received from the stream. Note the U of the first event you received.
Get a depth snapshot from https://api.binance.com/api/v3/depth?symbol=BNBBTC&limit=5000.
If the lastUpdateId from the snapshot is strictly less than the U from step 2, go back to step 3.
In the buffered events, discard any event where u is <= lastUpdateId of the snapshot. The first buffered event should now have lastUpdateId within its [U;u] range.
Set your local order book to the snapshot. Its update ID is lastUpdateId.
Apply the update procedure below to all buffered events, and then to all subsequent events received.
To apply an event to your local order book, follow this update procedure:

Decide whether the update event can be applied:
If the event last update ID (u) is less than the update ID of your local order book, ignore the event.
If the event first update ID (U) is greater than the update ID of your local order book + 1, you have missed some events.
Discard your local order book and restart the process from the beginning.
Normally, U of the next event is equal to u + 1 of the previous event.
For each price level in bids (b) and asks (a), set the new quantity in the order book:
If the price level does not exist in the order book, insert it with new quantity.
If the quantity is zero, remove the price level from the order book.
Set the order book update ID to the last update ID (u) in the processed event.
[!NOTE] Since depth snapshots retrieved from the API have a limit on the number of price levels (5000 on each side maximum), you won't learn the quantities for the levels outside of the initial snapshot unless they change.
So be careful when using the information for those levels, since they might not reflect the full view of the order book.
However, for most use cases, seeing 5000 levels on each side is enough to understand the market and trade effectively.


General API Information
The base endpoint is: wss://ws-api.binance.com:443/ws-api/v3.
If you experience issues with the standard 443 port, alternative port 9443 is also available.
The base endpoint for testnet is: wss://ws-api.testnet.binance.vision/ws-api/v3
A single connection to the API is only valid for 24 hours; expect to be disconnected after the 24-hour mark.
Before a disconnection either due to maintenance or after 24 hours, a serverShutdown event will be sent. Please reconnect as soon as possible to prevent stream interruption.
We support HMAC, RSA, and Ed25519 keys. For more information, please see API Key types.
Responses are in JSON by default. To receive responses in SBE, refer to the SBE FAQ page.
If your request contains a symbol name containing non-ASCII characters, then the response may contain non-ASCII characters encoded in UTF-8.
Some methods may return asset and/or symbol names containing non-ASCII characters encoded in UTF-8 even if the request did not contain non-ASCII characters.
The WebSocket server will send a ping frame every 20 seconds.
If the WebSocket server does not receive a pong frame back from the connection within a minute the connection will be disconnected.
When you receive a ping, you must send a pong with a copy of ping's payload as soon as possible.
Unsolicited pong frames are allowed, but will not prevent disconnection. It is recommended that the payload for these pong frames are empty.
Data is returned in chronological order, unless noted otherwise.
Without startTime or endTime, returns the most recent items up to the limit.
With startTime, returns oldest items from startTime up to the limit.
With endTime, returns most recent items up to endTime and the limit.
With both, behaves like startTime but does not exceed endTime.
All timestamps in the JSON responses are in milliseconds in UTC by default. To receive the information in microseconds, please add the parameter timeUnit=MICROSECOND or timeUnit=microsecond in the URL.
Timestamp parameters (e.g. startTime, endTime, timestamp) can be passed in milliseconds or microseconds.
All field names and values are case-sensitive, unless noted otherwise.
If there are enums or terms you want clarification on, please see SPOT Glossary for more information.
APIs have a timeout of 10 seconds when processing a request. If a response from the Matching Engine takes longer than this, the API responds with "Timeout waiting for response from backend server. Send status unknown; execution status unknown." (-1007 TIMEOUT)
This does not always mean that the request failed in the Matching Engine.
If the status of the request has not appeared in User Data Stream, please perform an API query for its status.
Please avoid SQL keywords in requests as they may trigger a security block by a WAF (Web Application Firewall) rule. See https://www.binance.com/en/support/faq/detail/360004492232 for more details.



Request format
Requests must be sent as JSON in text frames, one request per frame.

Example of request:

{
    "id": "e2a85d9f-07a5-4f94-8d5f-789dc3deb097",
    "method": "order.place",
    "params": {
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "LIMIT",
        "price": "0.1",
        "quantity": "10",
        "timeInForce": "GTC",
        "timestamp": 1655716096498,
        "apiKey": "T59MTDLWlpRW16JVeZ2Nju5A5C98WkMm8CSzWC4oqynUlTm1zXOxyauT8LmwXEv9",
        "signature": "5942ad337e6779f2f4c62cd1c26dba71c91514400a24990a3e7f5edec9323f90"
    }
}

Request fields:

Name	Type	Mandatory	Description
id	INT / STRING / null	YES	Arbitrary ID used to match responses to requests
method	STRING	YES	Request method name
params	OBJECT	NO	Request parameters. May be omitted if there are no parameters
Request id is truly arbitrary. You can use UUIDs, sequential IDs, current timestamp, etc. The server does not interpret id in any way, simply echoing it back in the response.

You can freely reuse IDs within a session. However, be careful to not send more than one request at a time with the same ID, since otherwise it might be impossible to tell the responses apart.

Request method names may be prefixed with explicit version: e.g., "v3/order.place".

The order of params is not significant.




Response format
Responses are returned as JSON in text frames, one response per frame.

Example of successful response:

{
    "id": "e2a85d9f-07a5-4f94-8d5f-789dc3deb097",
    "status": 200,
    "result": {
        "symbol": "BTCUSDT",
        "orderId": 12510053279,
        "orderListId": -1,
        "clientOrderId": "a097fe6304b20a7e4fc436",
        "transactTime": 1655716096505,
        "price": "0.10000000",
        "origQty": "10.00000000",
        "executedQty": "0.00000000",
        "origQuoteOrderQty": "0.000000",
        "cummulativeQuoteQty": "0.00000000",
        "status": "NEW",
        "timeInForce": "GTC",
        "type": "LIMIT",
        "side": "BUY",
        "workingTime": 1655716096505,
        "selfTradePreventionMode": "NONE"
    },
    "rateLimits": [
        {
            "rateLimitType": "ORDERS",
            "interval": "SECOND",
            "intervalNum": 10,
            "limit": 50,
            "count": 12
        },
        {
            "rateLimitType": "ORDERS",
            "interval": "DAY",
            "intervalNum": 1,
            "limit": 160000,
            "count": 4043
        },
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 321
        }
    ]
}

Example of failed response:

{
    "id": "e2a85d9f-07a5-4f94-8d5f-789dc3deb097",
    "status": 400,
    "error": {
        "code": -2010,
        "msg": "Account has insufficient balance for requested action."
    },
    "rateLimits": [
        {
            "rateLimitType": "ORDERS",
            "interval": "SECOND",
            "intervalNum": 10,
            "limit": 50,
            "count": 13
        },
        {
            "rateLimitType": "ORDERS",
            "interval": "DAY",
            "intervalNum": 1,
            "limit": 160000,
            "count": 4044
        },
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 322
        }
    ]
}

Response fields:

Name	Type	Mandatory	Description
id	INT / STRING / null	YES	Same as in the original request
status	INT	YES	Response status. See Status codes
result	OBJECT / ARRAY	YES	Response content. Present if request succeeded
error	OBJECT	Error description. Present if request failed
rateLimits	ARRAY	NO	Rate limiting status. See Rate limits
Status codes
Status codes in the status field are the same as in HTTP.

Here are some common status codes that you might encounter:

200 indicates a successful response.
4XX status codes indicate invalid requests; the issue is on your side.
400 – your request failed, see error for the reason.
403 – you have been blocked by the Web Application Firewall. This can indicate a rate limit violation or a security block. See https://www.binance.com/en/support/faq/detail/360004492232 for more details.
409 – your request partially failed but also partially succeeded, see error for details.
418 – you have been auto-banned for repeated violation of rate limits.
429 – you have exceeded API request rate limit, please slow down.
5XX status codes indicate internal errors; the issue is on Binance's side.
Important: If a response contains 5xx status code, it does not necessarily mean that your request has failed. Execution status is unknown and the request might have actually succeeded. Please use query methods to confirm the status. You might also want to establish a new WebSocket connection for that.
See Error codes for Binance for a list of error codes and messages.





Event format
User Data Stream events for non-SBE sessions are sent as JSON in text frames, one event per frame.

Events in SBE sessions will be sent as binary frames.

Please refer to userDataStream.subscribe for details on how to subscribe to User Data Stream in WebSocket API.

Example of an event:

{
    "subscriptionId": 0,
    "event": {
        "e": "outboundAccountPosition",
        "E": 1728972148778,
        "u": 1728972148778,
        "B": [
            {
                "a": "BTC",
                "f": "11818.00000000",
                "l": "182.00000000"
            },
            {
                "a": "USDT",
                "f": "10580.00000000",
                "l": "70.00000000"
            }
        ]
    }
}

Event fields:

Name	Type	Mandatory	Description
event	OBJECT	YES	Event payload. See User Data Streams
subscriptionId	INT	NO	Identifies which subscription the event is coming from. See User Data Stream subscriptions




Rate limits
Connection limits
There is a limit of 300 connections per attempt every 5 minutes.

The connection is per IP address.

General information on rate limits
Current API rate limits can be queried using the exchangeInfo request.
There are multiple rate limit types across multiple intervals.
Responses can indicate current rate limit status in the optional rateLimits field.
Requests fail with status 429 when unfilled order count or request rate limits are violated.
How to interpret rate limits
A response with rate limit status may look like this:

{
    "id": "7069b743-f477-4ae3-81db-db9b8df085d2",
    "status": 200,
    "result": {
        "serverTime": 1656400526260
    },
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 70
        }
    ]
}

The rateLimits array describes all currently active rate limits affected by the request.

Name	Type	Mandatory	Description
rateLimitType	ENUM	YES	Rate limit type: REQUEST_WEIGHT, ORDERS
interval	ENUM	YES	Rate limit interval: SECOND, MINUTE, HOUR, DAY
intervalNum	INT	YES	Rate limit interval multiplier
limit	INT	YES	Request limit per interval
count	INT	YES	Current usage per interval
Rate limits are accounted by intervals.

For example, a 1 MINUTE interval starts every minute. Request submitted at 00:01:23.456 counts towards the 00:01:00 minute's limit. Once the 00:02:00 minute starts, the count will reset to zero again.

Other intervals behave in a similar manner. For example, 1 DAY rate limit resets at 00:00 UTC every day, and 10 SECOND interval resets at 00, 10, 20... seconds of each minute.

APIs have multiple rate-limiting intervals. If you exhaust a shorter interval but the longer interval still allows requests, you will have to wait for the shorter interval to expire and reset. If you exhaust a longer interval, you will have to wait for that interval to reset, even if shorter rate limit count is zero.

How to show/hide rate limit information
rateLimits field is included with every response by default.

However, rate limit information can be quite bulky. If you are not interested in detailed rate limit status of every request, the rateLimits field can be omitted from responses to reduce their size.

Optional returnRateLimits boolean parameter in request.

Use returnRateLimits parameter to control whether to include rateLimits fields in response to individual requests.

Default request and response:

{ "id": 1, "method": "time" }

{
    "id": 1,
    "status": 200,
    "result": { "serverTime": 1656400526260 },
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 70
        }
    ]
}

Request and response without rate limit status:

{ "id": 2, "method": "time", "params": { "returnRateLimits": false } }

{ "id": 2, "status": 200, "result": { "serverTime": 1656400527891 } }

Optional returnRateLimits boolean parameter in connection URL.

If you wish to omit rateLimits from all responses by default, use returnRateLimits parameter in the query string instead:

wss://ws-api.binance.com:443/ws-api/v3?returnRateLimits=false

This will make all requests made through this connection behave as if you have passed "returnRateLimits": false.

If you want to see rate limits for a particular request, you need to explicitly pass the "returnRateLimits": true parameter.

Note: Your requests are still rate limited if you hide the rateLimits field in responses.

IP limits
Every request has a certain weight, added to your limit as you perform requests.
The heavier the request (e.g. querying data from multiple symbols), the more weight the request will cost.
Connecting to WebSocket API costs 2 weight.
Current weight usage is indicated by the REQUEST_WEIGHT rate limit type.
Use the exchangeInfo request to keep track of the current weight limits.
Weight is accumulated per IP address and is shared by all connections from that address.
If you go over the weight limit, requests fail with status 429.
This status code indicates you should back off and stop spamming the API.
Rate-limited responses include a retryAfter field, indicating when you can retry the request.
Repeatedly violating rate limits and/or failing to back off after receiving 429s will result in an automated IP ban and you will be disconnected.
Requests from a banned IP address fail with status 418.
retryAfter field indicates the timestamp when the ban will be lifted.
IP bans are tracked and scale in duration for repeat offenders, from 2 minutes to 3 days.
Successful response indicating that in 1 minute you have used 70 weight out of your 6000 limit:

{
    "id": "7069b743-f477-4ae3-81db-db9b8df085d2",
    "status": 200,
    "result": [],
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 70
        }
    ]
}

Failed response indicating that you are banned and the ban will last until epoch 1659146400000:

{
    "id": "fc93a61a-a192-4cf4-bb2a-a8f0f0c51e06",
    "status": 418,
    "error": {
        "code": -1003,
        "msg": "Way too much request weight used; IP banned until 1659146400000. Please use WebSocket Streams for live updates to avoid bans.",
        "data": {
            "serverTime": 1659142907531,
            "retryAfter": 1659146400000
        }
    },
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 2411
        }
    ]
}


Unfilled Order Count
Successfully placed orders update the ORDERS rate limit type.
Rejected or unsuccessful orders might or might not update the ORDERS rate limit type.
Please note that if your orders are consistently filled by trades, you can continuously place orders on the API. For more information, please see Spot Unfilled Order Count Rules.
Use the account.rateLimits.orders request to keep track of how many orders you have placed within this interval.
If you exceed this, requests fail with status 429.
This status code indicates you should back off and stop spamming the API.
Responses that have a status 429 include a retryAfter field, indicating when you can retry the request.
This is maintained per account and is shared by all API keys of the account.
Successful response indicating that you have placed 12 orders in 10 seconds, and 4043 orders in the past 24 hours:

{
    "id": "e2a85d9f-07a5-4f94-8d5f-789dc3deb097",
    "status": 200,
    "result": {
        "symbol": "BTCUSDT",
        "orderId": 12510053279,
        "orderListId": -1,
        "clientOrderId": "a097fe6304b20a7e4fc436",
        "transactTime": 1655716096505,
        "price": "0.10000000",
        "origQty": "10.00000000",
        "executedQty": "0.00000000",
        "origQuoteOrderQty": "0.000000",
        "cummulativeQuoteQty": "0.00000000",
        "status": "NEW",
        "timeInForce": "GTC",
        "type": "LIMIT",
        "side": "BUY",
        "workingTime": 1655716096505,
        "selfTradePreventionMode": "NONE"
    },
    "rateLimits": [
        {
            "rateLimitType": "ORDERS",
            "interval": "SECOND",
            "intervalNum": 10,
            "limit": 50,
            "count": 12
        },
        {
            "rateLimitType": "ORDERS",
            "interval": "DAY",
            "intervalNum": 1,
            "limit": 160000,
            "count": 4043
        },
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 321
        }
    ]
}




Request security
Each method has a security type indicating required API key permissions, shown next to the method name (e.g., Place new order (TRADE)).
If unspecified, the security type is NONE.
Except for NONE, all methods with a security type are considered SIGNED requests (i.e. including a signature), except for listenKey management.
Secure methods require a valid API key to be specified and authenticated.
API keys can be created on the API Management page of your Binance account.
Both API key and secret key are sensitive. Never share them with anyone. If you notice unusual activity in your account, immediately revoke all the keys and contact Binance support.
API keys can be configured to allow access only to certain types of secure methods.
For example, you can have an API key with TRADE permission for trading, while using a separate API key with USER_DATA permission to monitor your order status.
By default, an API key cannot TRADE. You need to enable trading in API Management first.
Security type	Description
NONE	Public market data
TRADE	Trading on the exchange, placing and canceling orders
USER_DATA	Private account information, such as order status and your trading history
USER_STREAM	Managing User Data Stream subscriptions
SIGNED request security
SIGNED requests require an additional parameter: signature, authorizing the request.
Signature Case Sensitivity
HMAC: Signatures generated using HMAC are not case-sensitive. This means the signature string can be verified regardless of letter casing.
RSA: Signatures generated using RSA are case-sensitive.
Ed25519: Signatures generated using ED25519 are also case-sensitive
Please consult SIGNED request example (HMAC), SIGNED request example (RSA), and SIGNED request example (Ed25519) on how to compute signature, depending on which API key type you are using.


Timing security
SIGNED requests also require a timestamp parameter which should be the current timestamp either in milliseconds or microseconds. (See General API Information)
An additional optional parameter, recvWindow, specifies for how long the request stays valid and may only be specified in milliseconds.
recvWindow supports up to three decimal places of precision (e.g., 6000.346) so that microseconds may be specified.
If recvWindow is not sent, it defaults to 5000 milliseconds.
Maximum recvWindow is 60000 milliseconds.
Request processing logic is as follows:
serverTime = getCurrentTime()
if (timestamp < (serverTime + 1 second) && (serverTime - timestamp) <= recvWindow) {
  // begin processing request
  serverTime = getCurrentTime()
  if (serverTime - timestamp) <= recvWindow {
    // forward request to Matching Engine
  } else {
    // reject request
  }
  // finish processing request
} else {
  // reject request
}

Serious trading is about timing. Networks can be unstable and unreliable, which can lead to requests taking varying amounts of time to reach the servers. With recvWindow, you can specify that the request must be processed within a certain number of milliseconds or be rejected by the server.

It is recommended to use a small recvWindow of 5000 or less!

SIGNED request example (HMAC)
Here is a step-by-step guide on how to sign requests using an HMAC secret key.

Example API key and secret key:

Key	Value
apiKey	vmPUZE6mv9SD5VNHk4HlWFsOr6aKE2zvsw0MuIgwCIPy6utIco14y7Ju91duEh8A
secretKey	NhqPtmdSJYdKjVHjA7PZj4Mge3R5YNiP1e3UZjInClVN65XAbvqqM6A7H5fATj0j
WARNING: DO NOT SHARE YOUR API KEY AND SECRET KEY WITH ANYONE.

The example keys are provided here only for illustrative purposes.

Example of request with a symbol name comprised entirely of ASCII characters:

{
    "id": "4885f793-e5ad-4c3b-8f6c-55d891472b71",
    "method": "order.place",
    "params": {
        "symbol": "BTCUSDT",
        "side": "SELL",
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": "0.01000000",
        "price": "52000.00",
        "recvWindow": 100,
        "timestamp": 1645423376532,
        "apiKey": "vmPUZE6mv9SD5VNHk4HlWFsOr6aKE2zvsw0MuIgwCIPy6utIco14y7Ju91duEh8A",
        "signature": "------ FILL ME ------"
    }
}

Example of a request with a symbol name containing non-ASCII characters:

{
    "id": "4885f793-e5ad-4c3b-8f6c-55d891472b71",
    "method": "order.place",
    "params": {
        "symbol": "１２３４５６",
        "side": "BUY",
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": "0.01000000",
        "price": "0.10000000",
        "recvWindow": 5000,
        "timestamp": 1645423376532,
        "apiKey": "vmPUZE6mv9SD5VNHk4HlWFsOr6aKE2zvsw0MuIgwCIPy6utIco14y7Ju91duEh8A",
        "signature": "------ FILL ME ------"
    }
}

As you can see, the signature parameter is currently missing.

Step 1: Construct the signature payload

Take all request params except signature and sort them in alphabetical order by parameter name:

For the first set of example parameters (ASCII only):

Parameter	Value
apiKey	vmPUZE6mv9SD5VNHk4HlWFsOr6aKE2zvsw0MuIgwCIPy6utIco14y7Ju91duEh8A
price	52000.00
quantity	0.01000000
recvWindow	100
side	SELL
symbol	BTCUSDT
timeInForce	GTC
timestamp	1645423376532
type	LIMIT
For the second set of example parameters (some non-ASCII characters):

Parameter	Value
apiKey	vmPUZE6mv9SD5VNHk4HlWFsOr6aKE2zvsw0MuIgwCIPy6utIco14y7Ju91duEh8A
price	0.10000000
quantity	1.00000000
recvWindow	5000
side	BUY
symbol	１２３４５６
timeInForce	GTC
timestamp	1645423376532
type	LIMIT
Format parameters as parameter=value pairs separated by &. Values need to be encoded in UTF-8.

For the first set of example parameters (ASCII only), the signature payload should look like this:

apiKey=vmPUZE6mv9SD5VNHk4HlWFsOr6aKE2zvsw0MuIgwCIPy6utIco14y7Ju91duEh8A&price=52000.00&quantity=0.01000000&recvWindow=100&side=SELL&symbol=BTCUSDT&timeInForce=GTC&timestamp=1645423376532&type=LIMIT


For the second set of example parameters (some non-ASCII characters), the signature payload should look like this:

apiKey=vmPUZE6mv9SD5VNHk4HlWFsOr6aKE2zvsw0MuIgwCIPy6utIco14y7Ju91duEh8A&price=0.10000000&quantity=1.00000000&recvWindow=5000&side=BUY&symbol=１２３４５６&timeInForce=GTC&timestamp=1645423376532&type=LIMIT


Step 2: Compute the signature

Use the secretKey of your API key as the signing key for the HMAC-SHA-256 algorithm.
Sign the UTF-8 bytes of the signature payload constructed in Step 1.
Encode the HMAC-SHA-256 output as a hex string.
Note that apiKey, secretKey, and the payload are case-sensitive, while the resulting signature value is case-insensitive.

You can cross-check your signature algorithm implementation with OpenSSL:

For the first set of example parameters (ASCII only):

$ echo -n 'apiKey=vmPUZE6mv9SD5VNHk4HlWFsOr6aKE2zvsw0MuIgwCIPy6utIco14y7Ju91duEh8A&price=52000.00&quantity=0.01000000&recvWindow=100&side=SELL&symbol=BTCUSDT&timeInForce=GTC&timestamp=1645423376532&type=LIMIT' \
  | openssl dgst -hex -sha256 -hmac 'NhqPtmdSJYdKjVHjA7PZj4Mge3R5YNiP1e3UZjInClVN65XAbvqqM6A7H5fATj0j'

aa1b5712c094bc4e57c05a1a5c1fd8d88dcd628338ea863fec7b88e59fe2db24


For the second set of example parameters (some non-ASCII characters):

$ echo -n 'apiKey=vmPUZE6mv9SD5VNHk4HlWFsOr6aKE2zvsw0MuIgwCIPy6utIco14y7Ju91duEh8A&price=0.10000000&quantity=1.00000000&recvWindow=5000&side=BUY&symbol=１２３４５６&timeInForce=GTC&timestamp=1645423376532&type=LIMIT' \
  | openssl dgst -hex -sha256 -hmac 'NhqPtmdSJYdKjVHjA7PZj4Mge3R5YNiP1e3UZjInClVN65XAbvqqM6A7H5fATj0j'

b33892ae8e687c939f4468c6268ddd4c40ac1af18ad19a064864c47bae0752cd


Step 3: Add signature to request params

Complete the request by adding the signature parameter with the signature string.

For the first set of example parameters (ASCII only):

{
    "id": "4885f793-e5ad-4c3b-8f6c-55d891472b71",
    "method": "order.place",
    "params": {
        "symbol": "BTCUSDT",
        "side": "SELL",
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": "0.01000000",
        "price": "52000.00",
        "recvWindow": 100,
        "timestamp": 1645423376532,
        "apiKey": "vmPUZE6mv9SD5VNHk4HlWFsOr6aKE2zvsw0MuIgwCIPy6utIco14y7Ju91duEh8A",
        "signature": "aa1b5712c094bc4e57c05a1a5c1fd8d88dcd628338ea863fec7b88e59fe2db24"
    }
}

For the second set of example parameters (some non-ASCII characters):

{
    "id": "4885f793-e5ad-4c3b-8f6c-55d891472b71",
    "method": "order.place",
    "params": {
        "symbol": "１２３４５６",
        "side": "BUY",
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": "1.00000000",
        "price": "0.10000000",
        "recvWindow": 5000,
        "timestamp": 1645423376532,
        "apiKey": "vmPUZE6mv9SD5VNHk4HlWFsOr6aKE2zvsw0MuIgwCIPy6utIco14y7Ju91duEh8A",
        "signature": "b33892ae8e687c939f4468c6268ddd4c40ac1af18ad19a064864c47bae0752cd"
    }
}

SIGNED request example (RSA)
Here is a step-by-step guide on how to sign requests using an RSA private key.

Key	Value
apiKey	CAvIjXy3F44yW6Pou5k8Dy1swsYDWJZLeoK2r8G4cFDnE9nosRppc2eKc1T8TRTQ
These examples assume the private key is stored in the file test-rsa-prv.pem.

WARNING: DO NOT SHARE YOUR API KEY AND PRIVATE KEY WITH ANYONE.

The example keys are provided here only for illustrative purposes.

Example of request with a symbol name comprised entirely of ASCII characters:

{
    "id": "4885f793-e5ad-4c3b-8f6c-55d891472b71",
    "method": "order.place",
    "params": {
        "symbol": "BTCUSDT",
        "side": "SELL",
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": "0.01000000",
        "price": "52000.00",
        "recvWindow": 100,
        "timestamp": 1645423376532,
        "apiKey": "CAvIjXy3F44yW6Pou5k8Dy1swsYDWJZLeoK2r8G4cFDnE9nosRppc2eKc1T8TRTQ",
        "signature": "------ FILL ME ------"
    }
}

Example of a request with a symbol name containing non-ASCII characters:

{
    "id": "4885f793-e5ad-4c3b-8f6c-55d891472b71",
    "method": "order.place",
    "params": {
        "symbol": "１２３４５６",
        "side": "BUY",
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": "0.01000000",
        "price": "0.10000000",
        "recvWindow": 5000,
        "timestamp": 1645423376532,
        "apiKey": "CAvIjXy3F44yW6Pou5k8Dy1swsYDWJZLeoK2r8G4cFDnE9nosRppc2eKc1T8TRTQ",
        "signature": "------ FILL ME ------"
    }
}

Step 1: Construct the signature payload

Take all request params except signature and sort them in alphabetical order by parameter name:

For the first set of example parameters (ASCII only):

Parameter	Value
apiKey	CAvIjXy3F44yW6Pou5k8Dy1swsYDWJZLeoK2r8G4cFDnE9nosRppc2eKc1T8TRTQ
price	52000.00
quantity	0.01000000
recvWindow	100
side	SELL
symbol	BTCUSDT
timeInForce	GTC
timestamp	1645423376532
type	LIMIT
For the second set of example parameters (some non-ASCII characters):

Parameter	Value
apiKey	CAvIjXy3F44yW6Pou5k8Dy1swsYDWJZLeoK2r8G4cFDnE9nosRppc2eKc1T8TRTQ
price	0.10000000
quantity	1.00000000
recvWindow	5000
side	BUY
symbol	１２３４５６
timeInForce	GTC
timestamp	1645423376532
type	LIMIT
Format parameters as parameter=value pairs separated by &. Values need to be encoded in UTF-8.

For the first set of example parameters (ASCII only), the signature payload should look like this:

apiKey=CAvIjXy3F44yW6Pou5k8Dy1swsYDWJZLeoK2r8G4cFDnE9nosRppc2eKc1T8TRTQ&price=52000.00&quantity=0.01000000&recvWindow=100&side=SELL&symbol=BTCUSDT&timeInForce=GTC&timestamp=1645423376532&type=LIMIT


For the second set of example parameters (some non-ASCII characters), the signature payload should look like this:

apiKey=CAvIjXy3F44yW6Pou5k8Dy1swsYDWJZLeoK2r8G4cFDnE9nosRppc2eKc1T8TRTQ&price=0.10000000&quantity=1.00000000&recvWindow=5000&side=BUY&symbol=１２３４５６&timeInForce=GTC&timestamp=1645423376532&type=LIMIT


Step 2: Compute the signature

Sign the UTF-8 bytes of the signature payload constructed in Step 1 using the RSASSA-PKCS1-v1_5 algorithm with SHA-256 hash function.
Encode the output in base64.
Note that apiKey, the payload, and the resulting signature are case-sensitive.

You can cross-check your signature algorithm implementation with OpenSSL:

For the first set of example parameters (ASCII only):

$ echo -n 'apiKey=CAvIjXy3F44yW6Pou5k8Dy1swsYDWJZLeoK2r8G4cFDnE9nosRppc2eKc1T8TRTQ&price=52000.00&quantity=0.01000000&recvWindow=100&side=SELL&symbol=BTCUSDT&timeInForce=GTC&timestamp=1645423376532&type=LIMIT' \
  | openssl dgst -sha256 -sign test-rsa-prv.pem \
  | openssl enc -base64 -A

OJJaf8C/3VGrU4ATTR4GiUDqL2FboSE1Qw7UnnoYNfXTXHubIl1iaePGuGyfct4NPu5oVEZCH4Q6ZStfB1w4ssgu0uiB/Bg+fBrRFfVgVaLKBdYHMvT+ljUJzqVaeoThG9oXlduiw8PbS9U8DYAbDvWN3jqZLo4Z2YJbyovyDAvDTr/oC0+vssLqP7NmlNb3fF3Bj7StmOwJvQJTbRAtzxK5PP7OQe+0mbW+D7RqVkUiSswR8qJFWTeSe4nXXNIdZdueYhF/Xf25L+KitJS5IHdIHcKfEw3MQzHFb2ZsGWkjDQwxkwr7Noi0Zaa+gFtxCuatGFm9dFIyx217pmSHtA==


For the second set of example parameters (some non-ASCII characters):

$ echo -n 'apiKey=CAvIjXy3F44yW6Pou5k8Dy1swsYDWJZLeoK2r8G4cFDnE9nosRppc2eKc1T8TRTQ&price=0.10000000&quantity=1.00000000&recvWindow=5000&side=BUY&symbol=１２３４５６&timeInForce=GTC&timestamp=1645423376532&type=LIMIT' \
  | openssl dgst -sha256 -sign test-rsa-prv.pem \
  | openssl enc -base64 -A

F3o/79Ttvl2cVYGPfBOF3oEOcm5QcYmTYWpdVIrKve5u+8paMNDAdUE+teqMxFM9HcquetGcfuFpLYtsQames5bDx/tskGM76TWW8HaM+6tuSYBSFLrKqChfA9hQGLYGjAiflf1YBnDhY+7vNbJFusUborNOloOj+ufzP5q42PvI3H0uNy3W5V3pyfXpDGCBtfCYYr9NAqA4d+AQfyllL/zkO9h9JSdozN49t0/hWGoD2dWgSO0Je6MytKEvD4DQXGeqNlBTB6tUXcWnRW+FcaKZ4KYqnxCtb1u8rFXUYgFykr2CbcJLSmw6ydEJ3EZ/NaZopRr+cU0W2m0HZ3qucw==


Step 3: Add signature to request params

Complete the request by adding the signature parameter with the signature string.

For the first set of example parameters (ASCII only):

{
    "id": "4885f793-e5ad-4c3b-8f6c-55d891472b71",
    "method": "order.place",
    "params": {
        "symbol": "BTCUSDT",
        "side": "SELL",
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": "0.01000000",
        "price": "52000.00",
        "newOrderRespType": "ACK",
        "recvWindow": 100,
        "timestamp": 1645423376532,
        "apiKey": "CAvIjXy3F44yW6Pou5k8Dy1swsYDWJZLeoK2r8G4cFDnE9nosRppc2eKc1T8TRTQ",
        "signature": "OJJaf8C/3VGrU4ATTR4GiUDqL2FboSE1Qw7UnnoYNfXTXHubIl1iaePGuGyfct4NPu5oVEZCH4Q6ZStfB1w4ssgu0uiB/Bg+fBrRFfVgVaLKBdYHMvT+ljUJzqVaeoThG9oXlduiw8PbS9U8DYAbDvWN3jqZLo4Z2YJbyovyDAvDTr/oC0+vssLqP7NmlNb3fF3Bj7StmOwJvQJTbRAtzxK5PP7OQe+0mbW+D7RqVkUiSswR8qJFWTeSe4nXXNIdZdueYhF/Xf25L+KitJS5IHdIHcKfEw3MQzHFb2ZsGWkjDQwxkwr7Noi0Zaa+gFtxCuatGFm9dFIyx217pmSHtA=="
    }
}


For the second set of example parameters (some non-ASCII characters):

{
    "id": "4885f793-e5ad-4c3b-8f6c-55d891472b71",
    "method": "order.place",
    "params": {
        "symbol": "１２３４５６",
        "side": "SELL",
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": "1.00000000",
        "price": "0.10000000",
        "recvWindow": 5000,
        "timestamp": 1645423376532,
        "apiKey": "CAvIjXy3F44yW6Pou5k8Dy1swsYDWJZLeoK2r8G4cFDnE9nosRppc2eKc1T8TRTQ",
        "signature": "F3o/79Ttvl2cVYGPfBOF3oEOcm5QcYmTYWpdVIrKve5u+8paMNDAdUE+teqMxFM9HcquetGcfuFpLYtsQames5bDx/tskGM76TWW8HaM+6tuSYBSFLrKqChfA9hQGLYGjAiflf1YBnDhY+7vNbJFusUborNOloOj+ufzP5q42PvI3H0uNy3W5V3pyfXpDGCBtfCYYr9NAqA4d+AQfyllL/zkO9h9JSdozN49t0/hWGoD2dWgSO0Je6MytKEvD4DQXGeqNlBTB6tUXcWnRW+FcaKZ4KYqnxCtb1u8rFXUYgFykr2CbcJLSmw6ydEJ3EZ/NaZopRr+cU0W2m0HZ3qucw=="
    }
}


SIGNED Request Example (Ed25519)
Note: It is highly recommended to use Ed25519 API keys as they will provide the best performance and security out of all supported key types.

Here is a step-by-step guide on how to sign requests using an Ed25519 private key.

Key	Value
apiKey	4yNzx3yWC5bS6YTwEkSRaC0nRmSQIIStAUOh1b6kqaBrTLIhjCpI5lJH8q8R8WNO
These examples assume the private key is stored in the file test-ed25519-prv.pem.

WARNING: DO NOT SHARE YOUR API KEY AND PRIVATE KEY WITH ANYONE.

The example keys are provided here only for illustrative purposes.

Example of request with a symbol name comprised entirely of ASCII characters:

{
    "id": "4885f793-e5ad-4c3b-8f6c-55d891472b71",
    "method": "order.place",
    "params": {
        "symbol": "BTCUSDT",
        "side": "SELL",
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": "0.01000000",
        "price": "52000.00",
        "recvWindow": 100,
        "timestamp": 1645423376532,
        "apiKey": "4yNzx3yWC5bS6YTwEkSRaC0nRmSQIIStAUOh1b6kqaBrTLIhjCpI5lJH8q8R8WNO",
        "signature": "------ FILL ME ------"
    }
}

Example of a request with a symbol name containing non-ASCII characters:

{
    "id": "4885f793-e5ad-4c3b-8f6c-55d891472b71",
    "method": "order.place",
    "params": {
        "symbol": "１２３４５６",
        "side": "BUY",
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": "0.01000000",
        "price": "0.10000000",
        "recvWindow": 5000,
        "timestamp": 1645423376532,
        "apiKey": "4yNzx3yWC5bS6YTwEkSRaC0nRmSQIIStAUOh1b6kqaBrTLIhjCpI5lJH8q8R8WNO",
        "signature": "------ FILL ME ------"
    }
}

Step 1: Construct the signature payload

Take all request params except signature and sort them in alphabetical order by parameter name:

For the first set of example parameters (ASCII only):

Parameter	Value
apiKey	4yNzx3yWC5bS6YTwEkSRaC0nRmSQIIStAUOh1b6kqaBrTLIhjCpI5lJH8q8R8WNO
price	52000.00
quantity	0.01000000
recvWindow	100
side	SELL
symbol	BTCUSDT
timeInForce	GTC
timestamp	1645423376532
type	LIMIT
For the second set of example parameters (some non-ASCII characters):

Parameter	Value
apiKey	4yNzx3yWC5bS6YTwEkSRaC0nRmSQIIStAUOh1b6kqaBrTLIhjCpI5lJH8q8R8WNO
price	0.20000000
quantity	1.00000000
recvWindow	5000
side	SELL
symbol	１２３４５６
timeInForce	GTC
timestamp	1668481559918
type	LIMIT
Format parameters as parameter=value pairs separated by &. Values need to be encoded in UTF-8.

For the first set of example parameters (ASCII only), the signature payload should look like this:

apiKey=4yNzx3yWC5bS6YTwEkSRaC0nRmSQIIStAUOh1b6kqaBrTLIhjCpI5lJH8q8R8WNO&price=52000.00&quantity=0.01000000&recvWindow=100&side=SELL&symbol=BTCUSDT&timeInForce=GTC&timestamp=1645423376532&type=LIMIT


For the second set of example parameters (some non-ASCII characters), the signature payload should look like this:

apiKey=4yNzx3yWC5bS6YTwEkSRaC0nRmSQIIStAUOh1b6kqaBrTLIhjCpI5lJH8q8R8WNO&price=0.10000000&quantity=1.00000000&recvWindow=5000&side=BUY&symbol=１２３４５６&timeInForce=GTC&timestamp=1645423376532&type=LIMIT


Step 2: Compute the signature

Sign the UTF-8 bytes of your signature payload constructed in Step 1 using the Ed25519 private key.
Encode the output in base64.
Note that apiKey, the payload, and the resulting signature are case-sensitive.

You can cross-check your signature algorithm implementation with OpenSSL:

For the first set of example parameters (ASCII only):

echo -n "apiKey=4yNzx3yWC5bS6YTwEkSRaC0nRmSQIIStAUOh1b6kqaBrTLIhjCpI5lJH8q8R8WNO&price=52000.00&quantity=0.01000000&recvWindow=100&side=SELL&symbol=BTCUSDT&timeInForce=GTC&timestamp=1645423376532&type=LIMIT" \
  | openssl dgst -sign ./test-ed25519-prv.pem \
  | openssl enc -base64 -A

EocljwPl29jDxWYaaRaOo4pJ9wEblFbklJvPugNscLLuKd5vHM2grWjn1z+rY0aJ7r/44enxHL6mOAJuJ1kqCg==


For the second set of example parameters (some non-ASCII characters):

echo -n "apiKey=4yNzx3yWC5bS6YTwEkSRaC0nRmSQIIStAUOh1b6kqaBrTLIhjCpI5lJH8q8R8WNO&price=0.10000000&quantity=1.00000000&recvWindow=5000&side=BUY&symbol=１２３４５６&timeInForce=GTC&timestamp=1645423376532&type=LIMIT" \
  | openssl dgst -sign ./test-ed25519-prv.pem \
  | openssl enc -base64 -A

dtNHJeyKry+cNjiGv+sv5kynO9S40tf8k7D5CfAEQAp0s2scunZj+ovJdz2OgW8XhkB9G3/HmASkA9uY9eyFCA==


Step 3: Add the signature to request params

For the first set of example parameters (ASCII only):

{
    "id": "4885f793-e5ad-4c3b-8f6c-55d891472b71",
    "method": "order.place",
    "params": {
        "symbol": "BTCUSDT",
        "side": "SELL",
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": "0.01000000",
        "price": "52000.00",
        "newOrderRespType": "ACK",
        "recvWindow": 100,
        "timestamp": 1645423376532,
        "apiKey": "4yNzx3yWC5bS6YTwEkSRaC0nRmSQIIStAUOh1b6kqaBrTLIhjCpI5lJH8q8R8WNO",
        "signature": "EocljwPl29jDxWYaaRaOo4pJ9wEblFbklJvPugNscLLuKd5vHM2grWjn1z+rY0aJ7r/44enxHL6mOAJuJ1kqCg=="
    }
}

For the second set of example parameters (some non-ASCII characters):

{
    "id": "4885f793-e5ad-4c3b-8f6c-55d891472b71",
    "method": "order.place",
    "params": {
        "symbol": "１２３４５６",
        "side": "SELL",
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": "1.00000000",
        "price": "0.10000000",
        "recvWindow": 5000,
        "timestamp": 1645423376532,
        "apiKey": "4yNzx3yWC5bS6YTwEkSRaC0nRmSQIIStAUOh1b6kqaBrTLIhjCpI5lJH8q8R8WNO",
        "signature": "dtNHJeyKry+cNjiGv+sv5kynO9S40tf8k7D5CfAEQAp0s2scunZj+ovJdz2OgW8XhkB9G3/HmASkA9uY9eyFCA=="
    }
}

Here is a sample Python script performing all the steps above:

#!/usr/bin/env python3

import base64
import time
import json
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from websocket import create_connection

# Set up authentication
API_KEY='put your own API Key here'
PRIVATE_KEY_PATH='test-prv-key.pem'

# Load the private key.
# In this example the key is expected to be stored without encryption,
# but we recommend using a strong password for improved security.
with open(PRIVATE_KEY_PATH, 'rb') as f:
  private_key = load_pem_private_key(data=f.read(), password=None)

# Set up the request parameters
params = {
    'apiKey':       API_KEY,
    'symbol':       '１２３４５６',
    'side':         'SELL',
    'type':         'LIMIT',
    'timeInForce':  'GTC',
    'quantity':     '1.0000000',
    'price':        '0.10000000',
    'recvWindow':   5000
}

# Timestamp the request
timestamp = int(time.time() * 1000) # UNIX timestamp in milliseconds
params['timestamp'] = timestamp

# Sort parameters alphabetically by name
params = dict(sorted(params.items()))

# Compute the signature payload
payload = '&'.join([f"{k}={v}" for k,v in params.items()]) # no percent encoding here!

# Sign the request
signature = base64.b64encode(private_key.sign(payload.encode('UTF-8')))
params['signature'] = signature.decode('ASCII')

# Send the request
request = {
    'id': 'my_new_order',
    'method': 'order.place',
    'params': params
}

ws = create_connection("wss://ws-api.binance.com:443/ws-api/v3")
ws.send(json.dumps(request))
result =  ws.recv()
ws.close()

print(result)



General requests
Test connectivity
{
    "id": "922bcc6e-9de8-440d-9e84-7c80933a8d0d",
    "method": "ping"
}

Test connectivity to the WebSocket API.

Note: You can use regular WebSocket ping frames to test connectivity as well, WebSocket API will respond with pong frames as soon as possible. ping request along with time is a safe way to test request-response handling in your application.

Weight: 1

Parameters: NONE

Data Source: Memory

Response:

{
    "id": "922bcc6e-9de8-440d-9e84-7c80933a8d0d",
    "status": 200,
    "result": {},
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 1
        }
    ]
}

Check server time
{
    "id": "187d3cb2-942d-484c-8271-4e2141bbadb1",
    "method": "time"
}

Test connectivity to the WebSocket API and get the current server time.

Weight: 1

Parameters: NONE

Data Source: Memory

Response:

{
    "id": "187d3cb2-942d-484c-8271-4e2141bbadb1",
    "status": 200,
    "result": {
        "serverTime": 1656400526260
    },
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 1
        }
    ]
}


Exchange information
{
    "id": "5494febb-d167-46a2-996d-70533eb4d976",
    "method": "exchangeInfo",
    "params": {
        "symbols": ["BNBBTC"]
    }
}

Query current exchange trading rules, rate limits, and symbol information.

Weight: 20

Parameters:

Name	Type	Mandatory	Description
symbol	STRING	NO	Describe a single symbol
symbols	ARRAY of STRING	Describe multiple symbols
permissions	ARRAY of STRING	Filter symbols by permissions
showPermissionSets	BOOLEAN	Controls whether the content of the permissionSets field is populated or not. Defaults to true.
symbolStatus	ENUM	Filters for symbols that have this tradingStatus.

Valid values: TRADING, HALT, BREAK
Cannot be used in combination with symbol or symbols
Notes:

Only one of symbol, symbols, permissions parameters can be specified.

Without parameters, exchangeInfo displays all symbols with ["SPOT, "MARGIN", "LEVERAGED"] permissions.

In order to list all active symbols on the exchange, you need to explicitly request all permissions.
permissions accepts either a list of permissions, or a single permission name. E.g. "SPOT".

Available Permissions


Examples of Symbol Permissions Interpretation from the Response:

[["A","B"]] means you may place an order if your account has either permission "A" or permission "B".
[["A"],["B"]] means you can place an order if your account has permission "A" and permission "B".
[["A"],["B","C"]] means you can place an order if your account has permission "A" and permission "B" or permission "C". (Inclusive or is applied here, not exclusive or, so your account may have both permission "B" and permission "C".)
Data Source: Memory

Response:

{
    "id": "5494febb-d167-46a2-996d-70533eb4d976",
    "status": 200,
    "result": {
        "timezone": "UTC",
        "serverTime": 1655969291181,
        // Global rate limits. See "Rate limits" section.
        "rateLimits": [
            {
                "rateLimitType": "REQUEST_WEIGHT",     // Rate limit type: REQUEST_WEIGHT, ORDERS, CONNECTIONS
                "interval": "MINUTE",                  // Rate limit interval: SECOND, MINUTE, DAY
                "intervalNum": 1,                      // Rate limit interval multiplier (i.e., "1 minute")
                "limit": 6000                          // Rate limit per interval
            },
            {
                "rateLimitType": "ORDERS",
                "interval": "SECOND",
                "intervalNum": 10,
                "limit": 50
            },
            {
                "rateLimitType": "ORDERS",
                "interval": "DAY",
                "intervalNum": 1,
                "limit": 160000
            },
            {
                "rateLimitType": "CONNECTIONS",
                "interval": "MINUTE",
                "intervalNum": 5,
                "limit": 300
            }
        ],
        // Exchange filters are explained on the "Filters" page:
        // https://github.com/binance/binance-spot-api-docs/blob/master/filters.md
        // All exchange filters are optional.
        "exchangeFilters": [],
        "symbols": [
            {
                "symbol": "BNBBTC",
                "status": "TRADING",
                "baseAsset": "BNB",
                "baseAssetPrecision": 8,
                "quoteAsset": "BTC",
                "quotePrecision": 8,
                "quoteAssetPrecision": 8,
                "baseCommissionPrecision": 8,
                "quoteCommissionPrecision": 8,
                "orderTypes": [
                    "LIMIT",
                    "LIMIT_MAKER",
                    "MARKET",
                    "STOP_LOSS_LIMIT",
                    "TAKE_PROFIT_LIMIT"
                ],
                "icebergAllowed": true,
                "ocoAllowed": true,
                "otoAllowed": true,
                "opoAllowed": true,
                "quoteOrderQtyMarketAllowed": true,
                "allowTrailingStop": true,
                "cancelReplaceAllowed": true,
                "amendAllowed": false,
                "pegInstructionsAllowed": true,
                "isSpotTradingAllowed": true,
                "isMarginTradingAllowed": true,
                // Symbol filters are explained on the "Filters" page:
                // https://github.com/binance/binance-spot-api-docs/blob/master/filters.md
                // All symbol filters are optional.
                "filters": [
                    {
                        "filterType": "PRICE_FILTER",
                        "minPrice": "0.00000100",
                        "maxPrice": "100000.00000000",
                        "tickSize": "0.00000100"
                    },
                    {
                        "filterType": "LOT_SIZE",
                        "minQty": "0.00100000",
                        "maxQty": "100000.00000000",
                        "stepSize": "0.00100000"
                    }
                ],
                "permissions": [],
                "permissionSets": [["SPOT", "MARGIN", "TRD_GRP_004"]],
                "defaultSelfTradePreventionMode": "NONE",
                "allowedSelfTradePreventionModes": ["NONE"]
            }
        ],
        // Optional field. Present only when SOR is available.
        // https://github.com/binance/binance-spot-api-docs/blob/master/faqs/sor_faq.md
        "sors": [
            {
                "baseAsset": "BTC",
                "symbols": ["BTCUSDT", "BTCUSDC"]
            }
        ]
    },
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 20
        }
    ]
}

Query Execution Rules
{
    "id": "5162affb-0aba-4821-b475-f2625006eb43",
    "method": "executionRules",
    "params": {
        "symbol": "BAZUSD"
    }
}

Weight and Parameters:

Note: No combination of multiple parameters is allowed.

Parameter	Weight	Type	Mandatory	Description
symbol	2	STRING	No	Query for specified symbol
symbols	2 for each symbol, capped at a max of 40	Query for multiple symbols
No parameter	40	N/A	N/A	Query for all symbols
symbolStatus	40	ENUM	No	Query for all symbols with the specified status
Supported values: TRADING, HALT, BREAK
Data Source: Memory

Response:

{
  "id": "5162affb-0aba-4821-b475-f2625006eb43",
  "status": 200,
  "result": {
    "symbolRules": [
      {
        "symbol": "BAZUSD",
        "rules": [
          {
            "ruleType": "PRICE_RANGE",
            "bidLimitMultUp": "1.0001",
            "bidLimitMultDown": "0.9999",
            "askLimitMultUp": "1.0001",
            "askLimitMultDown": "0.9999"
          }
        ]
      }
    ]
  }
}

Server Shutdown
{
  "event": {
    "e": "serverShutdown", // Event Type
    "E": 1770123456789     // Event Time
  }
}

serverShutdown is sent when the server is about to shut down.

Please reconnect to WebSocket API as soon as possible to avoid stream interruption.



Market data requests
Order book
{
    "id": "51e2affb-0aba-4821-ba75-f2625006eb43",
    "method": "depth",
    "params": {
        "symbol": "BNBBTC",
        "limit": 5
    }
}

Get current order book.

Note that this request returns limited market depth.

If you need to continuously monitor order book updates, please consider using WebSocket Streams:

<symbol>@depth<levels>
<symbol>@depth
You can use depth request together with <symbol>@depth streams to maintain a local order book.

Weight: Adjusted based on the limit:

Limit	Weight
1–100	5
101–500	25
501–1000	50
1001–5000	250
Parameters:

Name	Type	Mandatory	Description
symbol	STRING	YES	
limit	INT	NO	Default: 100; Maximum: 5000
symbolStatus	ENUM	NO	Filters for symbols that have this tradingStatus.
A status mismatch returns error -1220 SYMBOL_DOES_NOT_MATCH_STATUS
Valid values: TRADING, HALT, BREAK
Data Source: Memory

Response:

{
    "id": "51e2affb-0aba-4821-ba75-f2625006eb43",
    "status": 200,
    "result": {
        "lastUpdateId": 2731179239,
        // Bid levels are sorted from highest to lowest price.
        "bids": [
            [
                "0.01379900",     // Price
                "3.43200000"      // Quantity
            ],
            ["0.01379800", "3.24300000"],
            ["0.01379700", "10.45500000"],
            ["0.01379600", "3.82100000"],
            ["0.01379500", "10.26200000"]
        ],
        // Ask levels are sorted from lowest to highest price.
        "asks": [
            ["0.01380000", "5.91700000"],
            ["0.01380100", "6.01400000"],
            ["0.01380200", "0.26800000"],
            ["0.01380300", "0.33800000"],
            ["0.01380400", "0.26800000"]
        ]
    },
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 2
        }
    ]
}

Recent trades
{
    "id": "409a20bd-253d-41db-a6dd-687862a5882f",
    "method": "trades.recent",
    "params": {
        "symbol": "BNBBTC",
        "limit": 1
    }
}

Get recent trades.

If you need access to real-time trading activity, please consider using WebSocket Streams:

<symbol>@trade
Weight: 25

Parameters:

Name	Type	Mandatory	Description
symbol	STRING	YES	
limit	INT	NO	Default: 500; Maximum: 1000
Data Source: Memory

Response:

{
    "id": "409a20bd-253d-41db-a6dd-687862a5882f",
    "status": 200,
    "result": [
        {
            "id": 194686783,
            "price": "0.01361000",
            "qty": "0.01400000",
            "quoteQty": "0.00019054",
            "time": 1660009530807,
            "isBuyerMaker": true,
            "isBestMatch": true
        }
    ],
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 2
        }
    ]
}

Historical trades
{
    "id": "cffc9c7d-4efc-4ce0-b587-6b87448f052a",
    "method": "trades.historical",
    "params": {
        "symbol": "BNBBTC",
        "fromId": 0,
        "limit": 1
    }
}

Get historical trades.

Weight: 25

Parameters:

Name	Type	Mandatory	Description
symbol	STRING	YES	
fromId	INT	NO	Trade ID to begin at
limit	INT	NO	Default: 500; Maximum: 1000
Notes:

If fromId is not specified, the most recent trades are returned.
Data Source: Database

Response:

{
    "id": "cffc9c7d-4efc-4ce0-b587-6b87448f052a",
    "status": 200,
    "result": [
        {
            "id": 0,
            "price": "0.00005000",
            "qty": "40.00000000",
            "quoteQty": "0.00200000",
            "time": 1500004800376,
            "isBuyerMaker": true,
            "isBestMatch": true
        }
    ],
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 10
        }
    ]
}

Aggregate trades
{
    "id": "189da436-d4bd-48ca-9f95-9f613d621717",
    "method": "trades.aggregate",
    "params": {
        "symbol": "BNBBTC",
        "fromId": 50000000,
        "limit": 1
    }
}

Get aggregate trades.

An aggregate trade (aggtrade) represents one or more individual trades. Trades that fill at the same time, from the same taker order, with the same price – those trades are collected into an aggregate trade with total quantity of the individual trades.

If you need access to real-time trading activity, please consider using WebSocket Streams:

<symbol>@aggTrade
If you need historical aggregate trade data, please consider using data.binance.vision.

Weight: 4

Parameters:

Name	Type	Mandatory	Description
symbol	STRING	YES	
fromId	LONG	NO	Aggregate trade ID to begin at
startTime	LONG	NO	
endTime	LONG	NO	
limit	LONG	NO	Default: 500; Maximum: 1000
Notes:

If fromId is specified, return aggtrades with aggregate trade ID >= fromId.

Use fromId and limit to page through all aggtrades.

If startTime and/or endTime are specified, aggtrades are filtered by execution time (T).

fromId cannot be used together with startTime and endTime.

If no condition is specified, the most recent aggregate trades are returned.

Data Source: Database

Response:

{
    "id": "189da436-d4bd-48ca-9f95-9f613d621717",
    "status": 200,
    "result": [
        {
            "a": 50000000,          // Aggregate trade ID
            "p": "0.00274100",      // Price
            "q": "57.19000000",     // Quantity
            "f": 59120167,          // First trade ID
            "l": 59120170,          // Last trade ID
            "T": 1565877971222,     // Timestamp
            "m": true,              // Was the buyer the maker?
            "M": true               // Was the trade the best price match?
        }
    ],
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 2
        }
    ]
}

Klines
{
    "id": "1dbbeb56-8eea-466a-8f6e-86bdcfa2fc0b",
    "method": "klines",
    "params": {
        "symbol": "BNBBTC",
        "interval": "1h",
        "startTime": 1655969280000,
        "limit": 1
    }
}

Get klines (candlestick bars).

Klines are uniquely identified by their open & close time.

If you need access to real-time kline updates, please consider using WebSocket Streams:

<symbol>@kline_<interval>
If you need historical kline data, please consider using data.binance.vision.

Weight: 2

Parameters:

Name	Type	Mandatory	Description
symbol	STRING	YES	
interval	ENUM	YES	
startTime	LONG	NO	
endTime	LONG	NO	
timeZone	STRING	NO	Default: 0 (UTC)
limit	INT	NO	Default: 500; Maximum: 1000
Supported kline intervals (case-sensitive):

Interval	interval value
seconds	1s
minutes	1m, 3m, 5m, 15m, 30m
hours	1h, 2h, 4h, 6h, 8h, 12h
days	1d, 3d
weeks	1w
months	1M
Notes:

If startTime, endTime are not specified, the most recent klines are returned.
Supported values for timeZone:
Hours and minutes (e.g. -1:00, 05:45)
Only hours (e.g. 0, 8, 4)
Accepted range is strictly [-12:00 to +14:00] inclusive
If timeZone provided, kline intervals are interpreted in that timezone instead of UTC.
Note that startTime and endTime are always interpreted in UTC, regardless of timeZone.
Data Source: Database

Response:

{
    "id": "1dbbeb56-8eea-466a-8f6e-86bdcfa2fc0b",
    "status": 200,
    "result": [
        [
            1655971200000,       // Kline open time
            "0.01086000",        // Open price
            "0.01086600",        // High price
            "0.01083600",        // Low price
            "0.01083800",        // Close price
            "2290.53800000",     // Volume
            1655974799999,       // Kline close time
            "24.85074442",       // Quote asset volume
            2283,                // Number of trades
            "1171.64000000",     // Taker buy base asset volume
            "12.71225884",       // Taker buy quote asset volume
            "0"                  // Unused field, ignore
        ]
    ],
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 2
        }
    ]
}

UI Klines
{
    "id": "b137468a-fb20-4c06-bd6b-625148eec958",
    "method": "uiKlines",
    "params": {
        "symbol": "BNBBTC",
        "interval": "1h",
        "startTime": 1655969280000,
        "limit": 1
    }
}

Get klines (candlestick bars) optimized for presentation.

This request is similar to klines, having the same parameters and response. uiKlines return modified kline data, optimized for presentation of candlestick charts.

Weight: 2

Parameters:

Name	Type	Mandatory	Description
symbol	STRING	YES	
interval	ENUM	YES	See klines
startTime	LONG	NO	
endTime	LONG	NO	
timeZone	STRING	NO	Default: 0 (UTC)
limit	INT	NO	Default: 500; Maximum: 1000
Notes:

If startTime, endTime are not specified, the most recent klines are returned.
Supported values for timeZone:
Hours and minutes (e.g. -1:00, 05:45)
Only hours (e.g. 0, 8, 4)
Accepted range is strictly [-12:00 to +14:00] inclusive
If timeZone provided, kline intervals are interpreted in that timezone instead of UTC.
Note that startTime and endTime are always interpreted in UTC, regardless of timeZone.
Data Source: Database

Response:

{
    "id": "b137468a-fb20-4c06-bd6b-625148eec958",
    "status": 200,
    "result": [
        [
            1655971200000,       // Kline open time
            "0.01086000",        // Open price
            "0.01086600",        // High price
            "0.01083600",        // Low price
            "0.01083800",        // Close price
            "2290.53800000",     // Volume
            1655974799999,       // Kline close time
            "24.85074442",       // Quote asset volume
            2283,                // Number of trades
            "1171.64000000",     // Taker buy base asset volume
            "12.71225884",       // Taker buy quote asset volume
            "0"                  // Unused field, ignore
        ]
    ],
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 2
        }
    ]
}

Current average price
{
    "id": "ddbfb65f-9ebf-42ec-8240-8f0f91de0867",
    "method": "avgPrice",
    "params": {
        "symbol": "BNBBTC"
    }
}

Get current average price for a symbol.

Weight: 2

Parameters:

Name	Type	Mandatory	Description
symbol	STRING	YES	
Data Source: Memory

Response:

{
    "id": "ddbfb65f-9ebf-42ec-8240-8f0f91de0867",
    "status": 200,
    "result": {
        "mins": 5,                     // Average price interval (in minutes)
        "price": "9.35751834",         // Average price
        "closeTime": 1694061154503     // Last trade time
    },
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 2
        }
    ]
}

24hr ticker price change statistics
{
    "id": "93fb61ef-89f8-4d6e-b022-4f035a3fadad",
    "method": "ticker.24hr",
    "params": {
        "symbol": "BNBBTC"
    }
}

Get 24-hour rolling window price change statistics.

If you need to continuously monitor trading statistics, please consider using WebSocket Streams:

<symbol>@ticker or !ticker@arr
<symbol>@miniTicker or !miniTicker@arr
If you need different window sizes, use the ticker request.

Weight: Adjusted based on the number of requested symbols:

Symbols	Weight
1–20	2
21–100	40
101 or more	80
all symbols	80
Parameters:

Name	Type	Mandatory	Description
symbol	STRING	NO	Query ticker for a single symbol
symbols	ARRAY of STRING	Query ticker for multiple symbols
type	ENUM	NO	Ticker type: FULL (default) or MINI
symbolStatus	ENUM	NO	Filters for symbols that have this tradingStatus.
For a single symbol, a status mismatch returns error -1220 SYMBOL_DOES_NOT_MATCH_STATUS.
For multiple or all symbols, non-matching ones are simply excluded from the response.
Valid values: TRADING, HALT, BREAK
Notes:

symbol and symbols cannot be used together.

If no symbol is specified, returns information about all symbols currently trading on the exchange.

Data Source: Memory

Response:

FULL type, for a single symbol:

{
    "id": "93fb61ef-89f8-4d6e-b022-4f035a3fadad",
    "status": 200,
    "result": {
        "symbol": "BNBBTC",
        "priceChange": "0.00013900",
        "priceChangePercent": "1.020",
        "weightedAvgPrice": "0.01382453",
        "prevClosePrice": "0.01362800",
        "lastPrice": "0.01376700",
        "lastQty": "1.78800000",
        "bidPrice": "0.01376700",
        "bidQty": "4.64600000",
        "askPrice": "0.01376800",
        "askQty": "14.31400000",
        "openPrice": "0.01362800",
        "highPrice": "0.01414900",
        "lowPrice": "0.01346600",
        "volume": "69412.40500000",
        "quoteVolume": "959.59411487",
        "openTime": 1660014164909,
        "closeTime": 1660100564909,
        "firstId": 194696115,     // First trade ID
        "lastId": 194968287,      // Last trade ID
        "count": 272173           // Number of trades
    },
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 2
        }
    ]
}

MINI type, for a single symbol:

{
    "id": "9fa2a91b-3fca-4ed7-a9ad-58e3b67483de",
    "status": 200,
    "result": {
        "symbol": "BNBBTC",
        "openPrice": "0.01362800",
        "highPrice": "0.01414900",
        "lowPrice": "0.01346600",
        "lastPrice": "0.01376700",
        "volume": "69412.40500000",
        "quoteVolume": "959.59411487",
        "openTime": 1660014164909,
        "closeTime": 1660100564909,
        "firstId": 194696115,     // First trade ID
        "lastId": 194968287,      // Last trade ID
        "count": 272173           // Number of trades
    },
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 2
        }
    ]
}

If more than one symbol is requested, response returns an array:

{
    "id": "901be0d9-fd3b-45e4-acd6-10c580d03430",
    "status": 200,
    "result": [
        {
            "symbol": "BNBBTC",
            "priceChange": "0.00016500",
            "priceChangePercent": "1.213",
            "weightedAvgPrice": "0.01382508",
            "prevClosePrice": "0.01360800",
            "lastPrice": "0.01377200",
            "lastQty": "1.01400000",
            "bidPrice": "0.01377100",
            "bidQty": "7.55700000",
            "askPrice": "0.01377200",
            "askQty": "4.37900000",
            "openPrice": "0.01360700",
            "highPrice": "0.01414900",
            "lowPrice": "0.01346600",
            "volume": "69376.27900000",
            "quoteVolume": "959.13277091",
            "openTime": 1660014615517,
            "closeTime": 1660101015517,
            "firstId": 194697254,
            "lastId": 194969483,
            "count": 272230
        },
        {
            "symbol": "BTCUSDT",
            "priceChange": "-938.06000000",
            "priceChangePercent": "-3.938",
            "weightedAvgPrice": "23265.34432003",
            "prevClosePrice": "23819.17000000",
            "lastPrice": "22880.91000000",
            "lastQty": "0.00536000",
            "bidPrice": "22880.40000000",
            "bidQty": "0.00424000",
            "askPrice": "22880.91000000",
            "askQty": "0.04276000",
            "openPrice": "23818.97000000",
            "highPrice": "23933.25000000",
            "lowPrice": "22664.69000000",
            "volume": "153508.37606000",
            "quoteVolume": "3571425225.04441220",
            "openTime": 1660014615977,
            "closeTime": 1660101015977,
            "firstId": 1592019902,
            "lastId": 1597301762,
            "count": 5281861
        }
    ],
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 2
        }
    ]
}

Trading Day Ticker
{
    "id": "f4b3b507-c8f2-442a-81a6-b2f12daa030f",
    "method": "ticker.tradingDay",
    "params": {
        "symbols": ["BNBBTC", "BTCUSDT"],
        "timeZone": "00:00"
    }
}

Price change statistics for a trading day.

Weight:

4 for each requested symbol.

The weight for this request will cap at 200 once the number of symbols in the request is more than 50.

Parameters:

Name	Type	Mandatory	Description
symbol	STRING	YES	Query ticker of a single symbol
symbols	ARRAY of STRING	Query ticker for multiple symbols
timeZone	STRING	NO	Default: 0 (UTC)
type	ENUM	NO	Supported values: FULL or MINI.
If none provided, the default is FULL
symbolStatus	ENUM	NO	Filters for symbols that have this tradingStatus.
For a single symbol, a status mismatch returns error -1220 SYMBOL_DOES_NOT_MATCH_STATUS.
For multiple symbols, non-matching ones are simply excluded from the response.
Valid values: TRADING, HALT, BREAK
Notes:

Supported values for timeZone:
Hours and minutes (e.g. -1:00, 05:45)
Only hours (e.g. 0, 8, 4)
Data Source: Database

Response: - FULL

With symbol:

{
    "id": "f4b3b507-c8f2-442a-81a6-b2f12daa030f",
    "status": 200,
    "result": {
        "symbol": "BTCUSDT",
        "priceChange": "-83.13000000",            // Absolute price change
        "priceChangePercent": "-0.317",           // Relative price change in percent
        "weightedAvgPrice": "26234.58803036",     // quoteVolume / volume
        "openPrice": "26304.80000000",
        "highPrice": "26397.46000000",
        "lowPrice": "26088.34000000",
        "lastPrice": "26221.67000000",
        "volume": "18495.35066000",               // Volume in base asset
        "quoteVolume": "485217905.04210480",
        "openTime": 1695686400000,
        "closeTime": 1695772799999,
        "firstId": 3220151555,
        "lastId": 3220849281,
        "count": 697727
    },
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 4
        }
    ]
}

With symbols:

{
    "id": "f4b3b507-c8f2-442a-81a6-b2f12daa030f",
    "status": 200,
    "result": [
        {
            "symbol": "BTCUSDT",
            "priceChange": "-83.13000000",
            "priceChangePercent": "-0.317",
            "weightedAvgPrice": "26234.58803036",
            "openPrice": "26304.80000000",
            "highPrice": "26397.46000000",
            "lowPrice": "26088.34000000",
            "lastPrice": "26221.67000000",
            "volume": "18495.35066000",
            "quoteVolume": "485217905.04210480",
            "openTime": 1695686400000,
            "closeTime": 1695772799999,
            "firstId": 3220151555,
            "lastId": 3220849281,
            "count": 697727
        },
        {
            "symbol": "BNBUSDT",
            "priceChange": "2.60000000",
            "priceChangePercent": "1.238",
            "weightedAvgPrice": "211.92276958",
            "openPrice": "210.00000000",
            "highPrice": "213.70000000",
            "lowPrice": "209.70000000",
            "lastPrice": "212.60000000",
            "volume": "280709.58900000",
            "quoteVolume": "59488753.54750000",
            "openTime": 1695686400000,
            "closeTime": 1695772799999,
            "firstId": 672397461,
            "lastId": 672496158,
            "count": 98698
        }
    ],
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 8
        }
    ]
}

Response: - MINI

With symbol:

{
    "id": "f4b3b507-c8f2-442a-81a6-b2f12daa030f",
    "status": 200,
    "result": {
        "symbol": "BTCUSDT",
        "openPrice": "26304.80000000",
        "highPrice": "26397.46000000",
        "lowPrice": "26088.34000000",
        "lastPrice": "26221.67000000",
        "volume": "18495.35066000",              // Volume in base asset
        "quoteVolume": "485217905.04210480",     // Volume in quote asset
        "openTime": 1695686400000,
        "closeTime": 1695772799999,
        "firstId": 3220151555,                   // Trade ID of the first trade in the interval
        "lastId": 3220849281,                    // Trade ID of the last trade in the interval
        "count": 697727                          // Number of trades in the interval
    },
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 4
        }
    ]
}

With symbols:

{
    "id": "f4b3b507-c8f2-442a-81a6-b2f12daa030f",
    "status": 200,
    "result": [
        {
            "symbol": "BTCUSDT",
            "openPrice": "26304.80000000",
            "highPrice": "26397.46000000",
            "lowPrice": "26088.34000000",
            "lastPrice": "26221.67000000",
            "volume": "18495.35066000",
            "quoteVolume": "485217905.04210480",
            "openTime": 1695686400000,
            "closeTime": 1695772799999,
            "firstId": 3220151555,
            "lastId": 3220849281,
            "count": 697727
        },
        {
            "symbol": "BNBUSDT",
            "openPrice": "210.00000000",
            "highPrice": "213.70000000",
            "lowPrice": "209.70000000",
            "lastPrice": "212.60000000",
            "volume": "280709.58900000",
            "quoteVolume": "59488753.54750000",
            "openTime": 1695686400000,
            "closeTime": 1695772799999,
            "firstId": 672397461,
            "lastId": 672496158,
            "count": 98698
        }
    ],
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 8
        }
    ]
}

Rolling window price change statistics
{
    "id": "f4b3b507-c8f2-442a-81a6-b2f12daa030f",
    "method": "ticker",
    "params": {
        "symbols": ["BNBBTC", "BTCUSDT"],
        "windowSize": "7d"
    }
}

Get rolling window price change statistics with a custom window.

This request is similar to ticker.24hr, but statistics are computed on demand using the arbitrary window you specify.

Note: Window size precision is limited to 1 minute. While the closeTime is the current time of the request, openTime always start on a minute boundary. As such, the effective window might be up to 59999 ms wider than the requested windowSize.

Window computation example
If you need to continuously monitor trading statistics, please consider using WebSocket Streams:

<symbol>@ticker_<window_size> or !ticker_<window-size>@arr
Weight: Adjusted based on the number of requested symbols:

Symbols	Weight
1–50	4 per symbol
51–100	200
Parameters:

Name	Type	Mandatory	Description
symbol	STRING	YES	Query ticker of a single symbol
symbols	ARRAY of STRING	Query ticker for multiple symbols
type	ENUM	NO	Ticker type: FULL (default) or MINI
windowSize	ENUM	NO	Default 1d
symbolStatus	ENUM	NO	Filters for symbols that have this tradingStatus.
For a single symbol, a status mismatch returns error -1220 SYMBOL_DOES_NOT_MATCH_STATUS.
For multiple symbols, non-matching ones are simply excluded from the response.
Valid values: TRADING, HALT, BREAK
Supported window sizes:

Unit	windowSize value
minutes	1m, 2m ... 59m
hours	1h, 2h ... 23h
days	1d, 2d ... 7d
Notes:

Either symbol or symbols must be specified.

Maximum number of symbols in one request: 200.

Window size units cannot be combined. E.g., 1d 2h is not supported.

Data Source: Database

Response:

FULL type, for a single symbol:

{
    "id": "f4b3b507-c8f2-442a-81a6-b2f12daa030f",
    "status": 200,
    "result": {
        "symbol": "BNBBTC",
        "priceChange": "0.00061500",
        "priceChangePercent": "4.735",
        "weightedAvgPrice": "0.01368242",
        "openPrice": "0.01298900",
        "highPrice": "0.01418800",
        "lowPrice": "0.01296000",
        "lastPrice": "0.01360400",
        "volume": "587179.23900000",
        "quoteVolume": "8034.03382165",
        "openTime": 1659580020000,
        "closeTime": 1660184865291,
        "firstId": 192977765,     // First trade ID
        "lastId": 195365758,      // Last trade ID
        "count": 2387994          // Number of trades
    },
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 4
        }
    ]
}

MINI type, for a single symbol:

{
    "id": "bdb7c503-542c-495c-b797-4d2ee2e91173",
    "status": 200,
    "result": {
        "symbol": "BNBBTC",
        "openPrice": "0.01298900",
        "highPrice": "0.01418800",
        "lowPrice": "0.01296000",
        "lastPrice": "0.01360400",
        "volume": "587179.23900000",
        "quoteVolume": "8034.03382165",
        "openTime": 1659580020000,
        "closeTime": 1660184865291,
        "firstId": 192977765,     // First trade ID
        "lastId": 195365758,      // Last trade ID
        "count": 2387994          // Number of trades
    },
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 4
        }
    ]
}

If more than one symbol is requested, response returns an array:

{
    "id": "f4b3b507-c8f2-442a-81a6-b2f12daa030f",
    "status": 200,
    "result": [
        {
            "symbol": "BNBBTC",
            "priceChange": "0.00061500",
            "priceChangePercent": "4.735",
            "weightedAvgPrice": "0.01368242",
            "openPrice": "0.01298900",
            "highPrice": "0.01418800",
            "lowPrice": "0.01296000",
            "lastPrice": "0.01360400",
            "volume": "587169.48600000",
            "quoteVolume": "8033.90114517",
            "openTime": 1659580020000,
            "closeTime": 1660184820927,
            "firstId": 192977765,
            "lastId": 195365700,
            "count": 2387936
        },
        {
            "symbol": "BTCUSDT",
            "priceChange": "1182.92000000",
            "priceChangePercent": "5.113",
            "weightedAvgPrice": "23349.27074846",
            "openPrice": "23135.33000000",
            "highPrice": "24491.22000000",
            "lowPrice": "22400.00000000",
            "lastPrice": "24318.25000000",
            "volume": "1039498.10978000",
            "quoteVolume": "24271522807.76838630",
            "openTime": 1659580020000,
            "closeTime": 1660184820927,
            "firstId": 1568787779,
            "lastId": 1604337406,
            "count": 35549628
        }
    ],
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 8
        }
    ]
}

Symbol price ticker
{
    "id": "043a7cf2-bde3-4888-9604-c8ac41fcba4d",
    "method": "ticker.price",
    "params": {
        "symbol": "BNBBTC"
    }
}

Get the latest market price for a symbol.

If you need access to real-time price updates, please consider using WebSocket Streams:

<symbol>@aggTrade
<symbol>@trade
Weight: Adjusted based on the number of requested symbols:

Parameter	Weight
symbol	2
symbols	4
none	4
Parameters:

Name	Type	Mandatory	Description
symbol	STRING	NO	Query price for a single symbol
symbols	ARRAY of STRING	Query price for multiple symbols
symbolStatus	ENUM	NO	Filters for symbols that have this tradingStatus.
For a single symbol, a status mismatch returns error -1220 SYMBOL_DOES_NOT_MATCH_STATUS.
For multiple or all symbols, non-matching ones are simply excluded from the response.
Valid values: TRADING, HALT, BREAK
Notes:

symbol and symbols cannot be used together.

If no symbol is specified, returns information about all symbols currently trading on the exchange.

Data Source: Memory

Response:

{
    "id": "043a7cf2-bde3-4888-9604-c8ac41fcba4d",
    "status": 200,
    "result": {
        "symbol": "BNBBTC",
        "price": "0.01361900"
    },
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 2
        }
    ]
}

If more than one symbol is requested, response returns an array:

{
    "id": "e739e673-24c8-4adf-9cfa-b81f30330b09",
    "status": 200,
    "result": [
        {
            "symbol": "BNBBTC",
            "price": "0.01363700"
        },
        {
            "symbol": "BTCUSDT",
            "price": "24267.15000000"
        },
        {
            "symbol": "BNBBUSD",
            "price": "331.10000000"
        }
    ],
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 4
        }
    ]
}

Symbol order book ticker
{
    "id": "057deb3a-2990-41d1-b58b-98ea0f09e1b4",
    "method": "ticker.book",
    "params": {
        "symbols": ["BNBBTC", "BTCUSDT"]
    }
}

Get the current best price and quantity on the order book.

If you need access to real-time order book ticker updates, please consider using WebSocket Streams:

<symbol>@bookTicker
Weight: Adjusted based on the number of requested symbols:

Parameter	Weight
symbol	2
symbols	4
none	4
Parameters:

Name	Type	Mandatory	Description
symbol	STRING	NO	Query ticker for a single symbol
symbols	ARRAY of STRING	Query ticker for multiple symbols
symbolStatus	ENUM	NO	Filters for symbols that have this tradingStatus.
For a single symbol, a status mismatch returns error -1220 SYMBOL_DOES_NOT_MATCH_STATUS.
For multiple or all symbols, non-matching ones are simply excluded from the response.
Valid values: TRADING, HALT, BREAK
Notes:

symbol and symbols cannot be used together.

If no symbol is specified, returns information about all symbols currently trading on the exchange.

Data Source: Memory

Response:

{
    "id": "9d32157c-a556-4d27-9866-66760a174b57",
    "status": 200,
    "result": {
        "symbol": "BNBBTC",
        "bidPrice": "0.01358000",
        "bidQty": "12.53400000",
        "askPrice": "0.01358100",
        "askQty": "17.83700000"
    },
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 2
        }
    ]
}

If more than one symbol is requested, response returns an array:

{
    "id": "057deb3a-2990-41d1-b58b-98ea0f09e1b4",
    "status": 200,
    "result": [
        {
            "symbol": "BNBBTC",
            "bidPrice": "0.01358000",
            "bidQty": "12.53400000",
            "askPrice": "0.01358100",
            "askQty": "17.83700000"
        },
        {
            "symbol": "BTCUSDT",
            "bidPrice": "23980.49000000",
            "bidQty": "0.01000000",
            "askPrice": "23981.31000000",
            "askQty": "0.01512000"
        }
    ],
    "rateLimits": [
        {
            "rateLimitType": "REQUEST_WEIGHT",
            "interval": "MINUTE",
            "intervalNum": 1,
            "limit": 6000,
            "count": 4
        }
    ]
}

Query Reference Price
{
  "id": "5132affb-0aba-4821-b475-f262504556b43",
  "method": "referencePrice",
  "params": {
    "symbol": "BAZUSD"
  }
}

Weight: 2

Parameters:

Name	Type	Mandatory	Description
symbol	STRING	Yes	
Data Source:

Response:

If a reference price is set:

{
  "id": "5132affb-0aba-4821-b475-f262504556b43",
  "status": 200,
  "result": {
    "symbol": "BAZUSD",
    "referencePrice": "0.00501900",
    "timestamp": 1770946889251     //Timestamp when the reference price was valid
  }
}

If no reference price is set:

{
  "id": "5132affb-0aba-4821-b475-f262504556b43",
  "status": 200,
  "result": {
    "symbol": "BAZUSD",
    "referencePrice": null,
    "timestamp": 1770946889251      //Timestamp when the reference price was valid
  }
}

Query Reference Price Calculation
{
  "id": "5132affa-0aba-4831-b475-f262504556b41",
  "method": "referencePrice.calculation",
  "params": {
    "symbol": "BAZUSD"
  }
}

Describes how reference price is calculated for a given symbol.

Weight: 2

Parameters:

Name	Type	Mandatory	Description
symbol	STRING	Yes	
symbolStatus	ENUM	No	Supported values: TRADING, HALT, BREAK
Data Source: Memory

Response:

If reference price is not being calculated:

{
    "id": "5132affa-0aba-4831-b475-f262504556b41",
    "status": 400,
    "error":
    {
        "code": -2043,
        "msg": "This symbol doesn't have a reference price."
    }
}

If the reference price is being calculated by the matching engine as an arithmetic mean:

{
    "id": "5132affa-0aba-4831-b475-f262504556b41",
    "status": 200,
    "result":
    {
        "symbol": "BAZUSD",
        "calculationType": "ARITHMETIC_MEAN",
        "bucketCount": 10,
        "bucketWidthMs": 1000
    }
}

If the reference price is being calculated outside the matching engine:

{
    "id": "5132affa-0aba-4831-b475-f262504556b41",
    "status": 200,
    "result":
    {
        "symbol": "BAZUSD",
        "calculationType": "EXTERNAL",
        "externalCalculationId": 42
    }
}