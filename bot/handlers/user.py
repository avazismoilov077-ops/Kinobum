from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from config import ADMIN_IDS, BACKUP_CHANNEL_ID, AD_INTERVAL
from database.models import User
from services import MovieService, UserService, AdService
from keyboards import main_menu_kb, genres_kb, back_kb
from utils.logger import logger

router = Router()


async def send_movie(bot: Bot, chat_id: int, movie, session: AsyncSession):
    """Kinoni foydalanuvchiga yuborish"""
    caption = (
        f"🎬 <b>{movie.title}</b>\n\n"
        f"🎭 Janr: {movie.genre or 'Noma`lum'}\n\n"
        f"📝 {movie.description or ''}\n\n"
        f"👁 Ko'rishlar: {movie.views}"
    )

    try:
        if movie.backup_message_id:
            # Backup kanaldan nusxa olish
            await bot.copy_message(
                chat_id=chat_id,
                from_chat_id=BACKUP_CHANNEL_ID,
                message_id=movie.backup_message_id,
                caption=caption,
                parse_mode="HTML"
            )
        elif movie.video_file_id:
            if movie.poster_file_id:
                await bot.send_photo(chat_id, movie.poster_file_id, caption=caption, parse_mode="HTML")
            await bot.send_video(chat_id, movie.video_file_id)
        else:
            await bot.send_message(chat_id, caption, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Video yuborishda xato: {e}")
        await bot.send_message(chat_id, caption, parse_mode="HTML")


async def maybe_send_ad(bot: Bot, chat_id: int, user: User, session: AsyncSession):
    """Reklama yuborish (har AD_INTERVAL qidiruvdan keyin)"""
    try:
        if user.search_count % AD_INTERVAL == 0 and user.search_count > 0:
            ad = await AdService.get_active(session)
            if ad:
                kb = None
                if ad.button_text and ad.button_url:
                    kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text=ad.button_text, url=ad.button_url)]
                    ])
                if ad.photo_file_id:
                    await bot.send_photo(chat_id, ad.photo_file_id, caption=ad.text or "", reply_markup=kb)
                elif ad.video_file_id:
                    await bot.send_video(chat_id, ad.video_file_id, caption=ad.text or "", reply_markup=kb)
                elif ad.text:
                    await bot.send_message(chat_id, ad.text, reply_markup=kb)
    except Exception as e:
        logger.warning(f"Reklama yuborishda xato: {e}")


@router.message(F.text == "🎬 Kino qidirish")
async def movie_search_prompt(message: Message):
    await message.answer(
        "🔍 Kino nomini yoki kodini yuboring:",
        reply_markup=back_kb()
    )


@router.message(F.text == "🆕 Yangi kinolar")
async def new_movies(message: Message, session: AsyncSession):
    movies = await MovieService.get_latest(session, limit=10)
    if not movies:
        await message.answer("😔 Hozircha yangi kinolar yo'q.")
        return
    text = "🆕 <b>Yangi kinolar:</b>\n\n"
    for i, m in enumerate(movies, 1):
        text += f"{i}. 🎬 <b>{m.title}</b> | 👁 {m.views}\n"
    text += "\n<i>Kod yuboring yoki kino nomini yozing</i>"
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "🔥 Eng mashhur kinolar")
async def popular_movies(message: Message, session: AsyncSession):
    movies = await MovieService.get_popular(session, limit=10)
    if not movies:
        await message.answer("😔 Hozircha kinolar yo'q.")
        return
    text = "🔥 <b>Eng mashhur kinolar:</b>\n\n"
    for i, m in enumerate(movies, 1):
        text += f"{i}. 🎬 <b>{m.title}</b> | 👁 {m.views}\n"
    text += "\n<i>Kino kodini yuboring</i>"
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "🎭 Janrlar")
async def genres_list(message: Message, session: AsyncSession):
    genres = await MovieService.get_all_genres(session)
    if not genres:
        await message.answer("😔 Hozircha janrlar yo'q.")
        return
    await message.answer("🎭 Janrni tanlang:", reply_markup=genres_kb(genres))


@router.callback_query(F.data.startswith("genre:"))
async def genre_movies(callback: CallbackQuery, session: AsyncSession):
    genre = callback.data.split(":", 1)[1]
    movies = await MovieService.get_by_genre(session, genre)
    if not movies:
        await callback.answer("😔 Bu janrda kinolar yo'q.", show_alert=True)
        return
    text = f"🎭 <b>{genre}</b> janridagi kinolar:\n\n"
    for i, m in enumerate(movies, 1):
        text += f"{i}. 🎬 {m.title} | 👁 {m.views}\n"
    text += "\n<i>Kino kodini yuboring</i>"
    await callback.message.edit_text(text, reply_markup=back_kb(), parse_mode="HTML")


@router.message(F.text == "📜 Ko'rilganlar tarixi")
async def watch_history(message: Message, session: AsyncSession):
    history = await UserService.get_history(session, message.from_user.id)
    if not history:
        await message.answer("📜 Ko'rilganlar tarixi bo'sh.")
        return
    text = "📜 <b>Ko'rilganlar tarixi:</b>\n\n"
    for i, (h, m) in enumerate(history, 1):
        text += f"{i}. 🎬 {m.title}\n"
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "ℹ️ Bot haqida")
async def about_bot(message: Message):
    await message.answer(
        "ℹ️ <b>Kino Bot</b>\n\n"
        "🎬 Bu bot orqali siz kino kodini yuborib kinolarni ko'rishingiz mumkin.\n\n"
        "📌 <b>Qanday foydalanish:</b>\n"
        "1. Kino kodini yozing\n"
        "2. Yoki kino nomini qidiring\n"
        "3. Enjoy! 🍿\n\n"
        "🤖 Bot 24/7 ishlaydi",
        parse_mode="HTML"
    )


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: Message, session: AsyncSession, bot: Bot):
    """Kino kodi yoki nomi bo'yicha qidirish"""
    if message.from_user.id in ADMIN_IDS:
        return

    query = message.text.strip()
    user_db = await UserService.get_or_create(session, message.from_user.id,
                                              message.from_user.username,
                                              message.from_user.full_name)

    # Avval kod bo'yicha qidirish
    movie = await MovieService.find_by_code(session, query)

    # Topilmasa nom bo'yicha
    if not movie:
        movies = await MovieService.search_by_title(session, query)
        if len(movies) == 1:
            movie = movies[0]
        elif len(movies) > 1:
            builder = InlineKeyboardBuilder()
            for m in movies:
                builder.row(InlineKeyboardButton(text=f"🎬 {m.title}", callback_data=f"watch:{m.id}"))
            await message.answer(
                f"🔍 <b>'{query}'</b> bo'yicha natijalar:",
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
            return

    if not movie:
        await message.answer(
            "❌ <b>Kino topilmadi.</b>\n\n"
            "Iltimos, kino kodini to'g'ri kiriting yoki boshqa nom bilan qidiring.",
            parse_mode="HTML"
        )
        return

    # Ko'rishlar va tarixni yangilash
    await MovieService.increment_views(session, movie.id)
    await UserService.increment_search(session, message.from_user.id)
    await UserService.add_to_history(session, user_db.id, movie.id)

    await send_movie(bot, message.chat.id, movie, session)

    # Reklama tekshirish
    await maybe_send_ad(bot, message.chat.id, user_db, session)


@router.callback_query(F.data.startswith("watch:"))
async def watch_movie(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    movie_id = int(callback.data.split(":")[1])
    movie = await MovieService.get_by_id(session, movie_id)
    if not movie:
        await callback.answer("❌ Kino topilmadi!", show_alert=True)
        return

    user_db = await UserService.get_or_create(session, callback.from_user.id,
                                              callback.from_user.username,
                                              callback.from_user.full_name)

    await MovieService.increment_views(session, movie_id)
    await UserService.increment_search(session, callback.from_user.id)
    await UserService.add_to_history(session, user_db.id, movie_id)

    await callback.answer()
    await send_movie(bot, callback.message.chat.id, movie, session)
