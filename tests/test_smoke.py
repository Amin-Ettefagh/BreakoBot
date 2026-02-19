import asyncio

from app.config import load_config
from app.db.database import Database


class DummyCursor:
    def __init__(self) -> None:
        self.queries = []

    async def execute(self, query, params=None):
        self.queries.append(query)

    async def fetchone(self):
        return None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class DummyConn:
    def __init__(self, cursor: DummyCursor) -> None:
        self._cursor = cursor

    def cursor(self, *args, **kwargs):
        return self._cursor

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class DummyPool:
    def __init__(self, cursor: DummyCursor) -> None:
        self._cursor = cursor

    def acquire(self):
        return DummyConn(self._cursor)


def test_config_and_schema_smoke(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.setenv("DB_PASSWORD", "test-pass")
    monkeypatch.setenv("COINS_LIST", "BTC_USDT")

    cfg = load_config()
    assert cfg.bot_token == "test-token"

    cursor = DummyCursor()
    db = Database(cfg)
    db.pool = DummyPool(cursor)

    asyncio.run(db.init_schema())

    ddl = "\n".join(cursor.queries)
    assert "schema_version" in ddl
    assert "settings" in ddl
    assert "uq_users_telegram_id" in ddl
    assert "uq_analysis_coin" in ddl
