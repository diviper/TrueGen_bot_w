from datetime import date
from typing import Optional, ClassVar, Type
from pydantic import BaseModel, Field, field_validator, ConfigDict, field_validator


class ActItem(BaseModel):
    """Модель позиции в акте"""
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., description="Наименование позиции")
    quantity: float = Field(..., gt=0, description="Количество")
    unit: str = Field(default="шт.", description="Единица измерения")
    price: float = Field(..., gt=0, description="Цена за единицу")
    
    def __hash__(self):
        """Хеш-функция для объекта ActItem"""
        return hash((self.name.lower(), self.unit.lower(), round(self.price, 2)))
    
    def __eq__(self, other):
        """Сравнение объектов ActItem"""
        if not isinstance(other, ActItem):
            return False
        return (self.name.lower() == other.name.lower() and 
                self.unit.lower() == other.unit.lower() and 
                abs(self.price - other.price) < 0.01)  # Сравнение с плавающей точкой
    
    @property
    def total(self) -> float:
        """Общая стоимость позиции"""
        return round(self.quantity * self.price, 2)


class ActData(BaseModel):
    """Модель данных акта"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    date: date
    object_name: str
    items: list[ActItem] = Field(default_factory=list, description="Список позиций в акте")
    
    @field_validator('items')
    def validate_items(cls, v: list) -> list:
        if not v:
            raise ValueError('Акт не может быть пустым')
        return v
    
    @property
    def total(self) -> float:
        """Общая сумма акта"""
        if not self.items:
            return 0.0
        return round(sum(item.total for item in self.items), 2)


class UserContext(BaseModel):
    """Контекст пользовательской сессии"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    current_act: Optional[ActData] = None
    last_message_id: Optional[int] = None
    state: str = "idle"  # idle, waiting_for_act, waiting_for_confirmation
    
    def reset(self) -> None:
        """Сброс контекста пользователя"""
        self.current_act = None
        self.state = "idle"