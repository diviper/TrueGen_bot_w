import os
from pathlib import Path
from typing import Dict, Optional, Any

from aiogram import Router, F, types, html
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from datetime import datetime

from .models import ActData, ActItem, UserContext
from .parser import ActParser, clean_text
from .docgen import generate_act_document
from .preview import format_act_preview
from .template_utils import ensure_template_exists, create_default_template, is_valid_docx
from .config import (
    TEMPLATES_DIR, OUTPUT_DIR, get_main_keyboard, 
    get_cancel_keyboard, get_confirm_keyboard, LOGS_DIR
)
from .logger import logger

# Импортируем состояния бота
from .states import BotStates

# Создаем директории, если их нет
for directory in [TEMPLATES_DIR, OUTPUT_DIR, LOGS_DIR]:
    try:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f'Проверка директории {directory}: OK')
    except Exception as e:
        logger.error(f'Ошибка при создании директории {directory}: {e}')
        raise

# Словарь для хранения контекста пользователей
user_contexts: Dict[int, UserContext] = {}


def get_user_context(user_id: int) -> UserContext:
    """Возвращает контекст пользователя, создает новый, если не существует"""
    if user_id not in user_contexts:
        user_contexts[user_id] = UserContext()
    return user_contexts[user_id]


async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    user = message.from_user
    logger.info(f'Пользователь {user.full_name} ({user.id}) начал работу с ботом')
    
    # Получаем основную клавиатуру
    keyboard = get_main_keyboard()
    
    # Логируем создание клавиатуры
    logger.debug(f"Created main keyboard: {keyboard}")
    
    await message.answer(
        "👋 Привет! Я бот для создания актов.\n\n"
        "Отправь мне текст акта в формате:\n\n"
        "#АКТ 10.06.2025 | Объект: Название объекта\n"
        "подрозетники 30×40₽\n"
        "кабель 45 м × 25₽",
        reply_markup=keyboard
    )


async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    help_text = (
        "📝 <b>Как пользоваться ботом:</b>\n\n"
        "1. Отправь мне текст акта в формате:\n"
        "<code>#АКТ 10.06.2025 | Объект: Название объекта\n"
        "подрозетники 30×40₽\n"
        "кабель 45 м × 25₽</code>\n\n"
        "2. Проверь предпросмотр и подтверди генерацию\n"
        "3. Получи готовый акт в формате Word\n\n"
        "<b>Доступные команды:</b>\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать справку\n"
        "/cancel - Отменить текущее действие"
    )
    
    await message.answer(help_text, parse_mode='HTML')


async def cmd_cancel(message: types.Message, state: FSMContext):
    """Обработчик команды /cancel"""
    user = message.from_user
    user_ctx = get_user_context(user.id)
    user_ctx.reset()
    
    await state.finish()
    await message.answer(
        'Текущее действие отменено. Что бы вы хотели сделать?',
        reply_markup=get_main_keyboard()
    )
    logger.info(f'Пользователь {user.id} отменил текущее действие')


async def handle_act_text(message: types.Message, state: FSMContext):
    """Обработчик текста акта"""
    user = message.from_user
    user_ctx = get_user_context(user.id)
    
    try:
        # Парсим акт
        act_data = ActParser.parse_act(message.text)
        logger.info(f'Распарсенные данные: {act_data}')
        
        # Сохраняем акт в контекст пользователя
        user_ctx.current_act = act_data
        
        # Формируем предпросмотр
        preview = format_act_preview(act_data)
        
        # Получаем клавиатуру подтверждения
        keyboard = get_confirm_keyboard()
        
        # Отправляем предпросмотр
        sent_message = await message.answer(
            f'🔍 <b>Предпросмотр акта:</b>\n\n{preview}',
            parse_mode='HTML',
            reply_markup=keyboard
        )
        
        # Сохраняем ID сообщения для возможного редактирования
        user_ctx.last_message_id = sent_message.message_id
        
        # Переходим в состояние ожидания подтверждения
        await state.set_state(BotStates.waiting_for_confirmation)
        logger.info(f'Пользователь {user.id} отправил акт для проверки. Состояние: {await state.get_state()}')
        
    except Exception as e:
        error_msg = f'Ошибка при обработке акта: {str(e)}'
        logger.error(error_msg, exc_info=True)
        
        # Отправляем подробное сообщение об ошибке
        error_details = (
            '❌ <b>Ошибка при разборе акта!</b>\n\n'
            f'<b>Причина:</b> {str(e)}\n\n'
            'Проверьте формат ввода и попробуйте еще раз.\n\n'
            '<b>Пример правильного формата:</b>\n'
            '<code>#АКТ 10.06.2025 | Объект: Название объекта\n'
            'подрозетники 30×40₽\n'
            'кабель 45 м × 25₽</code>\n\n'
            'Или используйте формат с "по":\n'
            '<code>3 камеры по 2000₽\n'
            'стойка, 18 модулей по 1000₽</code>\n\n'
            '<i>Подсказка: Убедитесь, что каждая позиция с новой строки и указаны все необходимые параметры.</i>'
        )
        
        await message.answer(error_details, parse_mode='HTML')
        
        # Показываем кнопку отмены
        keyboard = get_cancel_keyboard()
        await message.answer("Нажмите 'Отмена', чтобы вернуться в главное меню.", reply_markup=keyboard)


async def handle_confirmation(message: types.Message, state: FSMContext):
    """Обработчик подтверждения генерации акта"""
    user = message.from_user
    user_ctx = get_user_context(user.id)
    logger.info(f'Обработка подтверждения от пользователя {user.id}. Текущий акт: {user_ctx.current_act is not None}')
    
    if not user_ctx.current_act:
        error_msg = 'Ошибка: данные акта отсутствуют в контексте пользователя'
        logger.error(error_msg)
        await message.answer(
            '❌ Ошибка: данные акта устарели. Пожалуйста, начните заново.',
            reply_markup=get_main_keyboard()
        )
        await state.finish()
        return
    
    if message.text == '✅ Сгенерировать акт':
        loading_msg = await message.answer('🔄 <b>Генерация акта...</b>', parse_mode='HTML')
        
        try:
            logger.info(f'Попытка генерации акта для пользователя {user.id}. Данные: {user_ctx.current_act}')
            
            # Проверяем и создаем шаблон при необходимости
            template_path = ensure_template_exists()
            logger.info(f'Используемый шаблон: {template_path.absolute() if template_path else "Не используется"}')
            
            # Генерируем имя файла
            timestamp = int(datetime.now().timestamp())
            doc_filename = f'Акт_от_{user_ctx.current_act.date.strftime("%d.%m.%Y")}_{timestamp}.docx'
            doc_path = OUTPUT_DIR / doc_filename
            
            # Генерируем документ с обработкой ошибок
            try:
                logger.info(f'Начало генерации документа. Шаблон: {template_path}, Выходной файл: {doc_path}')
                
                doc_path = generate_act_document(
                    act_data=user_ctx.current_act,
                    template_path=template_path,
                    output_path=doc_path
                )
                
                logger.info(f'Документ успешно сгенерирован: {doc_path.absolute()}')
                
                # Проверяем существование файла
                logger.info(f'Проверка существования файла: {doc_path.absolute()}')
                if not doc_path.exists():
                    error_msg = f'Сгенерированный файл не найден: {doc_path.absolute()}'
                    logger.error(error_msg)
                    raise FileNotFoundError(error_msg)
                
                # Проверяем размер файла
                file_size = doc_path.stat().st_size
                logger.info(f'Размер сгенерированного файла: {file_size} байт')
                
                if file_size == 0:
                    error_msg = f'Сгенерированный файл пуст: {doc_path.absolute()}'
                    logger.error(error_msg)
                    raise IOError(error_msg)
                
                # Отправляем документ пользователю
                logger.info(f'Попытка отправить документ пользователю: {doc_filename} ({file_size} байт)')
                await message.answer_document(
                    document=FSInputFile(doc_path, filename=doc_filename),
                    caption='✅ <b>Акт успешно сгенерирован!</b>',
                    parse_mode='HTML',
                    reply_markup=get_main_keyboard()
                )
                logger.info(f'Пользователь {user.id} успешно получил акт: {doc_path.absolute()}')
                
            except ValueError as e:
                logger.error(f'Ошибка валидации при генерации акта: {str(e)}', exc_info=True)
                await message.answer(
                    f'❌ <b>Ошибка при генерации акта:</b> {str(e)}\n\n'
                    'Проверьте корректность введенных данных и попробуйте еще раз.',
                    parse_mode='HTML',
                    reply_markup=get_main_keyboard()
                )
            except IOError as e:
                logger.error(f'Ошибка ввода-вывода при генерации акта: {str(e)}', exc_info=True)
                await message.answer(
                    '❌ <b>Ошибка при сохранении файла акта.</b>\n\n'
                    'Проверьте права доступа к директории или свяжитесь с поддержкой.',
                    parse_mode='HTML',
                    reply_markup=get_main_keyboard()
                )
            except Exception as e:
                logger.error(f'Непредвиденная ошибка при генерации акта: {str(e)}', exc_info=True)
                try:
                    # Пробуем создать простой документ как запасной вариант
                    doc = Document()
                    doc.add_heading('АКТ ВЫПОЛНЕННЫХ РАБОТ', 0)
                    doc.add_paragraph(f'Дата: {user_ctx.current_act.date.strftime("%d.%m.%Y")}')
                    doc.add_paragraph(f'Объект: {user_ctx.current_act.object_name}')
                    doc.add_paragraph()
                    
                    # Добавляем таблицу с позициями
                    table = doc.add_table(rows=1, cols=5, style='Table Grid')
                    table.cell(0, 0).text = '№'
                    table.cell(0, 1).text = 'Наименование'
                    table.cell(0, 2).text = 'Кол-во'
                    table.cell(0, 3).text = 'Ед.'
                    table.cell(0, 4).text = 'Сумма, ₽'
                    
                    for idx, item in enumerate(user_ctx.current_act.items, 1):
                        row = table.add_row().cells
                        row[0].text = str(idx)
                        row[1].text = item.name
                        row[2].text = str(item.quantity)
                        row[3].text = item.unit
                        row[4].text = f"{item.total:.2f}"
                    
                    # Добавляем итоговую сумму
                    doc.add_paragraph()
                    doc.add_paragraph(f'Итого: {user_ctx.current_act.total:.2f} ₽')
                    doc.add_paragraph('Без НДС')
                    
                    # Сохраняем документ
                    doc.save(doc_path)
                    logger.info(f'Создан упрощенный документ: {doc_path.absolute()}')
                    
                    # Отправляем документ пользователю
                    await message.answer_document(
                        document=FSInputFile(doc_path, filename=doc_filename),
                        caption='✅ <b>Акт сгенерирован в упрощенном виде.</b>',
                        parse_mode='HTML',
                        reply_markup=get_main_keyboard()
                    )
                    logger.info(f'Пользователь {user.id} получил упрощенный акт: {doc_path.absolute()}')
                    
                except Exception as inner_e:
                    logger.error(f'Критическая ошибка при создании упрощенного документа: {str(inner_e)}', exc_info=True)
                    raise Exception('Не удалось сгенерировать акт. Пожалуйста, попробуйте еще раз или свяжитесь с поддержкой.')
        finally:
            # Всегда сбрасываем состояние, даже если произошла ошибка
            try:
                user_ctx.reset()
                await state.finish()
                logger.info(f'Состояние пользователя {user.id} сброшено')
            except Exception as e:
                logger.error(f'Ошибка при сбросе состояния: {str(e)}', exc_info=True)
        
    elif message.text == '🔁 Изменить / перегенерировать':
        logger.info(f'Пользователь {user.id} запросил изменение акта')
        await message.answer(
            'Хорошо, пришлите исправленный текст акта:',
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.set_state(BotStates.waiting_for_act)
        logger.info(f'Состояние пользователя {user.id} изменено на waiting_for_act')


def setup_routers() -> Router:
    """Настройка и возврат роутера с обработчиками"""
    router = Router()
    
    # Хэндлеры команд
    router.message.register(cmd_start, Command("start"))
    router.message.register(cmd_help, Command("help"))
    router.message.register(cmd_cancel, Command("cancel"))
    
    # Обработчики состояний
    router.message.register(
        handle_act_text, 
        F.text,
        StateFilter(BotStates.waiting_for_act)
    )
    router.message.register(
        handle_confirmation,
        F.text,
        StateFilter(BotStates.waiting_for_confirmation)
    )
    
    # Обработчики кнопок
    @router.message(F.text == "Помощь")
    async def help_button(message: types.Message):
        await cmd_help(message)
    
    @router.message(F.text == "Создать акт")
    async def create_act_button(message: types.Message, state: FSMContext):
        try:
            logger.info(f"Кнопка 'Создать акт' нажата. Текущее состояние: {await state.get_state()}")
            await message.answer(
                "📝 Отправьте текст акта в формате:\n\n"
                "#АКТ 10.06.2025 | Объект: Название объекта\n"
                "подрозетники 30×40₽\n"
                "кабель 45 м × 25₽",
                reply_markup=types.ReplyKeyboardRemove()
            )
            await state.clear()  # Очищаем предыдущее состояние
            await state.set_state(BotStates.waiting_for_act)
            logger.info(f"Состояние после установки: {await state.get_state()}")
            return True
        except Exception as e:
            logger.error(f"Ошибка в create_act_button: {str(e)}", exc_info=True)
            await message.answer("Произошла ошибка. Пожалуйста, попробуйте еще раз.")
            return False
    
    @router.message(F.text == "Отмена")
    async def cancel_button(message: types.Message, state: FSMContext):
        await cmd_cancel(message, state)
    
    # Обработчик любого текстового сообщения
    @router.message(F.text)
    async def handle_text(message: types.Message, state: FSMContext):
        try:
            if message.text.startswith('/'):
                await cmd_start(message)
                return
                
            current_state = await state.get_state()
            logger.info(f"Получено текстовое сообщение. Текущее состояние: {current_state}")
            logger.info(f"Текст сообщения: {message.text[:100]}...")
            
            # Проверяем, похож ли текст на акт (начинается с #АКТ)
            if message.text.strip().startswith('#АКТ'):
                logger.info("Обнаружен текст акта, начинаем обработку")
                await state.set_state(BotStates.waiting_for_act)
                await handle_act_text(message, state)
            # Если состояние уже установлено
            current_state = await state.get_state()
            if current_state == BotStates.waiting_for_act:
                logger.info("Обработка как акт")
                await handle_act_text(message, state)
            elif current_state == BotStates.waiting_for_confirmation:
                logger.info("Обработка как подтверждение")
                await handle_confirmation(message, state)
            # Если состояние не установлено, но текст похож на акт
            elif any(x in message.text.lower() for x in ['×', 'x', '*', 'шт', 'м', 'р', 'руб']):
                logger.info("Текст похож на акт, начинаем обработку")
                await state.set_state(BotStates.waiting_for_act)
                await handle_act_text(message, state)
            # Во всех остальных случаях показываем справку
            else:
                await cmd_help(message)
        except Exception as e:
            logger.error(f"Ошибка в handle_text: {str(e)}", exc_info=True)
            await message.answer("Произошла ошибка при обработке сообщения. Пожалуйста, попробуйте еще раз.")
    
    # Обработчик неизвестных сообщений
    @router.message()
    async def unknown_message(message: types.Message):
        await message.answer(
            "Извините, я не понимаю эту команду. "
            "Введите /help для справки или /start для начала работы."
        )
    
    return router