from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import ADMIN_IDS
from services import MovieService
from keyboards import admin_menu_kb, admin_movie_manage_kb, cancel_kb
from states import AddCodeStates
from utils.logger import logger

router = Router()


@router.message(F.text.regexp(r"^/movie_(\d+)$"))
async def movie_manage_by_id(message: Message, session: AsyncSession):
    if message.from_user.id not in ADMIN_IDS:
        return
    movie_id = int(message.text.split("_")[1])
    movie = await MovieService.get_by_id(session, movie_id)
    if not movie:
        await message.answer("❌ Kino topilmadi!")
        return
    codes = await MovieService.get_codes(session, movie_id)
    code_list = "\n".join([f"• <code>{c.code}</code>" for c in codes]) or "<i>Kodlar yo'q</i>"
    await message.answer(
        f"🎬 <b>{movie.title}</b>\n"
        f"ID: {movie_id}\n"
        f"👁 Ko'rishlar: {movie.views}\n\n"
        f"🔑 Kodlar:\n{code_list}",
        reply_markup=admin_movie_manage_kb(movie_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("add_code:"))
async def add_code_start(callback, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    movie_id = int(callback.data.split(":")[1])
    await state.set_state(AddCodeStates.code)
    await state.update_data(movie_id=movie_id)
    await callback.message.answer("🔑 Yangi kodni kiriting:", reply_markup=cancel_kb())
    await callback.answer()


@router.message(AddCodeStates.code)
async def add_code_finish(message: Message, state: FSMContext, session: AsyncSession):
    if message.from_user.id not in ADMIN_IDS:
        return
    data = await state.get_data()
    movie_id = data.get("movie_id")
    code = message.text.strip()
    result = await MovieService.add_code(session, movie_id, code)
    if result:
        await message.answer(
            f"✅ Kod qo'shildi: <code>{code}</code>",
            reply_markup=admin_menu_kb(),
            parse_mode="HTML"
        )
    else:
        await message.answer(f"⚠️ <code>{code}</code> allaqachon mavjud!", parse_mode="HTML")
    await state.clear()
