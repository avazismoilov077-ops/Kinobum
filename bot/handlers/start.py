from aiogram import Router, Bot, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from config import ADMIN_IDS
from database import User
from services import UserService, ChannelService
from keyboards import main_menu_kb, admin_menu_kb, subscription_check_kb
from utils.logger import logger

router = Router()


async def check_subscriptions(bot: Bot, user_id: int, session: AsyncSession) -> tuple[bool, list[dict]]:
    """Foydalanuvchi barcha kanallarga obuna bo'lganini tekshirish (DB dan)"""
    channels = await ChannelService.get_all_active(session)
    if not channels:
        return True, []

    not_subscribed = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch.channel_id, user_id)
            if member.status in ("left", "kicked", "banned"):
                link = ch.invite_link or f"https://t.me/{ch.channel_id.lstrip('@')}"
                not_subscribed.append({"title": ch.title or ch.channel_id, "url": link})
        except Exception as e:
            logger.warning(f"Kanal tekshirishda xato ({ch.channel_id}): {e}")

    return len(not_subscribed) == 0, not_subscribed


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, bot: Bot):
    user = message.from_user
    await UserService.get_or_create(
        session,
        telegram_id=user.id,
        username=user.username,
        full_name=user.full_name,
    )

    # Obuna tekshirish
    is_subscribed, channels = await check_subscriptions(bot, user.id, session)

    if not is_subscribed:
        await message.answer(
            "👋 Xush kelibsiz!\n\n"
            "⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
            reply_markup=subscription_check_kb(channels)
        )
        return

    is_admin = user.id in ADMIN_IDS
    kb = admin_menu_kb() if is_admin else main_menu_kb()

    await message.answer(
        f"👋 Salom, <b>{user.full_name}</b>!\n\n"
        "🎬 <b>Kino Botga xush kelibsiz!</b>\n\n"
        "Kino kodini yuboring yoki menyu orqali tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "check_subscription")
async def check_sub_callback(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    user = callback.from_user
    is_subscribed, channels = await check_subscriptions(bot, user.id, session)

    if not is_subscribed:
        await callback.answer("❌ Siz hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=subscription_check_kb(channels))
        return

    await UserService.get_or_create(session, telegram_id=user.id,
                                    username=user.username, full_name=user.full_name)

    is_admin = user.id in ADMIN_IDS
    kb = admin_menu_kb() if is_admin else main_menu_kb()

    await callback.message.delete()
    await callback.message.answer(
        f"✅ Obuna tasdiqlandi!\n\n"
        f"👋 Salom, <b>{user.full_name}</b>!\n"
        "🎬 <b>Kino Botga xush kelibsiz!</b>\n\n"
        "Kino kodini yuboring yoki menyu orqali tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    is_admin = callback.from_user.id in ADMIN_IDS
    kb = admin_menu_kb() if is_admin else main_menu_kb()
    await callback.message.delete()
    await callback.message.answer(
        "🏠 Asosiy menyu:",
        reply_markup=kb
    )
