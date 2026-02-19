# Architecture

## High-Level Architecture
The system is composed of a Telegram bot, background workers, a database, and optional external integrations. The bot interacts with users and admins, while background tasks continuously analyze markets and send signals.

## Component Responsibilities
- `app/main.py`: Bootstraps configuration, DB, HTTP clients, and task scheduling.
- `app/db/database.py`: Schema management, queries, and runtime settings.
- `app/services/mexc_api.py`: MEXC market data client with retries and throttling.
- `app/services/analysis.py`: Indicator calculations and breakout detection.
- `app/services/signal_sender.py`: Telegram message delivery with throttling and safeguards.
- `app/services/spot_cycle.py`: Periodic spot signal generation.
- `app/services/futures_breakout.py`: Futures breakout detection loop.
- `app/services/optional_bridge.py`: Optional webhook sender and receiver.
- `app/handlers/*`: User and admin commands with FSM.

## Data Flow (Overview)
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

## Background Tasks
- Spot cycle: fetches candles, computes indicators, stores cache, sends signals.
- Futures breakout: checks 1m candles and alerts Extreme users.
- Daily reset: resets Free limits at midnight server time.

## Database Schema (Summary)
- `users`: Telegram ID, role, expiry, daily limits.
- `signals_log`: history of signals sent and targets.
- `analysis_cache`: last computed indicators per coin.
- `settings`: runtime configurable values (default Free limit).
- `schema_version`: schema tracking.

## Sequence Diagram: Spot Signal Flow
```
User -> Bot: /start
Bot -> Database: insert user if missing

Scheduler -> SpotCycle: tick
SpotCycle -> MEXC: get candles
SpotCycle -> Analysis: compute indicators
SpotCycle -> Database: upsert cache
SpotCycle -> SignalSender: send to roles
SignalSender -> Telegram: deliver messages
SignalSender -> Database: log signal
```

## Sequence Diagram: Futures Breakout Flow
```
Scheduler -> BreakoutWatcher: tick
BreakoutWatcher -> MEXC: get 1m candles
BreakoutWatcher -> Analysis: check breakout
BreakoutWatcher -> SignalSender: send to Extreme
SignalSender -> Telegram: deliver messages
SignalSender -> Database: log signal
```
