import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

from .config import config, DEBUG

# Настройка корневого логгера
def setup_logger():
    # Создаем форматтер
    formatter = logging.Formatter(
        fmt=config.LOG_FORMAT,
        datefmt=config.LOG_DATE_FORMAT
    )
    
    # Настраиваем обработчик для вывода в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Создаем директорию для логов, если её нет
    log_file = Path(config.LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Настраиваем обработчик для записи в файл с ротацией
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # Настраиваем уровень логирования
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    
    # Настраиваем корневой логгер
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Очищаем существующие обработчики
    logger.handlers.clear()
    
    # Добавляем обработчики
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Настраиваем уровень для библиотеки aiogram
    logging.getLogger('aiogram').setLevel(
        logging.DEBUG if config.DEBUG else logging.WARNING
    )
    
    # Настраиваем логирование asyncio в режиме отладки
    if config.DEBUG:
        logging.getLogger('asyncio').setLevel(logging.DEBUG)
    
    # Возвращаем настроенный логгер
    logger = logging.getLogger('act_bot')
    return logger

# Инициализируем логгер
logger = setup_logger()

# Логируем запуск логгера
logger.info('Инициализация логгера завершена')
logger.debug('Режим отладки: %s', 'ВКЛЮЧЕН' if config.DEBUG else 'ВЫКЛЮЧЕН')
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Повторная настройка логгера
logger = setup_logger()

# Функция для логирования в файл
def log_to_file(message, level='info'):
    """Логирует сообщение с указанным уровнем"""
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message)

# Логируем запуск логгера
logger.info('Инициализация логгера завершена')
logger.debug('Режим отладки: %s', 'ВКЛЮЧЕН' if config.DEBUG else 'ВЫКЛЮЧЕН')