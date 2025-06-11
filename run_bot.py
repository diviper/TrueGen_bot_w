import os
import sys
import asyncio
import logging
from pathlib import Path

# Настраиваем базовое логирование для отладки запуска
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('run_bot')

# Добавляем корень проекта в PYTHONPATH
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

logger.info(f"Python {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"Project root: {project_root}")

# Проверяем наличие .env файла
env_path = project_root / '.env'
logger.info(f"Checking .env at: {env_path}")

if not env_path.exists():
    logger.error(".env file not found!")
    sys.exit(1)

# Проверяем токен бота
with open(env_path, 'r', encoding='utf-8') as f:
    has_token = 'BOT_TOKEN=' in f.read()
    
if not has_token:
    logger.error("BOT_TOKEN not found in .env file!")
    sys.exit(1)

logger.info("Environment check passed")

# Импортируем бота после настройки окружения
from app.bot import main

if __name__ == '__main__':
    logger.info("Starting bot...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception("Fatal error in bot:")
        sys.exit(1)
