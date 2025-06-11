import os
from pathlib import Path
from dotenv import load_dotenv
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from pydantic import BaseModel, Field
from typing import Optional

# Загружаем переменные окружения из .env файла
load_dotenv()

# Базовый каталог проекта
BASE_DIR = Path(__file__).parent.parent

# Создаем необходимые директории
for dir_name in ['out', 'logs', 'templates']:
    dir_path = BASE_DIR / dir_name
    dir_path.mkdir(exist_ok=True, parents=True)

# Пути к каталогам
OUTPUT_DIR = BASE_DIR / 'out'
TEMPLATES_DIR = BASE_DIR / 'templates'
LOGS_DIR = BASE_DIR / 'logs'

class Settings(BaseModel):
    # Токен бота
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    
    # Режим отладки
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
    
    # Настройки логирования
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT: str = '%Y-%m-%d %H:%M:%S'
    LOG_FILE: str = str(LOGS_DIR / 'bot.log')
    
    # Валидация токена бота
    def __init__(self, **data):
        super().__init__(**data)
        if not self.BOT_TOKEN:
            raise ValueError('BOT_TOKEN не указан в .env файле')

# Создаем экземпляр настроек
config = Settings()

# Алиасы для обратной совместимости
BOT_TOKEN = config.BOT_TOKEN
DEBUG = config.DEBUG

# Основная клавиатура
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Создать акт")],
            [KeyboardButton(text="Помощь"), KeyboardButton(text="Отмена")]
        ],
        resize_keyboard=True
    )

# Клавиатура отмены
def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отмена")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# Клавиатура подтверждения
def get_confirm_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Сгенерировать акт")],
            [KeyboardButton(text="🔁 Изменить / перегенерировать")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# Алиасы для обратной совместимости
MAIN_KEYBOARD = get_main_keyboard()
CANCEL_KEYBOARD = get_cancel_keyboard()
CONFIRM_KEYBOARD = get_confirm_keyboard()

# Настройки логирования
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_LEVEL = 'DEBUG' if DEBUG else 'INFO'
LOG_FILE = LOGS_DIR / 'bot.log'