# Trader Bridge API

This optional webhook receives signals for auto-trading integration.

## Endpoint
- `POST /webhook`

## Authentication
- Header: `X-Bridge-Token: <token>`
- Required when `TRADER_BRIDGE_TOKEN` is set.

## Enable (Sender)
Set in `.env`:
- `ENABLE_TRADER_BRIDGE=true`
- `TRADER_BRIDGE_URL=https://your-webhook`
- `TRADER_BRIDGE_TOKEN=your-token`

## Receiver (FastAPI)
Run the receiver separately:
```
ENABLE_TRADER_BRIDGE=true TRADER_BRIDGE_TOKEN=your-token \
uvicorn app.services.optional_bridge:create_app --factory --host 0.0.0.0 --port 9000
```

## Request Example
```
{
  "type": "spot",
  "symbol": "BTC_USDT",
  "interval": "1h",
  "message": "..."
}
```

## Response Example
```
{
  "status": "ok"
}
```

## Error Cases
- `401 Unauthorized`: missing or invalid `X-Bridge-Token`.
- `400 Bad Request`: invalid JSON payload.
- `500 Internal Server Error`: unexpected server error.

## cURL Example
```
curl -X POST http://localhost:9000/webhook \
  -H "Content-Type: application/json" \
  -H "X-Bridge-Token: your-token" \
  -d '{"type":"spot","symbol":"BTC_USDT","interval":"1h","message":"test"}'
```
