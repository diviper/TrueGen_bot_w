from typing import List, Optional
from datetime import date

from .models import ActData, ActItem


def format_act_preview(act_data: ActData) -> str:
    """
    Форматирует данные акта в читаемый текст для предпросмотра
    
    Args:
        act_data: Данные акта
        
    Returns:
        Отформатированная строка с предпросмотром
    """
    # Заголовок
    lines = [
        f"<b>Акт выполненных работ</b>\n",
        f"<b>Дата:</b> {act_data.date.strftime('%d.%m.%Y')}",
        f"<b>Объект:</b> {act_data.object_name}",
        ""
    ]
    
    # Шапка таблицы
    lines.append(
        "<b>№ п/п</b> | "
        "<b>Наименование работ</b> | "
        "<b>Кол-во</b> | "
        "<b>Ед. изм.</b> | "
        "<b>Цена за ед., ₽</b> | "
        "<b>Стоимость, ₽</b>"
    )
    lines.append("-" * 80)
    
    # Позиции
    for i, item in enumerate(act_data.items, 1):
        total = item.quantity * item.price
        lines.append(
            f"{i:>5} | "
            f"{item.name[:30]:<30} | "
            f"{_format_number(item.quantity):>6} | "
            f"{item.unit:^8} | "
            f"{_format_number(item.price):>12} | "
            f"{_format_number(total):>12}"
        )
    
    # Итог
    lines.extend([
        "-" * 80,
        f"<b>Итого:</b> {_format_number(act_data.total)} ₽",
        f"<b>Без НДС</b>"
    ])
    
    return "\n".join(lines)


def _format_number(value: float) -> str:
    """
    Форматирует число с разделением разрядов и удалением лишних нулей
    
    Args:
        value: Число для форматирования
        
    Returns:
        Отформатированная строка
    """
    # Форматируем с разделением разрядов
    formatted = "{0:,.2f}".format(value).replace(",", " ")
    
    # Удаляем лишние нули и точку, если число целое
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    
    return formatted


def format_act_as_text(act_data: ActData) -> str:
    """
    Форматирует данные акта в текстовый формат для сохранения
    
    Args:
        act_data: Данные акта
        
    Returns:
        Отформатированная строка с данными акта
    """
    lines = [
        f"#АКТ {act_data.date.strftime('%d.%m.%Y')} | Объект: {act_data.object_name}"
    ]
    
    for item in act_data.items:
        lines.append(
            f"{item.name} {_format_number(item.quantity)} {item.unit} × {_format_number(item.price)}₽"
        )
    
    return "\n".join(lines)