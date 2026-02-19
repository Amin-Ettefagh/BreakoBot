# Crypto Signal Bot

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-green)

A production-grade Telegram trading-signal bot that delivers scheduled spot analysis, real-time futures breakout alerts, and role-based access management. Built with aiogram v3 and MariaDB, it is designed for reliability, extensibility, and safe operations in both local and Docker environments.

**Key Features**
- Role-based access: Free, VIP, Extreme with optional expiry
- Scheduled spot analysis using RSI/EMA/MACD
- Futures breakout alerts on 1m timeframe (Extreme only)
- Daily reset of Free quotas at midnight (server time)
- Admin panel: add/update users, deactivate, stats, export logs, broadcast
- Resilient MEXC calls with retries and throttling
- Telegram sending safeguards, throttling, and anti-duplicate broadcasts
- Optional trader bridge (webhook sender + FastAPI receiver)
- Docker Compose ready with health checks and log rotation

**Architecture Overview**
```
            +---------------------+
            |   Telegram Clients  |
            +----------+----------+
                       |
                       v
                 +-----------+
                 |  aiogram  |
                 +-----+-----+
                       |
      +----------------+----------------+
      |                                 |
      v                                 v
+-----------+                    +--------------+
| Handlers  |                    | Background   |
| user/admin|                    | Tasks        |
+-----+-----+                    +------+-------+
      |                                 |
      v                                 v
+-----------+                     +-------------+
| Database  |<------------------->| Services    |
+-----------+                     | analysis,   |
                                  | sender,     |
                                  | mexc_api    |
                                  +-------------+
```

**Tech Stack**
- Python 3.11+
- aiogram v3
- MariaDB/MySQL (aiomysql)
- aiohttp for HTTP
- pandas/numpy for indicators
- Docker + Docker Compose

**Folder Structure**
- `app/` application code
- `app/handlers/` Telegram command handlers and FSM
- `app/services/` analysis, sending, cycles, bridge, MEXC client
- `app/db/` DB access layer and schema
- `app/utils/` logging, backoff, validation, time helpers
- `docs/` extended documentation
- `tests/` unit and smoke tests

**How It Works (Flow)**
1. User sends `/start` and is registered if missing.
2. Background tasks run based on feature flags.
3. Spot cycle fetches candles, calculates indicators, stores cache, sends signals.
4. Futures breakout watches 1m candles and sends alerts to Extreme users.
5. Daily reset restores Free limits at midnight.
6. Admins manage roles, exports, stats, and broadcasts.

**Role System**
- Free: daily signal limit with midnight reset.
- VIP: unlimited spot signals.
- Extreme: unlimited spot signals + futures breakout alerts.
- Expired users receive no automated messages.

**Scheduling**
- Spot cycle runs every `SPOT_CYCLE_SECONDS`.
- Breakout checks run every `FUTURES_BREAKOUT_SECONDS`.
- Daily reset runs at midnight server time.

**Breakout Logic**
- Timeframe: 1m.
- Condition: last close > max(high) over lookback window.
- Anti-duplicate: suppress repeated alerts for same price within cooldown.

**Admin Panel Capabilities**
- Add/update subscription and expiry
- Deactivate user
- Broadcast to all active users
- View recent logs
- Stats: users by role, signals in last 24h, top coins
- Export logs as CSV
- Update Free limit at runtime
- Reload coins list

**Feature Flags**
- `ENABLE_SPOT_CYCLE`
- `ENABLE_FUTURES_BREAKOUT`
- `ENABLE_DAILY_RESET`
- `ENABLE_TRADER_BRIDGE`

**Environment Variables Summary**
| Name | Default | Description |
| --- | --- | --- |
| BOT_TOKEN | none | Telegram bot token (required) |
| DB_PASSWORD | none | DB user password (required) |
| DB_HOST | localhost | Database host |
| DB_PORT | 3306 | Database port |
| DB_USER | root | Database user |
| DB_NAME | crypto_bot | Database name |
| ADMINS | - | Comma-separated admin IDs |
| COINS_LIST | BTC_USDT,ETH_USDT | Symbols to analyze |
| TIMEFRAME | 1h | Spot timeframe |
| SPOT_CYCLE_SECONDS | 3600 | Spot cycle interval |
| FUTURES_BREAKOUT_SECONDS | 30 | Breakout scan interval |
| DEFAULT_FREE_LIMIT | 2 | Free daily limit |
| ENABLE_* | true/false | Feature flags |

Full reference in `docs/CONFIG.md`.

**Local Development**
1. Create `.env` from `.env.example` and set required values.
2. Install dependencies:
```
python -m pip install -r requirements.txt
```
3. Run:
```
python -m app.main
```

**Docker Deployment**
1. Create `.env` from `.env.example` and set required values.
2. Build and start:
```
docker compose up -d --build
```
3. View logs:
```
docker compose logs -f bot
```

**Production Deployment (VPS Example)**
1. Provision a VPS (Ubuntu 22.04 recommended).
2. Install Docker and Compose.
3. Clone repo and create `.env` with production values.
4. Restrict DB exposure and open only required ports.
5. Start services:
```
docker compose up -d --build
```
6. Monitor logs and system resources.

**Security Considerations**
- Keep `BOT_TOKEN` and DB credentials in secrets, never in Git.
- Restrict database access to internal networks.
- Limit admin IDs to trusted accounts.
- Enable bridge only when needed, secure it with tokens.

**Performance Considerations**
- Increase `TELEGRAM_SEND_DELAY_SECONDS` for large broadcasts.
- Use `MEXC_MIN_INTERVAL_SECONDS` to avoid throttling.
- Scale DB resources for high signal volume.

**Troubleshooting**
- Bot not starting: verify `BOT_TOKEN` and DB envs.
- No signals: check feature flags and `COINS_LIST`.
- MEXC errors: increase timeout and retries.
- Telegram rate limits: increase send delay.

**Contributing**
Open a PR from a feature branch, run `ruff` and `pytest`, and include a clear summary. See `CONTRIBUTING.md`.

**Roadmap**
- Strategy customization per symbol and timeframe
- Multiple exchange integrations
- Web dashboard for admins
- Metrics and alerting integrations
- Per-user notification preferences
- Signal caching and dedup at scale

**License**
MIT License. See `LICENSE`.
