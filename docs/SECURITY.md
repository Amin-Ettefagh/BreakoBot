# Security Guidance

## Token Handling
- Treat `BOT_TOKEN` and `TRADER_BRIDGE_TOKEN` as secrets.
- Store secrets in `.env` locally and secret managers in production.
- Never commit secrets to Git.

## Environment Best Practices
- Use different `.env` files for dev and prod.
- Restrict file permissions on `.env`.
- Rotate secrets periodically and after any suspected exposure.

## Database Security
- Keep DB on private networks or localhost only.
- Use strong passwords and least-privilege users.
- Enable backups and monitor for failed logins.

## Telegram Security Considerations
- Limit `ADMINS` to trusted accounts only.
- Avoid sending sensitive info in broadcast messages.
- Be aware that users can block the bot at any time.

## API Rate Limiting
- MEXC calls are throttled via `MEXC_MIN_INTERVAL_SECONDS`.
- Telegram sends are throttled via `TELEGRAM_SEND_DELAY_SECONDS`.
- Broadcasts are protected by a cooldown and duplicate window.

## Future Hardening Ideas
- Add IP allowlists for the webhook receiver.
- Integrate with a secrets manager.
- Add structured audit logs and alerts.
- Add monitoring for abnormal error rates.

For security reporting, see root `SECURITY.md`.
