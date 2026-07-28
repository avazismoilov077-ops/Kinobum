from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Advertisement


class AdService:

    @staticmethod
    async def get_active(session: AsyncSession) -> Advertisement | None:
        result = await session.execute(
            select(Advertisement).where(Advertisement.is_active == True).limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(session: AsyncSession) -> list[Advertisement]:
        result = await session.execute(select(Advertisement).order_by(Advertisement.id.desc()))
        return result.scalars().all()

    @staticmethod
    async def create(session: AsyncSession, text: str = None, photo_file_id: str = None,
                     video_file_id: str = None, button_text: str = None,
                     button_url: str = None) -> Advertisement:
        ad = Advertisement(
            text=text,
            photo_file_id=photo_file_id,
            video_file_id=video_file_id,
            button_text=button_text,
            button_url=button_url,
        )
        session.add(ad)
        await session.commit()
        await session.refresh(ad)
        return ad

    @staticmethod
    async def toggle(session: AsyncSession, ad_id: int) -> Advertisement | None:
        result = await session.execute(select(Advertisement).where(Advertisement.id == ad_id))
        ad = result.scalar_one_or_none()
        if ad:
            ad.is_active = not ad.is_active
            await session.commit()
        return ad

    @staticmethod
    async def delete(session: AsyncSession, ad_id: int) -> bool:
        result = await session.execute(select(Advertisement).where(Advertisement.id == ad_id))
        ad = result.scalar_one_or_none()
        if ad:
            await session.delete(ad)
            await session.commit()
            return True
        return False
