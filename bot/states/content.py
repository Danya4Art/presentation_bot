from aiogram.dispatcher.filters.state import State, StatesGroup


class CreatePresentation(StatesGroup):
    name = State()


class ChooseSlide(StatesGroup):
    name = State()


class TextWait(StatesGroup):
    name = State()
