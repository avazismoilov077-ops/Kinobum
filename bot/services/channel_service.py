from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import RequiredChannel


class ChannelService:

    @staticmethod
    async def get_all_active(session: AsyncSession) -> list[RequiredChannel]:
        result = await session.execute(
            select(RequiredChannel).where(RequiredChannel.is_active == True)
        )
        return result.scalars().all()

    @staticmethod
    async def get_all(session: AsyncSession) -> list[RequiredChannel]:
        result = await session.execute(
            select(RequiredChannel).order_by(RequiredChannel.id)
        )
        return result.scalars().all()

    @staticmethod
    async def add(session: AsyncSession, channel_id: str, title: str = None,
                  invite_link: str = None) -> RequiredChannel | None:
        # Avval mavjudligini tekshirish
        existing = await session.execute(
            select(RequiredChannel).where(RequiredChannel.channel_id == channel_id)
        )
        ch = existing.scalar_one_or_none()
        if ch:
            ch.is_active = True
            if title:
                ch.title = title
            if invite_link:
                ch.invite_link = invite_link
            await session.commit()
            return ch

        new_ch = RequiredChannel(
            channel_id=channel_id,
            title=title or channel_id,
            invite_link=invite_link,
        )
        session.add(new_ch)
        await session.commit()
        await session.refresh(new_ch)
        return new_ch

    @staticmethod
    async def remove(session: AsyncSession, ch_id: int) -> bool:
        result = await session.execute(
            select(RequiredChannel).where(RequiredChannel.id == ch_id)
        )
        ch = result.scalar_one_or_none()
        if ch:
            await session.delete(ch)
            await session.commit()
            return True
        return False

    @staticmethod
    async def toggle(session: AsyncSession, ch_id: int) -> RequiredChannel | None:
        result = await session.execute(
            select(RequiredChannel).where(RequiredChannel.id == ch_id)
        )
        ch = result.scalar_one_or_none()
        if ch:
            ch.is_active = not ch.is_active
            await session.commit()
        return ch
