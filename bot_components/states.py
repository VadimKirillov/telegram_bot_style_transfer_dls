from aiogram.dispatcher.filters.state import State, StatesGroup


class ST_States(StatesGroup):
    waiting_for_style = State()
    waiting_for_content = State()


class Standart_Styles_States(StatesGroup):
    waiting_for_style = State()
    waiting_for_content = State()