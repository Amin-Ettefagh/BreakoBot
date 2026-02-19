CREATE TABLE IF NOT EXISTS schema_version (
    id INT PRIMARY KEY,
    version INT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    username VARCHAR(255),
    role ENUM('free', 'vip', 'extreme') DEFAULT 'free',
    expire_at DATETIME DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    daily_free_limit INT DEFAULT 2,
    UNIQUE KEY uq_users_telegram_id (telegram_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) NOT NULL,
    setting_value VARCHAR(255) NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_settings_key (setting_key)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

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
