# 🎬 Kino Bot

Professional Telegram Kino Bot — aiogram 3.x, SQLite, Flask

## Ishga tushirish

```bash
cd bot
pip install -r requirements.txt
cp .env.example .env
# .env faylini to'ldiring
python bot.py
```

## .env sozlamalari

```env
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=6998664132
BACKUP_CHANNEL_ID=-1001234567890
REQUIRED_CHANNELS=@your_channel
PORT=8000
```

## Loyiha tuzilishi

```
bot/
├── bot.py              # Asosiy fayl
├── config.py           # Sozlamalar
├── requirements.txt
├── database/           # Models va DB
├── handlers/           # Barcha handlerlar
├── keyboards/          # Klaviaturalar
├── states/             # FSM states
├── middlewares/        # Middlewarelar
├── services/           # Business logic
├── utils/              # Logger
├── data/               # SQLite DB
└── logs/               # Log fayllar
```

## Render.com ga joylashtirish

1. GitHub ga push qiling
2. Render.com da `New Web Service` yarating
3. Environment variables qo'shing
4. Start command: `cd bot && python bot.py`
5. UptimeRobot da `/health` endpointni monitoring qiling

## Admin buyruqlari

- `/movie_{id}` — kinoni boshqarish
- `➕ Kino qo'shish` — yangi kino qo'shish
- `📊 Statistika` — botning statistikasi
- `📨 Barchaga xabar` — broadcast
- `📢 Reklama` — reklama boshqaruvi
