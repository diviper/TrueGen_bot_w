from aiogram.fsm.state import State, StatesGroup

class BotStates(StatesGroup):
    """Класс состояний бота"""
    waiting_for_act = State()  # Ожидание ввода акта
    waiting_for_confirmation = State()  # Ожидание подтверждения
    waiting_for_template = State()  # Ожидание загрузки шаблона
    waiting_for_act_edit = State()  # Ожидание редактирования акта
