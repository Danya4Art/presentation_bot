import logging
import os
import json

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext

from bot.pptx_maker import PPTXMaker
from bot.keyboards.reply_kb import help_kb, presentation_kb, commands
from bot.states.content import CreatePresentation
from stuff.paths import config_path, presentations_path


logger = logging.getLogger('handlers')


async def send_help(message: types.Message):
    await message.answer(
"""
РУКОВОДСТВО ПО ИСПОЛЬЗОВАНИЮ БОТА ДЛЯ СОЗДАНИЯ ПРЕЗЕНТАЦИЙ

Бот имеет 3 меню:
1. Главное - в нем Вы можете создать презентацию или выбрать уже созданную. 
При нажатии на кнопку выбора Вы увидите список всех существующих презентаций, нажмите на интересующую.
2. Презентация - здесь вы можете управлять презентацией, удалить ее или загрузить, отсюда Вы можете создать новый слайд по следующему шалону:
Добавить "заголовок ____" "длина ____" "дата ____" "gps ____" "заключение ____"
все поля являются опциональными, Вы сможете обновить их отдельно в меню слайда.
Если поле дата не было использовано в сообщении, то на слайде будет сегодняшняя дата.
Если поле gps не было исопльзовано в сообщении, то бот предложит отправить Ваше нынешнее месторасполажение через кнопку.
3. Слайд - в этом меню Вы также можете создавать слайды по шаблону как в меню Презентация.
Также Вы можете создавать пустые слайды, просматривать содержимое слайдов (в текстовом формате) и изменять содержимое

По вопросам обращайтесь к https://t.me/Danya4Art
"""
    )


async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    if not os.path.exists(config_path):
        with open(config_path, 'w') as f:
            f.write(json.dumps({'chats': {}}))
    user_config: dict = json.loads('\n'.join(open(config_path, 'r').readlines()))
    user_config['chats'].setdefault(
        message.chat.id,
        {
            'state': {
                'presentation': None, 'slide': None
            },
            'access': False,
            'catch_images': False
        }
    )
    with open(config_path, 'w') as f:
        f.write(json.dumps(user_config, indent=4))
    if not os.path.isdir(presentations_path):
        os.makedirs(presentations_path)
    if not os.path.isdir(os.path.join(presentations_path, str(message.chat.id))):
        os.makedirs(os.path.join(presentations_path, str(message.chat.id)))
    await message.reply("Бот для создания презентаций", reply_markup=help_kb)


async def cancel_handler(message: types.Message, state: FSMContext):
    """Allow user to cancel action via /cancel command"""
    current_state = await state.get_state()
    if current_state is None:
        # User is not in any state, ignoring
        return

    # Cancel state and inform user about it
    await state.finish()
    await message.reply('Отменено')


async def new_presentation(message: types.Message):
    """Start new presentation creation"""
    await CreatePresentation.name.set()
    await message.reply('Введите краткое название для новой презентации или /cancel чтобы отменить')


async def set_presentation_name(message: types.Message, state: FSMContext):
    """Check name for new presentation """
    await state.finish()
    if message.text in list(map(lambda x: x.replace('.pptx', ''), os.listdir(os.path.join(
            presentations_path, str(message.chat.id))))):
        await message.reply('Презентация с таким названием уже существует, пожалуйста, '
                            'выберите другое название или удалите существующую')
        return
    pm = PPTXMaker(path=os.path.abspath(
        os.path.join(
            presentations_path, str(message.chat.id), f'{message.text}.pptx')
        )
    )
    pm.save()
    user_config: dict = json.loads('\n'.join(open(config_path, 'r').readlines()))
    user_config['chats'][str(message.chat.id)]['state'].update({'presentation': message.text, 'slide': 0})
    with open(config_path, 'w') as f:
        f.write(json.dumps(user_config, indent=4))
    await message.reply(f'Успешно, презентация {message.text} создана')


async def choose_presentation(message: types.Message):
    """Open new presentation in bot"""
    prs = os.listdir(os.path.join(presentations_path, str(message.chat.id)))
    if len(prs) == 0:
        await message.reply('Презентации не найдены, создайте новую')
    else:
        kb = types.InlineKeyboardMarkup(resize_keyboard=True)
        for p in prs:
            kb.add(types.InlineKeyboardButton(p.replace('.pptx', ''), callback_data=f'/change {p}'))
        await message.reply('Выберите презентацию', reply_markup=kb)


async def change_presentation(callback_query: types.CallbackQuery, state: FSMContext):
    # await bot.answer_callback_query(callback_query.id)
    pr = ' '.join(callback_query.data.split()[1:])
    if os.path.exists(os.path.join(presentations_path, str(callback_query.message.chat.id), pr)):
        user_config: dict = json.loads('\n'.join(open(config_path, 'r').readlines()))
        user_config['chats'][str(callback_query.message.chat.id)]['state'].update({'presentation': pr, 'slide': -1})
        user_config['chats'][str(callback_query.message.chat.id)]['catch_images'] = True
        await callback_query.message.reply(f'Презентация {pr} выбрана, '
                                           f'Чтобы создать новый слайд напишите сообщение по следующему шаблону:\n\n',
                                           reply_markup=presentation_kb)
        await callback_query.message.answer('Добавить "заголовок _" "длина _" "дата _" "gps _" "заключение _"')
        await callback_query.message.answer('Для вызова более подробной информации отправьте /help')
        with open(config_path, 'w') as f:
            f.write(json.dumps(user_config, indent=4))
    else:
        await callback_query.message.reply('Презентации с таким именем не найдено, попробуйте снова')


def register_main_handlers(dp: Dispatcher):
    dp.register_message_handler(send_help, lambda msg: msg.text == 'Помощь')
    dp.register_message_handler(send_welcome, commands=['start', 'help'])
    dp.register_message_handler(cancel_handler, lambda msg: msg.text == 'Отмена', state='*')
    dp.register_message_handler(cancel_handler, state='*', commands=['cancel'])
    dp.register_message_handler(new_presentation, lambda msg: msg.text == 'Создать презентацию')
    dp.register_message_handler(set_presentation_name, lambda msg: msg.text not in commands, state=CreatePresentation.name)
    dp.register_message_handler(choose_presentation, lambda msg: msg.text == 'Выбрать презентацию')
    dp.register_callback_query_handler(change_presentation, lambda c: c.data.startswith('/change'))
