import pytest
from pathlib import Path

@pytest.fixture
def sample_act_text():
    return """
    #АКТ 12.05.2024 | Объект: Офис на Невском проспекте
    
    Услуги по уборке 1 кв.м. × 1500
    Мытье окон 3 шт. × 500
    """