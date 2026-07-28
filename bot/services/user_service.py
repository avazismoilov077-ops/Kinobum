from datetime import datetime, date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, WatchHistory, Movie
from utils.logger import logger


class UserService:

    @staticmethod
    async def get_or_create(session: AsyncSession, telegram_id: int, username: str = None, full_name: str = None) -> User:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            logger.info(f"Yangi foydalanuvchi: {telegram_id} - {full_name}")
        else:
            user.last_active = datetime.utcnow()
            if username:
                user.username = username
            if full_name:
                user.full_name = full_name
            await session.commit()
        return user

    @staticmethod
    async def get_all_active(session: AsyncSession) -> list[User]:
        result = await session.execute(
            select(User).where(User.is_blocked == False, User.is_active == True)
        )
        return result.scalars().all()

    @staticmethod
    async def increment_search(session: AsyncSession, telegram_id: int):
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.search_count += 1
            await session.commit()

    @staticmethod
    async def add_to_history(session: AsyncSession, user_id: int, movie_id: int):
        history = WatchHistory(user_id=user_id, movie_id=movie_id)
        session.add(history)
        await session.commit()

    @staticmethod
    async def get_history(session: AsyncSession, telegram_id: int, limit: int = 10) -> list:
        user_result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = user_result.scalar_one_or_none()
        if not user:
            return []
        result = await session.execute(
            select(WatchHistory, Movie)
            .join(Movie, WatchHistory.movie_id == Movie.id)
            .where(WatchHistory.user_id == user.id)
            .order_by(WatchHistory.watched_at.desc())
            .limit(limit)
        )
        return result.all()

    @staticmethod
    async def get_stats(session: AsyncSession) -> dict:
        total = await session.scalar(select(func.count(User.id)))
        today_start = datetime.combine(date.today(), datetime.min.time())
        today = await session.scalar(
            select(func.count(User.id)).where(User.joined_at >= today_start)
        )
        return {"total": total or 0, "today": today or 0}

    @staticmethod
    async def block_user(session: AsyncSession, telegram_id: int):
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.is_blocked = True
            await session.commit()
