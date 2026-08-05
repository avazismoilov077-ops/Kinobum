import os
from dotenv import load_dotenv

load_dotenv()

# Bot sozlamalari
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_IDS: list[int] = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "6998664132").split(",") if x.strip()]

# Kanal sozlamalari
BACKUP_CHANNEL_ID: int = int(os.getenv("BACKUP_CHANNEL_ID", "0"))
REQUIRED_CHANNELS: list[str] = [
    x.strip() for x in os.getenv("REQUIRED_CHANNELS", "").split(",") if x.strip()
]

# Database
DATABASE_URL: str = os.getenv("SQLITE_URL", "sqlite+aiosqlite:///data/kino_bot.db")

# Flask
FLASK_PORT: int = int(os.getenv("PORT", "8000"))

# Reklama
AD_INTERVAL: int = int(os.getenv("AD_INTERVAL", "10"))  # Har necha qidiruvdan keyin
