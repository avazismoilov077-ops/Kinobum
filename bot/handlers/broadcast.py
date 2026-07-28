import asyncio
from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from config import ADMIN_IDS
from services import UserService
from keyboards import admin_menu_kb, confirm_kb, cancel_kb
from states import BroadcastStates
from database.models import BroadcastLog
from utils.logger import logger

router = Router()


@router.message(F.text == "📨 Barchaga xabar")
async def broadcast_start(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.set_state(BroadcastStates.message)
    await message.answer(
        "📨 Yubormoqchi bo'lgan xabarni yuboring:\n"
        "(matn, rasm, video yoki forward)",
        reply_markup=cancel_kb()
    )


@router.message(BroadcastStates.message)
async def broadcast_confirm(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.update_data(message_id=message.message_id, chat_id=message.chat.id)
    await state.set_state(BroadcastStates.confirm)

    await message.answer(
        "✅ Yuqoridagi xabar barchaga yuborilsinmi?",
        reply_markup=confirm_kb("broadcast", 0)
    )


@router.callback_query(F.data == "confirm:broadcast:0")
async def do_broadcast(callback: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    if callback.from_user.id not in ADMIN_IDS:
        return

    data = await state.get_data()
    msg_id = data.get("message_id")
    from_chat = data.get("chat_id")
    await state.clear()

    users = await UserService.get_all_active(session)
    total = len(users)
    success = 0
    failed = 0

    status_msg = await callback.message.answer(f"📨 Yuborilmoqda... 0/{total}")

    for i, user in enumerate(users, 1):
        try:
            await bot.copy_message(
                chat_id=user.telegram_id,
                from_chat_id=from_chat,
                message_id=msg_id
            )
            success += 1
        except Exception as e:
            failed += 1
            if "blocked" in str(e).lower() or "deactivated" in str(e).lower():
                await UserService.block_user(session, user.telegram_id)

        # Har 20 ta da status yangilash
        if i % 20 == 0:
            try:
                percent = round(i / total * 100)
                await status_msg.edit_text(f"📨 Yuborilmoqda... {i}/{total} ({percent}%)")
            except Exception:
                pass

        await asyncio.sleep(0.05)  # Flood limit

    # Log saqlash
    log = BroadcastLog(total=total, success=success, failed=failed)
    session.add(log)
    await session.commit()

    await status_msg.edit_text(
        f"✅ <b>Xabar yuborildi!</b>\n\n"
        f"👥 Jami: {total}\n"
        f"✅ Muvaffaqiyatli: {success}\n"
        f"❌ Xato: {failed}\n"
        f"📊 Foiz: {round(success/total*100) if total else 0}%",
        parse_mode="HTML"
    )
    await callback.answer()
