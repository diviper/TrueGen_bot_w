import pytest
from datetime import datetime
from pathlib import Path
import sys

# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.parser import clean_text, ActParser
from app.models import ActData, ActItem

class TestCleanText:
    def test_clean_text_replaces_forbidden_words(self):
        """Тестирует замену запрещенных слов"""
        text = "Услуги шлюх и проституток"
        expected = "Услуги Девушки и персонал"
        assert clean_text(text) == expected

    def test_clean_text_preserves_good_text(self):
        """Тестирует, что нормальный текст не изменяется"""
        text = "Обычный текст без запрещенных слов"
        assert clean_text(text) == text

class TestActParser:
    def test_parse_act_valid_text(self, sample_act_text):
        """Тестирует разбор корректного акта"""
        act_data = ActParser.parse_act(sample_act_text)
        
        assert isinstance(act_data, ActData)
        assert act_data.object_name == "Офис на Невском проспекте"
        assert act_data.act_date == datetime(2024, 5, 12).date()
        assert len(act_data.items) == 2
        
        # Проверяем первую позицию
        assert act_data.items[0].name == "Услуги по уборке"
        assert act_data.items[0].quantity == 1.0
        assert act_data.items[0].unit == "кв.м."
        assert act_data.items[0].price == 1500.0
        
        # Проверяем вторую позицию
        assert act_data.items[1].name == "Мытье окон"
        assert act_data.items[1].quantity == 3.0
        assert act_data.items[1].unit == "шт."
        assert act_data.items[1].price == 500.0

    def test_parse_item_with_multiplier(self):
        """Тестирует разбор строки с множителем (например, 3 x 1000)"""
        item = ActParser._parse_item("Услуга 3 x 1000")
        assert item is not None
        assert item.name == "Услуга"
        assert item.quantity == 3.0
        assert item.unit is None or item.unit == ""
        assert item.price == 1000.0

    def test_parse_item_with_unit(self):
        """Тестирует разбор строки с единицей измерения"""
        item = ActParser._parse_item("Услуга 5 шт. × 500")
        assert item is not None
        assert item.name == "Услуга"
        assert item.quantity == 5.0
        assert item.unit == "шт."
        assert item.price == 500.0

    def test_parse_item_invalid_format(self):
        """Тестирует обработку некорректного формата строки"""
        item = ActParser._parse_item("Просто текст без цифр")
        assert item is None