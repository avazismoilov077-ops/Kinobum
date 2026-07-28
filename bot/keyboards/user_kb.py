from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def main_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🎬 Kino qidirish"),
        KeyboardButton(text="🆕 Yangi kinolar"),
    )
    builder.row(
        KeyboardButton(text="🔥 Eng mashhur kinolar"),
        KeyboardButton(text="🎭 Janrlar"),
    )
    builder.row(
        KeyboardButton(text="📜 Ko'rilganlar tarixi"),
        KeyboardButton(text="ℹ️ Bot haqida"),
    )
    return builder.as_markup(resize_keyboard=True)


def subscription_check_kb(channels: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ch in channels:
        builder.row(
            InlineKeyboardButton(
                text=f"📢 {ch['title']}",
                url=ch["url"]
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="✅ Obuna bo'ldim, tekshirish",
            callback_data="check_subscription"
        )
    )
    return builder.as_markup()


def genres_kb(genres: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for genre in genres:
        builder.button(text=genre, callback_data=f"genre:{genre}")
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_main")
    )
    return builder.as_markup()


def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_main")]
    ])


def movie_detail_kb(movie_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Ko'rish", callback_data=f"watch:{movie_id}")]
    ])
