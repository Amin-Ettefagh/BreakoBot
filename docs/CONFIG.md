# Configuration Reference

All configuration is loaded from environment variables or `.env`.
Defaults are applied where safe; missing required values will fail fast.

## Required Variables
- `BOT_TOKEN`: Telegram bot token.
- `DB_PASSWORD`: Database user password.
- `DB_ROOT_PASSWORD`: MariaDB root password (Docker only).

## Optional Variables
### Database
- `DB_HOST`: Database host (default `localhost`).
- `DB_PORT`: Database port (default `3306`).
- `DB_USER`: Database user (default `root`).
- `DB_NAME`: Database name (default `crypto_bot`).

### Roles and Admin
- `ADMINS`: Comma-separated Telegram IDs with admin access.
- `DEFAULT_FREE_LIMIT`: Daily free signals limit (default `2`).

### Coins and Scheduling
- `COINS_LIST`: Comma-separated symbols (e.g., `BTC_USDT,ETH_USDT`).
- `TIMEFRAME`: Spot analysis timeframe (default `1h`).
- `SPOT_CYCLE_SECONDS`: Spot interval (default `3600`).
- `FUTURES_BREAKOUT_SECONDS`: Breakout check interval (default `30`).
- `FUTURES_BREAKOUT_LOOKBACK`: Breakout lookback bars (default `3`).
- `FUTURES_BREAKOUT_COOLDOWN_SECONDS`: Cooldown per symbol (default `300`).

### Logging
- `LOG_LEVEL`: Log level (default `INFO`).
- `LOG_DIR`: Log directory (default `logs`).
- `LOG_RETENTION_DAYS`: Retention days (minimum `14`).

### MEXC API
- `MEXC_BASE_URL`: Base URL (default `https://www.mexc.com`).
- `MEXC_TIMEOUT_SECONDS`: HTTP timeout (default `15`).
- `MEXC_RETRIES`: Retry count (default `3`).
- `MEXC_BACKOFF_BASE`: Backoff base delay (default `0.5`).
- `MEXC_MIN_INTERVAL_SECONDS`: Minimum delay between requests (default `0.1`).

### Telegram Sending
- `TELEGRAM_RETRIES`: Retry count (default `2`).
- `TELEGRAM_BACKOFF_BASE`: Backoff base delay (default `0.5`).
- `TELEGRAM_SEND_DELAY_SECONDS`: Throttle between sends (default `0.2`).
- `BROADCAST_COOLDOWN_SECONDS`: Min seconds between broadcasts (default `60`).
- `BROADCAST_DUPLICATE_WINDOW_SECONDS`: Prevent duplicate broadcast in this window (default `300`).

### Feature Flags
- `ENABLE_SPOT_CYCLE`: Enable/disable spot cycle (default `true`).
- `ENABLE_FUTURES_BREAKOUT`: Enable/disable breakout alerts (default `true`).
- `ENABLE_DAILY_RESET`: Enable/disable midnight reset (default `true`).
- `ENABLE_TRADER_BRIDGE`: Enable/disable webhook bridge (default `false`).

### Trader Bridge (Optional)
- `TRADER_BRIDGE_URL`: Webhook URL (required when bridge enabled).
- `TRADER_BRIDGE_TOKEN`: Shared secret token for Authorization or receiver header.
- `TRADER_BRIDGE_TIMEOUT_SECONDS`: HTTP timeout (default `10`).
- `TRADER_BRIDGE_RETRIES`: Retry count (default `2`).
- `TRADER_BRIDGE_BACKOFF_BASE`: Backoff base delay (default `0.5`).

When running the FastAPI receiver, ensure `ENABLE_TRADER_BRIDGE=true`.

## Example Configurations
### Development (Minimal)
```
BOT_TOKEN=123456:abc
DB_PASSWORD=dev_pass
DB_HOST=127.0.0.1
DB_USER=crypto_bot
DB_NAME=crypto_bot
ADMINS=123456789
COINS_LIST=BTC_USDT,ETH_USDT
ENABLE_TRADER_BRIDGE=false
```

### Production (Docker)
```
BOT_TOKEN=123456:prod
DB_PASSWORD=strong_db_pass
DB_ROOT_PASSWORD=strong_root_pass
DB_HOST=db
DB_USER=crypto_bot
DB_NAME=crypto_bot
ADMINS=123456789,987654321
COINS_LIST=BTC_USDT,ETH_USDT,SOL_USDT
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30
MEXC_TIMEOUT_SECONDS=20
TELEGRAM_SEND_DELAY_SECONDS=0.4
ENABLE_TRADER_BRIDGE=false
```
