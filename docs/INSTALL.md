# Install Guide

This guide covers local installation and Docker-based deployment.

## Prerequisites
- Python 3.11+
- MariaDB/MySQL
- Docker + Docker Compose (optional)

## Database Setup (Local)
1. Install MariaDB/MySQL and start the service.
2. Create a database and user:
```
CREATE DATABASE crypto_bot;
CREATE USER 'crypto_bot'@'localhost' IDENTIFIED BY 'strong_password';
GRANT ALL PRIVILEGES ON crypto_bot.* TO 'crypto_bot'@'localhost';
FLUSH PRIVILEGES;
```
3. Update `.env` with DB credentials.

## Local Setup
1. Create a virtual environment:
```
python -m venv .venv
```
2. Activate it (Windows PowerShell):
```
.\.venv\Scripts\Activate.ps1
```
3. Install dependencies:
```
python -m pip install -r requirements.txt
```
4. Create `.env` from `.env.example` and fill required values.
5. Run the bot:
```
python -m app.main
```

## Docker Setup
1. Create `.env` from `.env.example` and fill required values.
2. Build and run:
```
docker compose up -d --build
```
3. Follow logs:
```
docker compose logs -f bot
```

## Common Errors
- Bot fails on start: ensure `BOT_TOKEN` and `DB_PASSWORD` are set.
- DB connection refused: check `DB_HOST`, `DB_PORT`, and DB service status.
- No signals: verify `COINS_LIST` and `ENABLE_SPOT_CYCLE`.
- MEXC errors: increase `MEXC_TIMEOUT_SECONDS` or `MEXC_RETRIES`.
- Telegram rate limit: increase `TELEGRAM_SEND_DELAY_SECONDS`.
