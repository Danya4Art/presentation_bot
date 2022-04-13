import logging
import os
import json
import re
from datetime import date

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext

from bot.keyboards.reply_kb import slide_kb, help_kb, header_kb, commands
from stuff.paths import config_path, presentations_path
from bot.states.content import ChooseSlide
from bot.pptx_maker import PPTXMaker


logger = logging.getLogger('handlers')


async def back(message: types.Message):
    """
    This handler using for return to previous page
    """
    await message.reply('Успешно', reply_markup=help_kb)


async def choose_slide(message: types.Message):
    """Wait for slide number"""
    user_config: dict = json.loads('\n'.join(open(config_path, 'r').readlines()))
    pr_path = os.path.join(presentations_path, str(message.chat.id),
                           user_config['chats'][str(message.chat.id)]['state']['presentation'])
    pm = PPTXMaker(pr_path, pr_path)
    if pm.slides_count == 1:
        await message.reply('Выбран титульный слайд', reply_markup=header_kb)
    else:
        await ChooseSlide.name.set()
        await message.reply(f'Напишите номер слайда от 1 до {pm.slides_count}')


async def set_slide_number(message: types.Message, state: FSMContext):
    """Check name for new presentation """
    await state.finish()
    user_config: dict = json.loads('\n'.join(open(config_path, 'r').readlines()))
    pr_path = os.path.join(presentations_path, str(message.chat.id),
                           user_config['chats'][str(message.chat.id)]['state']['presentation'])
    pm = PPTXMaker(pr_path, pr_path)
    slide_number = int(message.text) - 1
    if 0 <= slide_number < pm.slides_count:
        user_config['chats'][str(message.chat.id)]['state'].update({'slide': slide_number})
        with open(config_path, 'w') as f:
            f.write(json.dumps(user_config, indent=4))
        await message.reply(f'Вы выбрали {message.text} слайд', reply_markup=slide_kb)
    else:
        await message.reply(f'Число должно быть в диапазоне от 1 до {pm.slides_count}')


async def download_presentation(message: types.Message):
    user_config: dict = json.loads('\n'.join(open(config_path, 'r').readlines()))
    pr_path = os.path.join(presentations_path, str(message.chat.id),
                           user_config['chats'][str(message.chat.id)]['state']['presentation'])
    await message.answer_document(open(pr_path, 'rb'))


async def delete_presentation(message: types.Message):
    """Delete presentation"""
    kb = types.InlineKeyboardMarkup(resize_keyboard=True)
    kb.add(types.InlineKeyboardButton('Подтвердить удаление', callback_data='/delete'))
    await message.reply('Нажмите на кнопку ниже, чтобы удалить презентацию', reply_markup=kb)


async def force_delete_presentation(callback_query: types.CallbackQuery):
    """Approve deletion"""
    user_config: dict = json.loads('\n'.join(open(config_path, 'r').readlines()))
    pr_path = os.path.join(presentations_path, str(callback_query.message.chat.id),
                           user_config['chats'][str(callback_query.message.chat.id)]['state']['presentation'])
    os.remove(pr_path)
    await callback_query.message.answer('Презентация успешно удалена', reply_markup=help_kb)


async def add_slide_by_regex(message: types.Message):
    """Create new slide and fill it with text"""
    user_config: dict = json.loads('\n'.join(open(config_path, 'r').readlines()))
    pr_path = os.path.join(presentations_path, str(message.chat.id),
                           user_config['chats'][str(message.chat.id)]['state']['presentation'])
    pm = PPTXMaker(pr_path, pr_path)
    pm.create_slide()
    # header = re.findall(r'"Заголовок\s*(?P<header>.+?)"\s*', message.text, re.IGNORECASE)
    # length = re.findall(r'"Длина\s*(?P<header>.+?)"\s*', message.text, re.IGNORECASE)
    # insp_date = re.findall(r'"Дата\s*(?P<date>.+?)"\s*', message.text, re.IGNORECASE)
    # gps = re.findall(r'"GPS\s*(?P<gps>.+?)"\s*', message.text, re.IGNORECASE)
    # concl = re.findall(r'"Заключение\s*(?P<con>.+?)"\s*', message.text, re.IGNORECASE)
    match = re.match(
        r'Добавить\s*'
        r'"Заголовок\s*(?P<header>.+?)"\s*'
        r'"Длина\s*(?P<length>.+?)"\s*'
        r'("Дата\s*(?P<date>.+?)"\s*|'
        r'"GPS\s*(?P<gps>.+?)"\s*|'
        r'"Заключение\s*(?P<con>.+?)"\s*){0,3}',
        message.text,
        re.IGNORECASE
    )
    logger.error(match.groupdict())
    pm.put_text(-1, 0, f'{match["header"]}\nПротяженность {match["length"]}', size=20, center=True, bold=True)
    pm.put_text(-1, 1, f'{match["date"] if match["date"] else str(date.today().strftime("%d.%m.%Y"))}', paragraph=1)
    pm.put_text(-1, 1, f'{match["gps"] if match["gps"] else ""}', paragraph=3)
    pm.put_text(-1, 1, f'{match["con"] if match["con"] else ""}', paragraph=5)
    pm.save()
    user_config['chats'][str(message.chat.id)]['state']['slide'] = pm.slides_count - 1
    with open(config_path, 'w') as f:
        f.write(json.dumps(user_config, indent=4))
    # await ImageWait.name.set()
    await message.answer(f'Новый слайд создан, отправьте до 4ех фотографий, чтобы прикрепить их к этому слайду\n'
                         f'Чтобы новые фотографии не прикреплялись отправьте /cancel')


def register_presentation_handlers(dp: Dispatcher):
    dp.register_message_handler(back, lambda msg: msg.text.startswith('Вернуться к выбору презентации'))
    dp.register_message_handler(choose_slide, lambda msg: msg.text == 'Выбрать слайд')
    dp.register_message_handler(set_slide_number, lambda msg: msg.text not in commands and msg.text.isdigit(), state=ChooseSlide.name)
    dp.register_message_handler(download_presentation, lambda msg: msg.text == 'Загрузить презентацию')
    dp.register_message_handler(delete_presentation, lambda msg: msg.text == 'Удалить презентацию')
    dp.register_callback_query_handler(force_delete_presentation, lambda c: c.data == '/delete')
    dp.register_message_handler(add_slide_by_regex, regexp=r'^Добавить(\s*".+"\s*)+')
