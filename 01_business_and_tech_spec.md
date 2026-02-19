# پروژه: Crypto Signal Bot + VIP Management + (اختیاری) AutoTrader Bridge

این سند برای «ایجنت توسعه» نوشته شده تا دقیق بداند بیزنس چه می‌خواهد، چه اجزایی لازم است، و کد چگونه باید ساختاربندی و کامل شود.

---

## 1) هدف بیزنس (Business Objective)

یک سیستم تلگرامی که:
1) کاربران را ثبت می‌کند و سطح دسترسی **Free / VIP / Extreme** مدیریت می‌کند (اشتراک، تاریخ انقضا، فعال/غیرفعال).
2) به صورت زمان‌بندی‌شده داده بازار را از **MEXC** می‌گیرد و تحلیل تکنیکال انجام می‌دهد (RSI/EMA/MACD/Volume/Breakout).
3) خروجی را به پیام سیگنال تبدیل می‌کند و به کاربران ارسال می‌کند:
   - **Free**: محدودیت روزانه (مثلاً 2 سیگنال در روز)
   - **VIP**: بدون محدودیت
   - **Extreme**: بدون محدودیت + هشدار Breakout لحظه‌ای Futures (تایم‌فریم 1m)
4) پنل **Admin** دارد:
   - افزودن/بروزرسانی اشتراک کاربر (Role + Expire)
   - غیرفعال کردن کاربر
   - ارسال پیام همگانی
   - مشاهده لاگ سیگنال‌ها
5) (اختیاری/مرحله بعد) خروجی سیگنال بتواند به یک سرویس اتوتریدر متصل شود (Webhook) تا معامله خودکار انجام شود.

---

## 2) Scope و Deliverables

### نسخه MVP (در همین فایل کد مونولیت ارائه شده)
- ربات تلگرام (aiogram v3)
- دیتابیس MySQL/MariaDB (aiomysql)
- تحلیل تکنیکال ساده با pandas (RSI/EMA/MACD/Breakout)
- Scheduler داخلی (asyncio tasks) برای:
  - ارسال سیگنال Spot هر 1 ساعت (قابل تنظیم)
  - چک Breakout Futures هر 30 ثانیه (قابل تنظیم)
  - Reset سهمیه Free در نیمه‌شب
- پنل ادمین با FSM ساده
- لاگینگ استاندارد

### نسخه Production-Ready (برای ایجنت)
ایجنت باید پس از دریافت کد مونولیت:
- ساختار پروژه را به پکیج‌های جدا تبدیل کند (handlers/services/db/config)
- Dockerfile + docker-compose (ربات + DB) بسازد
- مدیریت secrets با .env (python-dotenv)
- Rate-limit و backoff برای API calls بهتر کند
- صحت‌سنجی سیگنال و مدیریت خطاها را کامل‌تر کند
- Observability: log rotation + metrics (اختیاری)
- تست‌ها (حداقل smoke test) اضافه کند

---

## 3) نیازمندی‌های فنی (Technical Requirements)

### 3.1 تکنولوژی‌ها
- Python 3.11+
- aiogram v3 (Telegram Bot Framework)
- aiomysql (async MySQL/MariaDB)
- aiohttp (HTTP async برای MEXC)
- pandas / numpy (تحلیل تکنیکال)
- Optional: python-dotenv (env loading)

### 3.2 دیتابیس و Schema
سه جدول اصلی:

#### users
- telegram_id (Unique)
- username
- role: ENUM('free','vip','extreme')
- expire_at (nullable)
- is_active
- daily_free_limit

#### signals_log
- coin, type(spot/futures), signal_text, target_group, created_at

#### analysis_cache
- coin (Unique)
- rsi, macd, ema20, ema50, volume, breakout, updated_at

**نکته مهم باگ**: برای UPSERT باید روی `analysis_cache.coin` کلید UNIQUE باشد.

---

## 4) جریان‌های اصلی (Core Flows)

### 4.1 Onboarding
- کاربر /start → اگر وجود ندارد insert می‌شود
- پاسخ: نقش + تاریخ انقضا + (اگر Free) سهمیه امروز

### 4.2 Menu / Profile
- /menu → منوی دکمه‌ای
- /profile → نمایش اطلاعات

### 4.3 Admin
- فقط telegram_id های داخل ADMINS مجازند
- /admin → منو
- add_user: ورودی `telegram_id role days`
- remove_user: ورودی `telegram_id`
- broadcast: متن پیام
- logs: 10 لاگ آخر

### 4.4 Signal Cycle (Spot)
- هر N ثانیه (default: 3600) برای لیست کوین‌ها:
  - get_candles از MEXC
  - محاسبه اندیکاتورها
  - ذخیره cache
  - ساخت پیام
  - ارسال به نقش‌های مجاز

### 4.5 Futures Breakout (Extreme)
- هر 30 ثانیه:
  - تایم‌فریم 1m
  - Breakout ساده: last_close > max(prev_high over lookback)
  - ارسال فقط برای Extreme
  - anti-duplicate برای جلوگیری از اسپم

### 4.6 Reset Daily Limit
- هر روز نیمه‌شب timezone سرور:
  - daily_free_limit برای Free ها به مقدار DEFAULT_FREE_LIMIT برگردد

---

## 5) Security / Ops

- BOT_TOKEN، DB_PASSWORD، ADMINS باید از ENV/Secret management بیاید (در مونولیت هم پشتیبانی شده)
- برای production پیشنهاد:
  - محدود کردن دسترسی DB
  - لاگ‌های حساس را ماسک کردن
  - Rate limit Telegram + MEXC
  - docker-compose شامل شبکه داخلی

---

## 6) Acceptance Criteria

- با تنظیم ENV ها، اجرای `python 02_monolith_crypto_signal_bot.py`:
  - Bot بالا بیاید و /start کار کند
  - اتصال DB برقرار شود و schema ساخته شود
  - Background tasks شروع شوند
  - /admin فقط برای ADMINS جواب دهد
  - ارسال سیگنال‌ها در بازه تنظیم‌شده انجام شود (قابل مشاهده در لاگ و signals_log)

---

## 7) پارامترهای قابل تنظیم (ENV)

- BOT_TOKEN
- DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
- TIMEFRAME (default 1h)
- SPOT_CYCLE_SECONDS (default 3600)
- FUTURES_BREAKOUT_SECONDS (default 30)
- DEFAULT_FREE_LIMIT (default 2)
- ADMINS (comma-separated telegram_id ها)
- COINS_LIST (comma-separated مثل BTC_USDT,ETH_USDT)

---

## 8) نکات تکمیلی برای ایجنت
- کد مونولیت عمدی است تا ایجنت بتواند سریع refactor کند.
- ایجنت باید آن را به ماژول‌های تمیز تبدیل کند و باگ‌ها/لبه‌ها را کامل پوشش دهد.
