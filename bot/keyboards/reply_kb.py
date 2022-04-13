from aiogram import types


commands = [
    'Создать презентацию', 'Выбрать презентацию', 'Помощь', 'Выбрать слайд', 'Загрузить презентацию',
    'Вернуться к выбору презентации', 'Изменить текст титульного листа', 'Создать новый слайд',
    'Вернуться к текущей презентации', 'Изменить заголовок', 'Изменить текст', 'Создать новый слайд',
    'К предыдущему слайду', 'К следующему слайду', 'Отмена', 'Удалить презентацию', 'Посмотреть содержимое слайда',
    'Добавить изображение', 'Удалить слайд', 'Добавить изображения'
]
buttons = {name: types.KeyboardButton(name) for name in commands}

help_kb = types.ReplyKeyboardMarkup(resize_keyboard=True).\
    add(buttons['Создать презентацию']).\
    add(buttons['Выбрать презентацию']).\
    add(buttons['Помощь'])

presentation_kb = types.ReplyKeyboardMarkup(resize_keyboard=True).\
    add(buttons['Выбрать слайд']).\
    add(buttons['Загрузить презентацию']).\
    add(buttons['Удалить презентацию']).\
    add(buttons['Вернуться к выбору презентации'])

header_kb = types.ReplyKeyboardMarkup(resize_keyboard=True).\
    add(buttons['Посмотреть содержимое слайда']).\
    add(buttons['Изменить текст']).\
    add(buttons['Создать новый слайд']).\
    add(buttons['К следующему слайду']).\
    add(buttons['Вернуться к текущей презентации'])

slide_kb = types.ReplyKeyboardMarkup(resize_keyboard=True).\
    add(buttons['Посмотреть содержимое слайда']).\
    add(buttons['Изменить текст']).\
    add(buttons['Добавить изображения']).\
    add(buttons['Создать новый слайд']).\
    add(buttons['К предыдущему слайду']).\
    add(buttons['К следующему слайду']).\
    add(buttons['Удалить слайд']).\
    add(buttons['Вернуться к текущей презентации'])

location_kb = types.ReplyKeyboardMarkup(resize_keyboard=True).\
    add(types.KeyboardButton('Отправить свое месторасположение', request_location=True)).\
    add(types.KeyboardButton('Отменить отправку месторасположения'))
