from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.config import Config
from app.db.database import Database

router = Router()


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Profile", callback_data="profile")],
            [InlineKeyboardButton(text="Signals", callback_data="signals")],
            [InlineKeyboardButton(text="Help", callback_data="help")],
        ]
    )


def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Back to menu", callback_data="menu")]]
    )


@router.message(Command("start"))
async def start_cmd(message: Message, db: Database, config: Config) -> None:
    """Register user if needed and show access level."""
    await db.add_user_if_not_exists(message.from_user.id, message.from_user.username)
    user = await db.get_user(message.from_user.id) or {}
    role = user.get("role", "free")
    expire = user.get("expire_at")

    extra = ""
    if role == "free":
        extra = (
            f"\nDaily remaining signals: {user.get('daily_free_limit', config.default_free_limit)}"
        )

    full_name = html.escape(message.from_user.full_name or "User")
    expire_text = expire if expire else "No expiry"
    await message.answer(
        "Hello {name}!\n"
        "Access level: <b>{role}</b>\n"
        "Expire at: {expire}{extra}".format(
            name=full_name,
            role=role.upper(),
            expire=expire_text,
            extra=extra,
        )
    )


@router.message(Command("menu"))
async def menu_cmd(message: Message) -> None:
    await message.answer("Main menu", reply_markup=main_menu_kb())


@router.message(Command("profile"))
async def profile_cmd(message: Message, db: Database, config: Config) -> None:
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("You are not registered yet. Send /start first.")
        return

    extra = ""
    if user["role"] == "free":
        extra = f"\nDaily remaining signals: {user['daily_free_limit']}"

    expire_text = user["expire_at"] if user["expire_at"] else "No expiry"
    txt = (
        "Profile\n"
        f"Access level: <b>{user['role'].upper()}</b>\n"
        f"Expire at: {expire_text}{extra}"
    )
    await message.answer(txt, reply_markup=back_to_menu_kb())


@router.callback_query(F.data.in_({"menu", "profile", "signals", "help"}))
async def menu_callbacks(callback: CallbackQuery, db: Database, config: Config) -> None:
    if callback.data == "menu":
        await callback.message.answer("Main menu", reply_markup=main_menu_kb())
    elif callback.data == "profile":
        await profile_cmd(callback.message, db, config)
    elif callback.data == "signals":
        await callback.message.answer("Signals are sent on schedule.")
    elif callback.data == "help":
        await callback.message.answer("Commands: /start /menu /profile /admin /reload_coins")
    await callback.answer()
