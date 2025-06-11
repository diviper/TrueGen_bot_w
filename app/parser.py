import re
from datetime import datetime, date
from typing import List, Optional, Tuple, Dict, Any

from .models import ActData, ActItem
from .logger import logger

# Словарь для замены нежелательных слов
WORD_REPLACEMENTS = {
    'шлюх': 'Девушки',
    'проститутк': 'персонал',
    'кальян': 'оборудование',
    'по 10ке': 'по договорённости',
    'за ночь': 'за смену',
    'за сутки': 'за период',
    'три ночи': 'три смены',
    'ночей': 'смен',
    'ночь': 'смена',
    'девушк': 'ассистент',
    'девочк': 'ассистент',
    'мальчик': 'ассистент',
    'мальчиков': 'ассистентов',
    'девушек': 'ассистентов',
    'девочек': 'ассистентов',
    'по вызову': 'по заявке',
    'выезд': 'визит',
    'выездная': 'выездная бригада',
    'выездные': 'выездные бригады',
    'выездного': 'выездной бригады',
    'выездной': 'выездной бригады',
    'выездную': 'выездную бригаду',
    'выездные': 'выездные бригады',
    'выездными': 'выездными бригадами',
    'выездных': 'выездных бригад',
    'выездным': 'выездным бригадам',
    'выездными': 'выездными бригадами',
    'выездных': 'выездных бригадах'
}

# Список прилагательных для генерации нейтральных названий
NEUTRAL_ADJECTIVES = [
    'технический', 'вспомогательный', 'обслуживающий', 'оперативный', 'функциональный',
    'основной', 'дополнительный', 'резервный', 'аварийный', 'дежурный',
    'рабочий', 'сменный', 'постоянный', 'временный', 'сезонный'
]

# Список существительных для генерации нейтральных названий
NEUTRAL_NOUNS = [
    'персонал', 'состав', 'отряд', 'наряд', 'экипаж', 'расчет', 'отдел', 'департамент',
    'сектор', 'участок', 'блок', 'комплекс', 'набор', 'комплект', 'состав', 'персонал'
]

def clean_text(text: str) -> str:
    """
    Очищает текст от нежелательных слов и выражений
    
    Args:
        text: Исходный текст
        
    Returns:
        str: Очищенный текст
    """
    if not text or not isinstance(text, str):
        return text
    
    # Приводим к нижнему регистру для поиска
    lower_text = text.lower()
    
    # Проверяем наличие нежелательных слов
    has_inappropriate = any(word in lower_text for word in WORD_REPLACEMENTS.keys())
    
    # Если есть нежелательные слова, заменяем их
    if has_inappropriate:
        for word, replacement in WORD_REPLACEMENTS.items():
            if word in lower_text:
                # Заменяем с сохранением регистра
                text = re.sub(re.escape(word), replacement, text, flags=re.IGNORECASE)
        
        # Добавляем примечание о замене
        if not text.strip().endswith('.'):
            text += '.'
        text += ' (названия скорректированы)'
    
    return text

def generate_neutral_name() -> str:
    """Генерирует нейтральное название для замены"""
    adj = random.choice(NEUTRAL_ADJECTIVES)
    noun = random.choice(NEUTRAL_NOUNS)
    return f"{adj} {noun}"


class ActParser:
    """Класс для парсинга текстового представления акта"""
    
    # Регулярные выражения для разбора строки акта
    HEADER_PATTERN = re.compile(
        r'#АКТ\s+(?P<date>\d{1,2}[./]\d{1,2}[./]\d{2,4})\s*\|\s*Объект:\s*(?P<object_name>.+)',
        re.IGNORECASE
    )
    
    ITEM_PATTERN = re.compile(
        r'(?P<name>.+?)\s+'  # Наименование
        r'(?P<quantity>\d+(?:[.,]\d+)?(?:\s*[xх]\s*\d+)?)'  # Количество с возможным множителем (например, 3 x 1224)
        r'(?:\s*(?P<unit>[а-яa-z.]+)(?:\s+[а-яa-z.]*)?)?'  # Опциональная единица измерения с возможным текстом после
        r'\s*[×x*]\s*'  # Разделитель
        r'(?P<price>\d+(?:[.,]\d+)?(?:\s*[₽р]?\s*[а-яa-z.]*)?)'  # Цена с возможным текстом после
        r'\s*(?:[₽р]|$)',  # Опциональный знак рубля или конец строки
        re.IGNORECASE | re.UNICODE
    )
    
    # Словарь синонимов единиц измерения
    UNIT_ALIASES = {
        'шт': 'шт.',
        'штук': 'шт.',
        'м': 'м',
        'метр': 'м',
        'кг': 'кг',
        'килограмм': 'кг',
        'компл': 'компл.',
        'комплект': 'компл.',
    }
    
    @classmethod
    def parse_act(cls, text: str) -> ActData:
        """
        Парсит текст акта и возвращает объект ActData
        
        Args:
            text: Текст акта
            
        Returns:
            ActData: Объект с данными акта
            
        Raises:
            ValueError: Если формат акта некорректен
        """
        # Очищаем текст от нежелательных слов
        cleaned_text = clean_text(text)
        if cleaned_text != text:
            logger.info(f'Текст акта был очищен: {text[:100]}...')
            
        lines = [line.strip() for line in cleaned_text.split('\n') if line.strip()]
        if not lines:
            raise ValueError('Пустой акт')
            
        # Парсим заголовок
        header_match = cls.HEADER_PATTERN.match(lines[0])
        if not header_match:
            raise ValueError('Неверный формат заголовка. Пример: #АКТ 10.06.2025 | Объект: Название объекта')
            
        date_str = header_match.group('date')
        object_name = header_match.group('object_name').strip()
        
        # Очищаем название объекта
        object_name = clean_text(object_name)
        
        try:
            act_date = datetime.strptime(date_str, '%d.%m.%Y').date()
        except ValueError:
            raise ValueError(f'Неверный формат даты: {date_str}. Используйте ДД.ММ.ГГГГ')
            
        # Парсим позиции
        items = []
        for line in lines[1:]:
            try:
                # Пропускаем пустые строки и комментарии
                if not line.strip() or line.strip().startswith('#'):
                    continue
                    
                items.extend(item for item in [cls._parse_item(line)] if item)
            except Exception as e:
                logger.warning(f'Ошибка при разборе строки "{line}": {e}')
                continue
                
        # Удаляем дубликаты, сохраняя порядок
        seen = set()
        items = [x for x in items if not (x in seen or seen.add(x))]
                
        if not items:
            raise ValueError('Не найдено ни одной позиции в акте')
            
        return ActData(
            date=act_date,
            object_name=object_name,
            items=items
        )
    
    @classmethod
    def _parse_date(cls, date_str: str) -> date:
        """Парсит дату из строки"""
        # Нормализуем разделители
        date_str = date_str.replace('/', '.').replace('\\', '.')
        
        # Пробуем разные форматы даты
        for fmt in ('%d.%m.%Y', '%d.%m.%y', '%d.%m'):
            try:
                dt = datetime.strptime(date_str, fmt)
                # Если год не указан, используем текущий
                if fmt in ('%d.%m',):
                    dt = dt.replace(year=datetime.now().year)
                return dt.date()
            except ValueError:
                continue
        
        raise ValueError(f'Неизвестный формат даты: {date_str}')
    
    @classmethod
    def _parse_item(cls, line: str) -> Optional[ActItem]:
        """
        Парсит строку с позицией акта
        
        Args:
            line: Строка с позицией
            
        Returns:
            ActItem: Объект с данными позиции или None, если строка не соответствует формату
        """
        try:
            # Удаляем лишние пробелы и нормализуем символы
            line = ' '.join(line.split())
            
            # Пробуем найти совпадение с основным шаблоном
            match = cls.ITEM_PATTERN.match(line)
            
            # Если не нашли совпадение, пробуем альтернативные форматы
            if not match:
                # Формат: "3 кальяна по 1224"
                alt_match = re.match(r'(?P<quantity>\d+)\s+(?P<name>[^\d]+)(?:по|:)\s*(?P<price>\d+)', line, re.IGNORECASE)
                if alt_match:
                    name = alt_match.group('name').strip(' ,')
                    quantity = float(alt_match.group('quantity'))
                    price = float(alt_match.group('price'))
                    return ActItem(name=name, quantity=quantity, unit='шт.', price=price)
                
                # Формат: "4 шлюхи по 10ке за ночь, три ночи в целом"
                alt_match = re.match(r'(?P<quantity>\d+)\s+(?P<name>[^\d]+)(?:по|:)\s*(?P<price>\d+)', line, re.IGNORECASE)
                if alt_match:
                    name = alt_match.group('name').strip(' ,')
                    quantity = float(alt_match.group('quantity'))
                    price = float(alt_match.group('price'))
                    # Если в строке есть упоминание о ночах, умножаем на количество ночей
                    if 'ноч' in line.lower():
                        nights_match = re.search(r'(\d+)\s+ноч', line.lower())
                        if nights_match:
                            nights = float(nights_match.group(1))
                            price *= nights
                    return ActItem(name=name, quantity=quantity, unit='шт.', price=price)
                
                # Формат: "стойка слабаточная, 18 модулей по 1000р"
                alt_match = re.match(r'(?P<name>.+?)[,;]\s*(?P<quantity>\d+)\s+(?:модул|мод\.?|шт\.?)\s*(?:по|:)?\s*(?P<price>\d+)', line, re.IGNORECASE)
                if alt_match:
                    name = alt_match.group('name').strip()
                    quantity = float(alt_match.group('quantity'))
                    price = float(alt_match.group('price'))
                    return ActItem(name=name, quantity=quantity, unit='мод.', price=price)
                
                # Формат: "7 камер по 2000р"
                alt_match = re.match(r'(?P<quantity>\d+)\s+(?P<name>[^\d]+)(?:по|:)\s*(?P<price>\d+)', line, re.IGNORECASE)
                if alt_match:
                    name = alt_match.group('name').strip(' ,')
                    quantity = float(alt_match.group('quantity'))
                    price = float(alt_match.group('price'))
                    return ActItem(name=name, quantity=quantity, unit='шт.', price=price)
                
                return None
            
            # Обработка стандартного формата
            name = match.group('name').strip()
            quantity_str = match.group('quantity')
            unit = (match.group('unit') or 'шт.').lower()
            price_str = re.sub(r'[^0-9.,]', '', match.group('price'))
            
            # Обрабатываем количество с множителем (например, "3 x 1224")
            if 'x' in quantity_str or 'х' in quantity_str:  # Английская и русская x
                parts = re.split(r'[xх]', quantity_str, maxsplit=1)
                if len(parts) == 2:
                    qty = float(parts[0].strip().replace(',', '.'))
                    multiplier = float(parts[1].strip().replace(',', '.'))
                    quantity = qty * multiplier
                else:
                    quantity = float(quantity_str.replace(',', '.'))
            else:
                quantity = float(quantity_str.replace(',', '.'))
            
            # Обрабатываем цену (удаляем все нечисловые символы, кроме точки и запятой)
            price = float(price_str.replace(',', '.'))
            
            # Нормализуем единицу измерения
            unit = cls.UNIT_ALIASES.get(unit, unit)
            
            return ActItem(
                name=name.strip(),
                quantity=quantity,
                unit=unit,
                price=price
            )
            
        except (ValueError, AttributeError) as e:
            logger.debug(f'Ошибка парсинга строки "{line}": {e}')
            return None