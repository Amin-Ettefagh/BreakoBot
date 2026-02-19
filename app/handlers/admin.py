from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta
from typing import List, Tuple

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.config import Config, reload_coins
from app.db.database import Database
from app.services.signal_sender import SignalSender
from app.utils.validators import parse_coins_list, validate_role

router = Router()


class AdminStates(StatesGroup):
    waiting_add_user = State()
    waiting_remove_user = State()
    waiting_broadcast = State()
    waiting_set_limit = State()


def is_admin(user_id: int, config: Config) -> bool:
    return user_id in config.admins if config.admins else False


def admin_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Add/Update subscription", callback_data="admin:add_user")],
            [InlineKeyboardButton(text="Deactivate user", callback_data="admin:remove_user")],
            [InlineKeyboardButton(text="Broadcast", callback_data="admin:broadcast")],
            [InlineKeyboardButton(text="Stats", callback_data="admin:stats")],
            [InlineKeyboardButton(text="Export logs", callback_data="admin:export_logs")],
            [InlineKeyboardButton(text="Set free limit", callback_data="admin:set_limit")],
            [InlineKeyboardButton(text="View logs", callback_data="admin:logs")],
            [InlineKeyboardButton(text="Reload coins", callback_data="admin:reload_coins")],
        ]
    )


@router.message(Command("admin"))
async def admin_cmd(message: Message, config: Config) -> None:
    if not is_admin(message.from_user.id, config):
        await message.answer("You are not an admin.")
        return
    await message.answer("Admin panel", reply_markup=admin_panel_kb())


@router.message(Command("admin_stats"))
async def admin_stats_cmd(message: Message, db: Database, config: Config) -> None:
    if not is_admin(message.from_user.id, config):
        await message.answer("You are not an admin.")
        return
    text = await _build_stats_text(db)
    await message.answer(text)


@router.message(Command("export_logs"))
async def export_logs_cmd(message: Message, db: Database, config: Config) -> None:
    if not is_admin(message.from_user.id, config):
        await message.answer("You are not an admin.")
        return
    await _send_logs_csv(message, db)


@router.message(Command("set_limit"))
async def set_limit_cmd(message: Message, state: FSMContext, config: Config) -> None:
    if not is_admin(message.from_user.id, config):
        await message.answer("You are not an admin.")
        return
    await message.answer("Send new free limit (integer):")
    await state.set_state(AdminStates.waiting_set_limit)


@router.message(Command("reload_coins"))
async def reload_coins_cmd(message: Message, config: Config) -> None:
    if not is_admin(message.from_user.id, config):
        await message.answer("You are not an admin.")
        return

    raw = message.text.replace("/reload_coins", "", 1).strip()
    try:
        if raw:
            coins = parse_coins_list(raw)
            config.coins_list = coins
        else:
            coins = reload_coins(config)
        await message.answer(f"Coins reloaded: {', '.join(coins)}")
    except Exception as exc:
        await message.answer(f"Reload failed: {exc}")


@router.callback_query(F.data.startswith("admin:"))
async def admin_callbacks(
    callback: CallbackQuery, state: FSMContext, db: Database, config: Config
) -> None:
    if not is_admin(callback.from_user.id, config):
        await callback.answer("You are not an admin.", show_alert=True)
        return

    action = callback.data.split("admin:", 1)[1]
    if action == "add_user":
        await callback.message.answer("Send: telegram_id role days\nExample: 123456789 vip 30")
        await state.set_state(AdminStates.waiting_add_user)
    elif action == "remove_user":
        await callback.message.answer("Send telegram_id to deactivate.")
        await state.set_state(AdminStates.waiting_remove_user)
    elif action == "broadcast":
        await callback.message.answer("Send broadcast message text:")
        await state.set_state(AdminStates.waiting_broadcast)
    elif action == "logs":
        logs = await db.get_last_logs(10)
        if not logs:
            await callback.message.answer("No logs yet.")
        else:
            text = "Last 10 signals:\n"
            for coin, typ, grp, created in logs:
                text += f"{created} | {coin} | {typ} | {grp}\n"
            await callback.message.answer(text)
    elif action == "reload_coins":
        try:
            coins = reload_coins(config)
            await callback.message.answer(f"Coins reloaded: {', '.join(coins)}")
        except Exception as exc:
            await callback.message.answer(f"Reload failed: {exc}")
    elif action == "stats":
        text = await _build_stats_text(db)
        await callback.message.answer(text)
    elif action == "export_logs":
        await _send_logs_csv(callback.message, db)
    elif action == "set_limit":
        await callback.message.answer("Send new free limit (integer):")
        await state.set_state(AdminStates.waiting_set_limit)

    await callback.answer()


@router.message(AdminStates.waiting_add_user)
async def admin_add_user(
    message: Message, state: FSMContext, db: Database, config: Config
) -> None:
    try:
        if not is_admin(message.from_user.id, config):
            raise PermissionError("Not an admin")
        parts = message.text.strip().split()
        if len(parts) != 3:
            raise ValueError("Format: telegram_id role days")

        telegram_id = int(parts[0])
        role = validate_role(parts[1])
        days = int(parts[2])
        expire = None if days <= 0 else (datetime.now() + timedelta(days=days))

        await db.add_user_if_not_exists(telegram_id, None)
        await db.set_role(telegram_id, role, expire)
        await message.answer(
            f"User {telegram_id} updated: role={role} expire={expire if expire else 'NULL'}"
        )
    except Exception as exc:
        await message.answer(f"Error: {exc}")
    finally:
        await state.clear()


@router.message(AdminStates.waiting_remove_user)
async def admin_remove_user(
    message: Message, state: FSMContext, db: Database, config: Config
) -> None:
    try:
        if not is_admin(message.from_user.id, config):
            raise PermissionError("Not an admin")
        telegram_id = int(message.text.strip())
        await db.deactivate_user(telegram_id)
        await message.answer(f"User {telegram_id} deactivated.")
    except Exception as exc:
        await message.answer(f"Error: {exc}")
    finally:
        await state.clear()


@router.message(AdminStates.waiting_broadcast)
async def admin_broadcast(
    message: Message, state: FSMContext, sender: SignalSender, config: Config
) -> None:
    try:
        if not is_admin(message.from_user.id, config):
            raise PermissionError("Not an admin")
        text = message.text.strip()
        if not text:
            raise ValueError("Message is empty")
        sent = await sender.broadcast(text)
        await message.answer(f"Broadcast delivered to {sent} users.")
    except Exception as exc:
        await message.answer(f"Error: {exc}")
    finally:
        await state.clear()


@router.message(AdminStates.waiting_set_limit)
async def admin_set_limit(
    message: Message, state: FSMContext, db: Database, config: Config
) -> None:
    try:
        if not is_admin(message.from_user.id, config):
            raise PermissionError("Not an admin")
        value = int(message.text.strip())
        if value < 0:
            raise ValueError("Limit must be >= 0")
        await db.set_default_free_limit(value)
        await db.reset_daily_limits()
        config.default_free_limit = value
        await message.answer(f"Default free limit set to {value} and applied to free users.")
    except Exception as exc:
        await message.answer(f"Error: {exc}")
    finally:
        await state.clear()


async def _build_stats_text(db: Database) -> str:
    roles = await db.count_users_by_role()
    signals_24h = await db.count_signals_last_24h()
    top_coins = await db.top_coins_by_signals()
    expired = await db.fetch_expired_users()

    role_lines = [f"{role}: {count}" for role, count in roles]
    top_lines = [f"{coin}: {count}" for coin, count in top_coins]

    text = "Admin Stats\n"
    text += "Users by role:\n" + ("\n".join(role_lines) if role_lines else "No users") + "\n\n"
    text += f"Expired users: {len(expired)}\n\n"
    text += f"Signals sent (last 24h): {signals_24h}\n\n"
    text += "Top coins (last 24h):\n" + ("\n".join(top_lines) if top_lines else "No signals")
    return text


async def _send_logs_csv(message: Message, db: Database, limit: int = 500) -> None:
    rows = await db.export_signals_log(limit)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["coin", "type", "target_group", "created_at", "signal_text"])
    for coin, typ, grp, created_at, signal_text in rows:
        writer.writerow([coin, typ, grp, created_at, signal_text])

    data = buffer.getvalue().encode("utf-8")
    filename = f"signals_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    await message.answer_document(BufferedInputFile(data, filename=filename))
