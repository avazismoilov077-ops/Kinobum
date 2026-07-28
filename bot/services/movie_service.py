from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Movie, MovieCode
from utils.logger import logger


class MovieService:

    @staticmethod
    async def create(session: AsyncSession, title: str, genre: str, description: str,
                     poster_file_id: str = None, video_file_id: str = None,
                     backup_message_id: int = None) -> Movie:
        movie = Movie(
            title=title,
            genre=genre,
            description=description,
            poster_file_id=poster_file_id,
            video_file_id=video_file_id,
            backup_message_id=backup_message_id,
        )
        session.add(movie)
        await session.commit()
        await session.refresh(movie)
        logger.info(f"Yangi kino qo'shildi: {movie.id} - {title}")
        return movie

    @staticmethod
    async def get_by_id(session: AsyncSession, movie_id: int) -> Movie | None:
        result = await session.execute(
            select(Movie).where(Movie.id == movie_id, Movie.is_active == True)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def find_by_code(session: AsyncSession, code: str) -> Movie | None:
        code = code.strip().lower()
        result = await session.execute(
            select(Movie)
            .join(MovieCode, MovieCode.movie_id == Movie.id)
            .where(
                func.lower(MovieCode.code) == code,
                Movie.is_active == True
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def search_by_title(session: AsyncSession, query: str) -> list[Movie]:
        result = await session.execute(
            select(Movie)
            .where(
                Movie.title.ilike(f"%{query}%"),
                Movie.is_active == True
            )
            .limit(10)
        )
        return result.scalars().all()

    @staticmethod
    async def get_latest(session: AsyncSession, limit: int = 10) -> list[Movie]:
        result = await session.execute(
            select(Movie)
            .where(Movie.is_active == True)
            .order_by(desc(Movie.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_popular(session: AsyncSession, limit: int = 10) -> list[Movie]:
        result = await session.execute(
            select(Movie)
            .where(Movie.is_active == True)
            .order_by(desc(Movie.views))
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_by_genre(session: AsyncSession, genre: str) -> list[Movie]:
        result = await session.execute(
            select(Movie)
            .where(Movie.genre.ilike(f"%{genre}%"), Movie.is_active == True)
            .order_by(desc(Movie.created_at))
            .limit(20)
        )
        return result.scalars().all()

    @staticmethod
    async def get_all_genres(session: AsyncSession) -> list[str]:
        result = await session.execute(
            select(Movie.genre).where(Movie.is_active == True, Movie.genre.isnot(None)).distinct()
        )
        return [r[0] for r in result.all() if r[0]]

    @staticmethod
    async def increment_views(session: AsyncSession, movie_id: int):
        result = await session.execute(select(Movie).where(Movie.id == movie_id))
        movie = result.scalar_one_or_none()
        if movie:
            movie.views += 1
            await session.commit()

    @staticmethod
    async def delete(session: AsyncSession, movie_id: int) -> bool:
        result = await session.execute(select(Movie).where(Movie.id == movie_id))
        movie = result.scalar_one_or_none()
        if movie:
            movie.is_active = False
            await session.commit()
            logger.info(f"Kino o'chirildi: {movie_id}")
            return True
        return False

    @staticmethod
    async def get_stats(session: AsyncSession) -> dict:
        total_movies = await session.scalar(select(func.count(Movie.id)).where(Movie.is_active == True))
        total_codes = await session.scalar(select(func.count(MovieCode.id)))
        top_movies = await session.execute(
            select(Movie).where(Movie.is_active == True).order_by(desc(Movie.views)).limit(5)
        )
        return {
            "total_movies": total_movies or 0,
            "total_codes": total_codes or 0,
            "top_movies": top_movies.scalars().all()
        }

    @staticmethod
    async def add_code(session: AsyncSession, movie_id: int, code: str) -> MovieCode | None:
        existing = await session.execute(
            select(MovieCode).where(func.lower(MovieCode.code) == code.strip().lower())
        )
        if existing.scalar_one_or_none():
            return None
        mc = MovieCode(movie_id=movie_id, code=code.strip())
        session.add(mc)
        await session.commit()
        await session.refresh(mc)
        return mc

    @staticmethod
    async def get_codes(session: AsyncSession, movie_id: int) -> list[MovieCode]:
        result = await session.execute(
            select(MovieCode).where(MovieCode.movie_id == movie_id)
        )
        return result.scalars().all()

    @staticmethod
    async def delete_code(session: AsyncSession, code_id: int) -> bool:
        result = await session.execute(select(MovieCode).where(MovieCode.id == code_id))
        code = result.scalar_one_or_none()
        if code:
            await session.delete(code)
            await session.commit()
            return True
        return False
