from aiogram import Router, Bot, F
from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from config import ADMIN_IDS, BACKUP_CHANNEL_ID
from services import MovieService, UserService, AdService, ChannelService
from keyboards import (
    admin_menu_kb, main_menu_kb, admin_movie_manage_kb,
    admin_codes_kb, admin_channels_kb, confirm_kb, cancel_kb, ad_manage_kb
)
from states import AddMovieStates, AddAdStates, AddChannelStates

from utils.logger import logger

router = Router()


class IsAdmin(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ADMIN_IDS


# ─── Admin panel ───────────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "🏠 Foydalanuvchi menyusi")
async def to_user_menu(message: Message):
    await message.answer("🏠 Foydalanuvchi menyusi:", reply_markup=main_menu_kb())


@router.message(IsAdmin(), F.text == "📊 Statistika")
async def stats(message: Message, session: AsyncSession):
    user_stats = await UserService.get_stats(session)
    movie_stats = await MovieService.get_stats(session)

    top_text = ""
    for i, m in enumerate(movie_stats["top_movies"], 1):
        top_text += f"  {i}. {m.title} — {m.views} ko'rish\n"

    await message.answer(
        "📊 <b>Statistika</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{user_stats['total']}</b>\n"
        f"📅 Bugungi yangilar: <b>{user_stats['today']}</b>\n\n"
        f"🎬 Jami kinolar: <b>{movie_stats['total_movies']}</b>\n"
        f"🔑 Jami kodlar: <b>{movie_stats['total_codes']}</b>\n\n"
        f"🔥 <b>Top 5 kino:</b>\n{top_text or '  Hali yoq'}",
        parse_mode="HTML"
    )


# ─── Kino qo'shish ─────────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "➕ Kino qo'shish")
async def add_movie_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AddMovieStates.title)
    await message.answer("🎬 Kino nomini kiriting:", reply_markup=cancel_kb())


@router.message(AddMovieStates.title)
async def add_movie_title(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.update_data(title=message.text.strip())
    await state.set_state(AddMovieStates.genre)
    await message.answer("🎭 Janrini kiriting (masalan: Drama, Komediya, Triller):")


@router.message(AddMovieStates.genre)
async def add_movie_genre(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.update_data(genre=message.text.strip())
    await state.set_state(AddMovieStates.description)
    await message.answer("📝 Tavsifini kiriting:")


@router.message(AddMovieStates.description)
async def add_movie_description(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.update_data(description=message.text.strip())
    await state.set_state(AddMovieStates.poster)
    await message.answer("🖼 Posterni yuboring (ixtiyoriy, o'tkazib yuborish uchun /skip yozing):")


@router.message(AddMovieStates.poster)
async def add_movie_poster(message: Message, state: FSMContext, bot: Bot):
    if message.from_user.id not in ADMIN_IDS:
        return
    poster_id = None
    if message.photo:
        poster_id = message.photo[-1].file_id
    elif message.text != "/skip":
        await message.answer("⚠️ Rasm yuboring yoki /skip yozing:")
        return

    await state.update_data(poster_file_id=poster_id)
    await state.set_state(AddMovieStates.video)
    await message.answer("🎥 Videoni yuboring:")


@router.message(AddMovieStates.video)
async def add_movie_video(message: Message, state: FSMContext, bot: Bot, session: AsyncSession):
    if message.from_user.id not in ADMIN_IDS:
        return
    if not message.video:
        await message.answer("⚠️ Video yuboring!")
        return

    video_file_id = message.video.file_id
    data = await state.get_data()

    # Backup kanalga yuborish
    backup_msg_id = None
    try:
        sent = await bot.send_video(
            BACKUP_CHANNEL_ID,
            video_file_id,
            caption=f"🎬 {data['title']} | {data.get('genre', '')}"
        )
        backup_msg_id = sent.message_id
        logger.info(f"Backup yuborildi: message_id={backup_msg_id}")
    except Exception as e:
        logger.error(f"Backup kanalga yuborishda xato: {e}")
        await message.answer(f"⚠️ Backup kanalga yuborishda xato: {e}\nLekin kino saqlanadi.")

    movie = await MovieService.create(
        session,
        title=data["title"],
        genre=data["genre"],
        description=data["description"],
        poster_file_id=data.get("poster_file_id"),
        video_file_id=video_file_id,
        backup_message_id=backup_msg_id,
    )

    await state.set_state(AddMovieStates.add_code)
    await state.update_data(movie_id=movie.id)

    await message.answer(
        f"✅ <b>{movie.title}</b> qo'shildi! (ID: {movie.id})\n\n"
        "🔑 Endi kod kiriting (bir nechta bo'lsa bitta-bitta kiriting).\n"
        "Tugash uchun /done yozing:",
        reply_markup=cancel_kb(),
        parse_mode="HTML"
    )


@router.message(AddMovieStates.add_code)
async def add_movie_code_step(message: Message, state: FSMContext, session: AsyncSession):
    if message.from_user.id not in ADMIN_IDS:
        return
    if message.text == "/done":
        data = await state.get_data()
        movie_id = data.get("movie_id")
        codes = await MovieService.get_codes(session, movie_id)
        await state.clear()
        await message.answer(
            f"✅ Kino saqlandi!\n"
            f"🔑 Kodlar soni: {len(codes)}\n\n"
            f"Boshqarish uchun /movie_{movie_id}",
            reply_markup=admin_menu_kb()
        )
        return

    data = await state.get_data()
    movie_id = data.get("movie_id")
    code = message.text.strip()
    result = await MovieService.add_code(session, movie_id, code)
    if result:
        await message.answer(f"✅ Kod qo'shildi: <code>{code}</code>\n"
                             "Yana kod kiriting yoki /done yozing.", parse_mode="HTML")
    else:
        await message.answer(f"⚠️ <code>{code}</code> kodi allaqachon mavjud!", parse_mode="HTML")


# ─── Kino o'chirish ────────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "❌ Kino o'chirish")
async def delete_movie_prompt(message: Message):
    await message.answer("🎬 O'chirmoqchi bo'lgan kino ID sini kiriting:")


@router.callback_query(F.data.startswith("delete_movie:"))
async def confirm_delete_movie(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    movie_id = int(callback.data.split(":")[1])
    await callback.message.edit_reply_markup(reply_markup=confirm_kb("movie", movie_id))


@router.callback_query(F.data.startswith("confirm:movie:"))
async def do_delete_movie(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id not in ADMIN_IDS:
        return
    movie_id = int(callback.data.split(":")[2])
    success = await MovieService.delete(session, movie_id)
    await callback.answer("✅ Kino o'chirildi!" if success else "❌ Kino topilmadi!", show_alert=True)
    await callback.message.delete()


# ─── Kodlar boshqaruvi ─────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "🎬 Kodlar boshqaruvi")
async def codes_manage_prompt(message: Message):
    await message.answer("🎬 Kino ID sini kiriting:")


@router.callback_query(F.data.startswith("movie_manage:"))
async def movie_manage(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id not in ADMIN_IDS:
        return
    movie_id = int(callback.data.split(":")[1])
    movie = await MovieService.get_by_id(session, movie_id)
    if not movie:
        await callback.answer("❌ Kino topilmadi!", show_alert=True)
        return
    await callback.message.edit_text(
        f"🎬 <b>{movie.title}</b>\nID: {movie.id}",
        reply_markup=admin_movie_manage_kb(movie_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("list_codes:"))
async def list_codes(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id not in ADMIN_IDS:
        return
    movie_id = int(callback.data.split(":")[1])
    codes = await MovieService.get_codes(session, movie_id)
    if not codes:
        await callback.answer("🔑 Kodlar yo'q.", show_alert=True)
        return
    await callback.message.edit_text(
        f"🔑 Kodlar ({len(codes)} ta) — o'chirish uchun bosing:",
        reply_markup=admin_codes_kb(movie_id, codes)
    )


@router.callback_query(F.data.startswith("del_code:"))
async def delete_code(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id not in ADMIN_IDS:
        return
    code_id = int(callback.data.split(":")[1])
    await MovieService.delete_code(session, code_id)
    await callback.answer("✅ Kod o'chirildi!")
    await callback.message.delete()


# ─── Majburiy obuna ────────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "🔑 Majburiy obuna")
async def subscription_manage(message: Message, session: AsyncSession):
    channels = await ChannelService.get_all(session)
    text = "🔑 <b>Majburiy obuna kanallari:</b>\n\n"
    if channels:
        for ch in channels:
            status = "✅ Faol" if ch.is_active else "❌ Nofaol"
            text += f"• {ch.title or ch.channel_id} — {status}\n"
    else:
        text += "<i>Hozircha kanallar yo'q</i>\n"
    text += "\nKanal qo'shish/o'chirish:"
    await message.answer(text, reply_markup=admin_channels_kb(channels), parse_mode="HTML")


@router.callback_query(F.data == "add_channel")
async def add_channel_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await state.set_state(AddChannelStates.channel_id)
    await callback.message.answer(
        "📢 Kanal username yoki ID sini yuboring:\n\n"
        "<b>Namuna:</b> <code>@kanalim</code> yoki <code>-1001234567890</code>\n\n"
        "⚠️ Bot kanalning admini bo'lishi kerak!",
        reply_markup=cancel_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddChannelStates.channel_id)
async def add_channel_finish(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    if message.from_user.id not in ADMIN_IDS:
        return

    channel_input = message.text.strip()

    # Kanal ma'lumotlarini olish
    try:
        chat = await bot.get_chat(channel_input)
        channel_id = str(chat.id) if str(chat.id).startswith("-") else f"@{chat.username}" if chat.username else str(chat.id)
        title = chat.title or channel_input
        invite_link = chat.invite_link or (f"https://t.me/{chat.username}" if chat.username else None)

        ch = await ChannelService.add(session, channel_id=channel_id, title=title, invite_link=invite_link)
        await state.clear()
        await message.answer(
            f"✅ <b>{title}</b> kanali qo'shildi!\n"
            f"ID: <code>{channel_id}</code>",
            reply_markup=admin_menu_kb(),
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(
            f"❌ Kanal topilmadi: {e}\n\n"
            "Bot kanalning admini ekanligini tekshiring va qayta urinib ko'ring:",
        )


@router.callback_query(F.data.startswith("toggle_ch:"))
async def toggle_channel(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id not in ADMIN_IDS:
        return
    ch_id = int(callback.data.split(":")[1])
    ch = await ChannelService.toggle(session, ch_id)
    status = "faol" if ch and ch.is_active else "nofaol"
    await callback.answer(f"Kanal {status} qilindi!")
    channels = await ChannelService.get_all(session)
    await callback.message.edit_reply_markup(reply_markup=admin_channels_kb(channels))


@router.callback_query(F.data.startswith("del_ch:"))
async def delete_channel(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id not in ADMIN_IDS:
        return
    ch_id = int(callback.data.split(":")[1])
    await ChannelService.remove(session, ch_id)
    await callback.answer("✅ Kanal o'chirildi!")
    channels = await ChannelService.get_all(session)
    text = "🔑 <b>Majburiy obuna kanallari:</b>\n\n"
    if channels:
        for ch in channels:
            status = "✅ Faol" if ch.is_active else "❌ Nofaol"
            text += f"• {ch.title or ch.channel_id} — {status}\n"
    else:
        text += "<i>Hozircha kanallar yo'q</i>\n"
    text += "\nKanal qo'shish/o'chirish:"
    await callback.message.edit_text(text, reply_markup=admin_channels_kb(channels), parse_mode="HTML")


# ─── Reklama ───────────────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "📢 Reklama boshqaruvi")
async def ad_manage(message: Message, session: AsyncSession):
    ads = await AdService.get_all(session)
    if not ads:
        await message.answer(
            "📢 <b>Reklamalar</b>\n\nHozircha reklamalar yo'q.",
            reply_markup=ad_manage_kb([]),
            parse_mode="HTML"
        )
        return
    await message.answer(
        f"📢 <b>Reklamalar ({len(ads)} ta)</b>\n\n✅ — faol | ❌ — nofaol",
        reply_markup=ad_manage_kb(ads),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("toggle_ad:"))
async def toggle_ad(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id not in ADMIN_IDS:
        return
    ad_id = int(callback.data.split(":")[1])
    ad = await AdService.toggle(session, ad_id)
    status = "faol" if ad and ad.is_active else "nofaol"
    await callback.answer(f"Reklama {status} qilindi!")
    ads = await AdService.get_all(session)
    await callback.message.edit_reply_markup(reply_markup=ad_manage_kb(ads))


@router.callback_query(F.data.startswith("delete_ad:"))
async def delete_ad(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id not in ADMIN_IDS:
        return
    ad_id = int(callback.data.split(":")[1])
    await AdService.delete(session, ad_id)
    await callback.answer("✅ Reklama o'chirildi!")
    ads = await AdService.get_all(session)
    await callback.message.edit_reply_markup(reply_markup=ad_manage_kb(ads))


@router.callback_query(F.data == "add_ad")
async def add_ad_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await state.set_state(AddAdStates.content)
    await callback.message.answer(
        "📢 Reklama matnini, rasmini yoki videosini yuboring:",
        reply_markup=cancel_kb()
    )


@router.message(AddAdStates.content)
async def add_ad_content(message: Message, state: FSMContext, session: AsyncSession):
    if message.from_user.id not in ADMIN_IDS:
        return
    photo_id = message.photo[-1].file_id if message.photo else None
    video_id = message.video.file_id if message.video else None
    text = message.text or message.caption or ""

    ad = await AdService.create(session, text=text, photo_file_id=photo_id, video_file_id=video_id)
    await state.clear()
    await message.answer(
        f"✅ Reklama #{ad.id} qo'shildi!",
        reply_markup=admin_menu_kb()
    )


@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("❌ Bekor qilindi.", reply_markup=admin_menu_kb())
