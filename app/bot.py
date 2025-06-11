import asyncio
import logging
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from . import handlers
from .config import BOT_TOKEN, LOG_LEVEL, LOG_FILE, DEBUG
from .logger import logger


def setup_bot():
    """Настройка и инициализация бота"""
    try:
        # Настраиваем логгер
        logger.info("Setting up bot...")
        logger.info(f"Using token: {BOT_TOKEN[:10]}..." if BOT_TOKEN else "No BOT_TOKEN provided!")
        
        # Инициализируем бот с настройками по умолчанию
        bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode='HTML')
        )
        # Инициализируем диспетчер с хранилищем в памяти
        dp = Dispatcher(storage=MemoryStorage())
        
        # Регистрируем обработчики
        logger.info("Setting up routers...")
        router = handlers.setup_routers()
        dp.include_router(router)
        
        # Обработчик ошибок
        @dp.error()
        async def error_handler(event: types.ErrorEvent, *args, **kwargs):
            logger.error(f'Error: {event.exception}', exc_info=event.exception)
            await event.update.message.answer('Произошла ошибка. Пожалуйста, попробуйте еще раз.')
        
        logger.info("Bot setup completed")
        return bot, dp
        
    except Exception as e:
        logger.critical(f'Error in bot setup: {str(e)}', exc_info=True)
        raise


async def main():
    """Главная функция для запуска бота"""
    bot = dp = None
    try:
        bot, dp = setup_bot()
        logger.info('Starting bot...')
        
        # Проверяем соединение с API Telegram
        me = await bot.get_me()
        logger.info(f'Bot @{me.username} started successfully')
        
        # Запускаем поллинг
        logger.info('Starting polling...')
        await dp.start_polling(bot, skip_updates=True)
        
    except asyncio.CancelledError:
        logger.info('Bot stopped by user')
    except Exception as e:
        logger.critical(f'Fatal error: {str(e)}', exc_info=True)
        raise
    finally:
        if bot:
            logger.info('Closing bot session...')
            await bot.session.close()
        logger.info('Bot stopped')


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Bot stopped by user')
    except Exception as e:
        logger.critical(f'Unhandled exception: {str(e)}', exc_info=True)
        sys.exit(1)