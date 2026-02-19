"""Database access layer using aiomysql.`n`nContains schema initialization, settings management, and query helpers.`n"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import aiomysql

from app.config import Config


SCHEMA_VERSION = 1


class Database:
    """Thin wrapper around aiomysql pool with helper queries."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self.pool: Optional[aiomysql.Pool] = None

    async def connect(self) -> None:
        self.pool = await aiomysql.create_pool(
            host=self._config.db_host,
            port=self._config.db_port,
            user=self._config.db_user,
            password=self._config.db_password,
            db=self._config.db_name,
            autocommit=True,
            minsize=1,
            maxsize=10,
        )

    async def close(self) -> None:
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

    def _require_pool(self) -> aiomysql.Pool:
        if not self.pool:
            raise RuntimeError("DB pool is not initialized")
        return self.pool

    async def init_schema(self) -> None:
        """Create tables if they do not exist."""
        ddl = [
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                id INT PRIMARY KEY,
                version INT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """,
            f"""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                telegram_id BIGINT NOT NULL,
                username VARCHAR(255),
                role ENUM('free', 'vip', 'extreme') DEFAULT 'free',
                expire_at DATETIME DEFAULT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                daily_free_limit INT DEFAULT {self._config.default_free_limit},
                UNIQUE KEY uq_users_telegram_id (telegram_id)
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS settings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                setting_key VARCHAR(100) NOT NULL,
                setting_value VARCHAR(255) NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_settings_key (setting_key)
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS signals_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                coin VARCHAR(20),
                type ENUM('spot', 'futures'),
                signal_text TEXT,
                target_group ENUM('free', 'vip', 'extreme'),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                KEY idx_signals_created (created_at),
                KEY idx_signals_coin_created (coin, created_at)
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS analysis_cache (
                id INT AUTO_INCREMENT PRIMARY KEY,
                coin VARCHAR(20) NOT NULL,
                rsi FLOAT,
                macd FLOAT,
                ema20 FLOAT,
                ema50 FLOAT,
                volume FLOAT,
                breakout BOOLEAN,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_analysis_coin (coin),
                KEY idx_analysis_updated (updated_at)
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """,
        ]

        pool = self._require_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                for q in ddl:
                    await cur.execute(q)

                # Best-effort index creation for existing tables (ignore errors if already exists)
                for q in [
                    "ALTER TABLE signals_log ADD INDEX idx_signals_created (created_at)",
                    "ALTER TABLE signals_log ADD INDEX idx_signals_coin_created (coin, created_at)",
                    "ALTER TABLE analysis_cache ADD INDEX idx_analysis_updated (updated_at)",
                ]:
                    try:
                        await cur.execute(q)
                    except Exception:
                        pass

        await self._ensure_schema_version()
        await self._ensure_default_settings()

    async def _ensure_schema_version(self) -> None:
        pool = self._require_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT version FROM schema_version WHERE id=1")
                row = await cur.fetchone()
                if not row:
                    await cur.execute(
                        "INSERT INTO schema_version (id, version) VALUES (1, %s)",
                        (SCHEMA_VERSION,),
                    )
                    return
                if int(row["version"]) < SCHEMA_VERSION:
                    await cur.execute(
                        "UPDATE schema_version "
                        "SET version=%s, updated_at=CURRENT_TIMESTAMP "
                        "WHERE id=1",
                        (SCHEMA_VERSION,),
                    )

    async def _ensure_default_settings(self) -> None:
        if await self.get_setting("default_free_limit") is None:
            await self.set_setting("default_free_limit", str(self._config.default_free_limit))

    async def add_user_if_not_exists(self, telegram_id: int, username: Optional[str]) -> None:
        default_limit = await self.get_default_free_limit()
        q = """
            INSERT INTO users (telegram_id, username, daily_free_limit)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE username=VALUES(username);
        """
        pool = self._require_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(q, (telegram_id, username, default_limit))

    async def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        q = "SELECT * FROM users WHERE telegram_id=%s"
        pool = self._require_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(q, (telegram_id,))
                return await cur.fetchone()

    async def set_role(self, telegram_id: int, role: str, expire_at: Optional[datetime]) -> None:
        q = "UPDATE users SET role=%s, expire_at=%s, is_active=1 WHERE telegram_id=%s"
        pool = self._require_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(q, (role, expire_at, telegram_id))

    async def deactivate_user(self, telegram_id: int) -> None:
        q = "UPDATE users SET is_active=0 WHERE telegram_id=%s"
        pool = self._require_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(q, (telegram_id,))

    async def fetch_active_users_by_role(self, role: str) -> List[Dict[str, Any]]:
        q = """
            SELECT * FROM users
            WHERE role=%s AND is_active=1
              AND (expire_at IS NULL OR expire_at > NOW())
        """
        pool = self._require_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(q, (role,))
                return await cur.fetchall()

    async def fetch_all_active_users(self) -> List[Dict[str, Any]]:
        q = """
            SELECT * FROM users
            WHERE is_active=1 AND (expire_at IS NULL OR expire_at > NOW())
        """
        pool = self._require_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(q)
                return await cur.fetchall()

    async def decrease_free_limit(self, telegram_id: int) -> None:
        q = """
            UPDATE users
            SET daily_free_limit = GREATEST(daily_free_limit - 1, 0)
            WHERE telegram_id=%s AND role='free'
        """
        pool = self._require_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(q, (telegram_id,))

    async def reset_daily_limits(self) -> None:
        default_limit = await self.get_default_free_limit()
        q = "UPDATE users SET daily_free_limit=%s WHERE role='free'"
        pool = self._require_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(q, (default_limit,))

    async def log_signal(self, coin: str, s_type: str, text: str, target: str) -> None:
        q = "INSERT INTO signals_log (coin, type, signal_text, target_group) VALUES (%s,%s,%s,%s)"
        pool = self._require_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(q, (coin, s_type, text, target))

    async def get_last_logs(self, limit: int = 10) -> List[Tuple]:
        q = "SELECT coin, type, target_group, created_at FROM signals_log ORDER BY id DESC LIMIT %s"
        pool = self._require_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(q, (limit,))
                return await cur.fetchall()

    async def upsert_analysis_cache(
        self,
        coin: str,
        rsi: float,
        macd: float,
        ema20: float,
        ema50: float,
        volume: float,
        breakout: bool,
    ) -> None:
        q = """
            INSERT INTO analysis_cache (coin, rsi, macd, ema20, ema50, volume, breakout)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
              rsi=VALUES(rsi),
              macd=VALUES(macd),
              ema20=VALUES(ema20),
              ema50=VALUES(ema50),
              volume=VALUES(volume),
              breakout=VALUES(breakout),
              updated_at=CURRENT_TIMESTAMP
        """
        pool = self._require_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(q, (coin, rsi, macd, ema20, ema50, volume, breakout))

    async def fetch_expired_users(self) -> List[Dict[str, Any]]:
        q = "SELECT * FROM users WHERE expire_at IS NOT NULL AND expire_at <= NOW()"
        pool = self._require_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(q)
                return await cur.fetchall()

    async def count_users_by_role(self) -> List[Tuple[str, int]]:
        q = "SELECT role, COUNT(*) FROM users GROUP BY role"
        pool = self._require_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(q)
                return await cur.fetchall()

    async def count_signals_last_24h(self) -> int:
        q = "SELECT COUNT(*) FROM signals_log WHERE created_at >= (NOW() - INTERVAL 1 DAY)"
        pool = self._require_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(q)
                row = await cur.fetchone()
                return int(row[0]) if row else 0

    async def top_coins_by_signals(self, limit: int = 5) -> List[Tuple[str, int]]:
        q = (
            "SELECT coin, COUNT(*) as cnt FROM signals_log "
            "WHERE created_at >= (NOW() - INTERVAL 1 DAY) "
            "GROUP BY coin ORDER BY cnt DESC LIMIT %s"
        )
        pool = self._require_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(q, (limit,))
                return await cur.fetchall()

    async def export_signals_log(self, limit: int = 500) -> List[Tuple]:
        q = (
            "SELECT coin, type, target_group, created_at, signal_text "
            "FROM signals_log ORDER BY id DESC LIMIT %s"
        )
        pool = self._require_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(q, (limit,))
                return await cur.fetchall()

    async def get_setting(self, key: str) -> Optional[str]:
        q = "SELECT setting_value FROM settings WHERE setting_key=%s"
        pool = self._require_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(q, (key,))
                row = await cur.fetchone()
                return row[0] if row else None

    async def set_setting(self, key: str, value: str) -> None:
        q = (
            "INSERT INTO settings (setting_key, setting_value) VALUES (%s, %s) "
            "ON DUPLICATE KEY UPDATE setting_value=VALUES(setting_value), "
            "updated_at=CURRENT_TIMESTAMP"
        )
        pool = self._require_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(q, (key, value))

    async def get_default_free_limit(self) -> int:
        value = await self.get_setting("default_free_limit")
        if value is None:
            return self._config.default_free_limit
        try:
            return max(int(value), 0)
        except ValueError:
            return self._config.default_free_limit

    async def set_default_free_limit(self, limit: int) -> None:
        await self.set_setting("default_free_limit", str(max(limit, 0)))

