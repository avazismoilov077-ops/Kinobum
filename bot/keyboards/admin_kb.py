from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def admin_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="➕ Kino qo'shish"),
        KeyboardButton(text="❌ Kino o'chirish"),
    )
    builder.row(
        KeyboardButton(text="📊 Statistika"),
        KeyboardButton(text="📨 Barchaga xabar"),
    )
    builder.row(
        KeyboardButton(text="👑 Admin boshqaruvi"),
        KeyboardButton(text="🔑 Majburiy obuna"),
    )
    builder.row(
        KeyboardButton(text="📢 Reklama boshqaruvi"),
        KeyboardButton(text="🎬 Kodlar boshqaruvi"),
    )
    builder.row(KeyboardButton(text="🏠 Foydalanuvchi menyusi"))
    return builder.as_markup(resize_keyboard=True)


def admin_movie_manage_kb(movie_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔑 Kod qo'shish", callback_data=f"add_code:{movie_id}"),
        InlineKeyboardButton(text="📋 Kodlar ro'yxati", callback_data=f"list_codes:{movie_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="❌ Kinoni o'chirish", callback_data=f"delete_movie:{movie_id}")
    )
    return builder.as_markup()


def admin_codes_kb(movie_id: int, codes: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code in codes:
        builder.row(
            InlineKeyboardButton(
                text=f"🗑 {code.code}",
                callback_data=f"del_code:{code.id}"
            )
        )
    builder.row(
        InlineKeyboardButton(text="➕ Yangi kod", callback_data=f"add_code:{movie_id}"),
        InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"movie_manage:{movie_id}"),
    )
    return builder.as_markup()


def admin_channels_kb(channels: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, ch in enumerate(channels):
        builder.row(
            InlineKeyboardButton(text=f"❌ {ch}", callback_data=f"remove_channel:{i}")
        )
    builder.row(
        InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="add_channel")
    )
    return builder.as_markup()


def confirm_kb(action: str, item_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha", callback_data=f"confirm:{action}:{item_id}"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data="cancel_action"),
        ]
    ])


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")]
    ])


def ad_manage_kb(ads: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ad in ads:
        status = "✅" if ad.is_active else "❌"
        builder.row(
            InlineKeyboardButton(
                text=f"{status} Reklama #{ad.id}",
                callback_data=f"toggle_ad:{ad.id}"
            ),
            InlineKeyboardButton(text="🗑", callback_data=f"delete_ad:{ad.id}")
        )
    builder.row(
        InlineKeyboardButton(text="➕ Yangi reklama", callback_data="add_ad")
    )
    return builder.as_markup()
