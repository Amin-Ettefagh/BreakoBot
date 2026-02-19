import pytest

from app.config import load_config


def test_missing_required_env(monkeypatch):
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    monkeypatch.setenv("COINS_LIST", "BTC_USDT")

    with pytest.raises(RuntimeError) as exc:
        load_config()
    msg = str(exc.value)
    assert "BOT_TOKEN is required" in msg
    assert "DB_PASSWORD is required" in msg


def test_invalid_retention(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "test")
    monkeypatch.setenv("DB_PASSWORD", "test")
    monkeypatch.setenv("COINS_LIST", "BTC_USDT")
    monkeypatch.setenv("LOG_RETENTION_DAYS", "3")

    with pytest.raises(RuntimeError) as exc:
        load_config()
    assert "LOG_RETENTION_DAYS must be >= 14" in str(exc.value)


def test_trader_bridge_requires_url(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "test")
    monkeypatch.setenv("DB_PASSWORD", "test")
    monkeypatch.setenv("COINS_LIST", "BTC_USDT")
    monkeypatch.setenv("ENABLE_TRADER_BRIDGE", "true")
    monkeypatch.delenv("TRADER_BRIDGE_URL", raising=False)

    with pytest.raises(RuntimeError) as exc:
        load_config()
    assert "TRADER_BRIDGE_URL" in str(exc.value)
