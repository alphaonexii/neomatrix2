import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.executor import start_webhook

# ---------- НАСТРОЙКИ ----------
# Берём токен из переменных окружения (это безопасно)
BOT_TOKEN = os.environ.get('8695102951:AAFFfrLz8g5WA_N-ZHK9dmR4DuJZbR2KQlY')  # ЗАМЕНИТЕ НА СВОЙ ТОКЕН!
# Render автоматически подставляет внешний URL в переменную RENDER_EXTERNAL_URL
WEBHOOK_HOST = os.environ.get('RENDER_EXTERNAL_URL', 'https://ваш-сервис.onrender.com')  # ЗАМЕНИТЕ ПОТОМ
WEBHOOK_PATH = '/webhook'  # Путь, на который Telegram будет отправлять обновления
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"  # Полный URL вебхука
PORT = int(os.environ.get('PORT', 10000))  # Порт, который слушает Render

# Настраиваем логирование – чтобы видеть, что происходит
logging.basicConfig(level=logging.INFO)

# Создаём бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())  # Добавляем логирование

# ---------- КОМАНДЫ ----------
# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    """Отвечает на команду /start"""
    await message.reply(
        "👋 Привет! Я новый бот, созданный с нуля.\n"
        "Пока я умею только отвечать на /start и /help."
    )

# Обработчик команды /help
@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    """Отвечает на команду /help"""
    await message.reply(
        "📚 Доступные команды:\n"
        "/start - Приветствие\n"
        "/help - Это сообщение"
    )

# ---------- ВЕБХУК ----------
async def on_startup(dp):
    """Выполняется при запуске бота"""
    # Устанавливаем вебхук
    await bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Вебхук установлен на {WEBHOOK_URL}")

async def on_shutdown(dp):
    """Выполняется при остановке бота"""
    # Удаляем вебхук
    await bot.delete_webhook()
    print("👋 Вебхук удалён")

# ---------- ЗАПУСК ----------
if __name__ == '__main__':
    # Запускаем вебхук
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host='0.0.0.0',
        port=PORT
    )