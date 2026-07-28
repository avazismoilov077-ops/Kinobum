from datetime import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text,
    Boolean, DateTime, ForeignKey, func
)
from sqlalchemy.orm import relationship
from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    search_count = Column(Integer, default=0)
    joined_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    history = relationship("WatchHistory", back_populates="user", lazy="dynamic")

    def __repr__(self):
        return f"<User {self.telegram_id} - {self.full_name}>"


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False, index=True)
    genre = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    poster_file_id = Column(String(500), nullable=True)
    video_file_id = Column(String(500), nullable=True)
    backup_message_id = Column(BigInteger, nullable=True)
    views = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    codes = relationship("MovieCode", back_populates="movie", lazy="dynamic", cascade="all, delete-orphan")
    history = relationship("WatchHistory", back_populates="movie", lazy="dynamic")

    def __repr__(self):
        return f"<Movie {self.id} - {self.title}>"


class MovieCode(Base):
    __tablename__ = "movie_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(100), unique=True, nullable=False, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    movie = relationship("Movie", back_populates="codes")

    def __repr__(self):
        return f"<MovieCode {self.code} -> movie_id={self.movie_id}>"


class WatchHistory(Base):
    __tablename__ = "watch_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    watched_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="history")
    movie = relationship("Movie", back_populates="history")


class Advertisement(Base):
    __tablename__ = "advertisements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text, nullable=True)
    photo_file_id = Column(String(500), nullable=True)
    video_file_id = Column(String(500), nullable=True)
    button_text = Column(String(255), nullable=True)
    button_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class BroadcastLog(Base):
    __tablename__ = "broadcast_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    total = Column(Integer, default=0)
    success = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
