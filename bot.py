import os
import logging
import asyncio
import asyncpg
from datetime import datetime
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.executor import start_webhook

# ---------- НАСТРОЙКИ ----------
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан в переменных окружения!")

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL не задана в переменных окружения!")

WEBHOOK_HOST = os.environ.get('RENDER_EXTERNAL_URL')
if not WEBHOOK_HOST:
    raise ValueError("RENDER_EXTERNAL_URL не задана!")

WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
PORT = int(os.environ.get('PORT', 10000))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# ---------- РАБОТА С БАЗОЙ ДАННЫХ ----------
async def init_db():
    """Создаёт таблицы, если их нет"""
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS players (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            level INT DEFAULT 1,
            exp INT DEFAULT 0,
            credits INT DEFAULT 1000,
            joined_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    await conn.close()
    print("✅ Таблицы созданы/проверены")

async def get_player(user_id):
    """Получает игрока из БД"""
    conn = await asyncpg.connect(DATABASE_URL)
    row = await conn.fetchrow('SELECT * FROM players WHERE user_id = $1', user_id)
    await conn.close()
    return row

async def create_player(user_id, username, first_name):
    """Создаёт нового игрока в БД"""
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('''
        INSERT INTO players (user_id, username, first_name) VALUES ($1, $2, $3)
    ''', user_id, username, first_name)
    await conn.close()

# ---------- КОМАНДЫ ----------
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    first_name = message.from_user.first_name or "NoName"
    
    # Проверяем, есть ли игрок в БД
    player = await get_player(user_id)
    if not player:
        await create_player(user_id, username, first_name)
        await message.reply(
            f"👋 Привет, {first_name}! Ты зарегистрирован в игре!\n"
            f"Твой уровень: 1 | Кредиты: 1000\n\n"
            f"Используй /profile чтобы увидеть свой профиль."
        )
    else:
        await message.reply(
            f"👋 С возвращением, {first_name}!\n"
            f"Твой уровень: {player['level']} | Кредиты: {player['credits']}\n\n"
            f"Используй /profile для просмотра профиля."
        )

@dp.message_handler(commands=['profile'])
async def cmd_profile(message: types.Message):
    user_id = message.from_user.id
    player = await get_player(user_id)
    
    if not player:
        await message.reply("Сначала введи /start для регистрации.")
        return
    
    await message.reply(
        f"📊 **ПРОФИЛЬ**\n\n"
        f"Имя: {player['first_name']}\n"
        f"Уровень: {player['level']}\n"
        f"Опыт: {player['exp']}/100\n"
        f"💰 Кредиты: {player['credits']}\n"
        f"📅 В игре с: {player['joined_at'].strftime('%d.%m.%Y')}",
        parse_mode="Markdown"
    )

@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    await message.reply(
        "📚 **Доступные команды:**\n"
        "/start - Начать игру (регистрация)\n"
        "/profile - Показать профиль\n"
        "/help - Это сообщение"
    )

# ---------- ВЕБХУК (РУЧНОЙ AioHTTP) ----------
async def handle_webhook(request):
    """Обработчик POST-запросов от Telegram"""
    try:
        update_data = await request.json()
        update = types.Update(**update_data)
        await dp.process_update(update)
        return web.Response(status=200)
    except Exception as e:
        logging.error(f"Ошибка обработки вебхука: {e}")
        return web.Response(status=500)

async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Вебхук установлен на {WEBHOOK_URL}")
    info = await bot.get_webhook_info()
    print(f"ℹ️ Текущий вебхук: {info.url}")

async def on_shutdown(app):
    await bot.delete_webhook()
    print("👋 Вебхук удалён")

# ---------- ЗАПУСК ----------
if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())

    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, handle_webhook)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    print(f"🚀 Запуск aiohttp сервера на порту {PORT}")
    web.run_app(app, host='0.0.0.0', port=PORT)