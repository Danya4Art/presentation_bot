import logging
import os
import json
from random import randint

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext

from bot.pptx_maker import PPTXMaker
from bot.keyboards.reply_kb import slide_kb, presentation_kb, header_kb, commands
from bot.states.content import TextWait
from stuff.paths import config_path, presentations_path, images_path


logger = logging.getLogger('handlers')


async def get_slide_content(message: types.Message):
    user_config: dict = json.loads('\n'.join(open(config_path, 'r').readlines()))
    pr_path = os.path.join(presentations_path, str(message.chat.id),
                           user_config['chats'][str(message.chat.id)]['state']['presentation'])
    pm = PPTXMaker(pr_path, pr_path)
    response = pm.get_content(int(user_config['chats'][str(message.chat.id)]['state']['slide']))
    await message.answer('\n\n'.join(response))


async def create_slide(message: types.Message):
    user_config: dict = json.loads('\n'.join(open(config_path, 'r').readlines()))
    pr_path = os.path.join(presentations_path, str(message.chat.id),
                           user_config['chats'][str(message.chat.id)]['state']['presentation'])
    pm = PPTXMaker(pr_path, pr_path)
    pm.create_slide()
    pm.save()
    await message.answer(f'Новый слайд создан')


async def redact_text(message: types.Message):
    user_config: dict = json.loads('\n'.join(open(config_path, 'r').readlines()))
    kb = types.InlineKeyboardMarkup(resize_keyboard=True)
    headers = ['Название слайда', 'Дата инспекции', 'GPS-координаты', 'Замечания и ывод'] if user_config['chats'][str(message.chat.id)]['state']['slide'] else ['Название презентации']
    for header in headers:
        kb.add(types.InlineKeyboardButton(header, callback_data=f'/redact_text {header}'))
    await message.answer(f'Выберите, какой блок текста отредактировать', reply_markup=kb)


async def _redact_text(callback_query: types.CallbackQuery):
    """Redact specify shape/paragraph"""
    await TextWait.name.set()
    user_config: dict = json.loads('\n'.join(open(config_path, 'r').readlines()))
    cb = ' '.join(callback_query.data.split()[1:])
    data = {
        'Название слайда':  {
            'shape': 0,
            'paragraph': 0
        },
        'Дата инспекции': {
            'shape': 1,
            'paragraph': 1
        },
        'GPS-координаты': {
            'shape': 1,
            'paragraph': 3
        },
        'Выводы и замечания': {
            'paragraph': 5
        }
    } if user_config['chats'][str(callback_query.message.chat.id)]['state']['slide'] else {
        'Название презентации': {
            'shape': 2,
            'paragraph': 0
        }
    }
    if cb in data.keys():
        user_config: dict = json.loads('\n'.join(open(config_path, 'r').readlines()))
        user_config['chats'][str(callback_query.message.chat.id)]['state'].update(data[cb])
        with open(config_path, 'w') as f:
            f.write(json.dumps(user_config, indent=4))
        await callback_query.message.reply(f'Напишите текст для заполнения поля "{cb}"')
    else:
        await callback_query.message.reply('Такого поля нет')


async def set_text(message: types.Message, state: FSMContext):
    """Check name for new presentation """
    await state.finish()
    user_config: dict = json.loads('\n'.join(open(config_path, 'r').readlines()))
    pr_path = os.path.join(presentations_path, str(message.chat.id),
                           user_config['chats'][str(message.chat.id)]['state']['presentation'])
    pm = PPTXMaker(pr_path, pr_path)
    slide = user_config['chats'][str(message.chat.id)]['state']['slide']
    shape = user_config['chats'][str(message.chat.id)]['state']['shape']
    paragraph = user_config['chats'][str(message.chat.id)]['state']['paragraph']
    size, center, bold = 16, False, False
    if slide == 0 or shape == 0:
        size, center, bold = 30, True, True
    if paragraph:
        paragraph = int(paragraph)
    pm.put_text(slide, shape, message.text, paragraph=paragraph, size=size, center=center, bold=bold)
    pm.save()
    await message.reply(f'Успешно')


async def redact_img(message: types.Message):
    """Redact specify shape/paragraph"""
    user_config: dict = json.loads('\n'.join(open(config_path, 'r').readlines()))
    if not user_config['chats'][str(message.chat.id)]['state']['slide']:
        await message.reply(f'На титульном слайде не предусмотрено размещение изображений')
        return
    else:
        user_config['chats'][str(message.chat.id)]['catch_images'] = True
        with open(config_path, 'w') as f:
            f.write(json.dumps(user_config, indent=4))
        await message.reply(f'Отправьте изображения (по одному фото на одно сообщение)')


async def add_img(message: types.Message):
    """Check name for new presentation """
    user_config: dict = json.loads('\n'.join(open(config_path, 'r').readlines()))
    if not user_config['chats'][str(message.chat.id)]['catch_images']:
        await message.reply('Эти фото не будут прикреплены, чтобы новые фото прикреплялись к слайдам'
                            'отправьте /switch_catching')
        return
    pr_path = os.path.join(presentations_path, str(message.chat.id),
                           user_config['chats'][str(message.chat.id)]['state']['presentation'])
    pm = PPTXMaker(pr_path, pr_path)
    current_slide = user_config['chats'][str(message.chat.id)]['state']['slide']
    if not current_slide or current_slide == -1 and pm.slides_count == 1:
        await message.reply('Невозможно добавить фото на первый слайд, пожалуйста, выберите другой или создайте новый')
        return
    slide = user_config['chats'][str(message.chat.id)]['state']['slide']
    # for photo in message.photo:
    photo = message.photo[-1]
    logger.error(len(message.photo))
    photo_path = os.path.abspath(os.path.join(images_path, str(message.chat.id), f'{randint(1000, 9999)}.png'))
    await photo.download(destination_file=photo_path)
    logger.error(pm.get_content(slide))
    if int(pm.get_content(slide)[-1].split()[-1]) >= 4:
        pm.duplicate_slide()
        slide += 1
        user_config['chats'][str(message.chat.id)]['state']['slide'] = slide
        with open(config_path, 'w') as f:
            f.write(json.dumps(user_config, indent=4))
        await message.reply('На данном слайде достигнуто максимальное количество фотографий, создан новый слайд')
    pm.put_image(slide, photo_path)
    os.remove(photo_path)
    pm.save()
    await message.reply('Все фото добавлены')


async def switch_catching(message: types.Message):
    user_config: dict = json.loads('\n'.join(open(config_path, 'r').readlines()))
    user_config['chats'][str(message.chat.id)]['catch_images'] = not user_config['chats'][str(message.chat.id)]['catch_images']
    with open(config_path, 'w') as f:
        f.write(json.dumps(user_config, indent=4))
    await message.answer(
        'Теперь изображения' + (' ' if user_config['chats'][str(message.chat.id)]['catch_images'] else ' не ') +
        'будут прикрпеляться к презентации'
    )


async def to_pref(message: types.Message):
    user_config: dict = json.loads('\n'.join(open(config_path, 'r').readlines()))
    if user_config['chats'][str(message.chat.id)]['state']['slide'] > 0:
        user_config['chats'][str(message.chat.id)]['state']['slide'] -= 1
        with open(config_path, 'w') as f:
            f.write(json.dumps(user_config, indent=4))
        await message.answer(
            f"Успешно, текущий слайд {user_config['chats'][str(message.chat.id)]['state']['slide'] + 1}",
            reply_markup=(slide_kb if user_config['chats'][str(message.chat.id)]['state']['slide'] > 0 else header_kb)
        )
    else:
        await message.answer('Вы уже находитесь на первом слайде')


async def to_next(message: types.Message):
    user_config: dict = json.loads('\n'.join(open(config_path, 'r').readlines()))
    pr_path = os.path.join(presentations_path, str(message.chat.id),
                           user_config['chats'][str(message.chat.id)]['state']['presentation'])
    pm = PPTXMaker(pr_path, pr_path)
    if user_config['chats'][str(message.chat.id)]['state']['slide'] < pm.slides_count - 1:
        user_config['chats'][str(message.chat.id)]['state']['slide'] += 1
        with open(config_path, 'w') as f:
            f.write(json.dumps(user_config, indent=4))
        await message.answer(
            f"Успешно, текущий слайд {user_config['chats'][str(message.chat.id)]['state']['slide'] + 1}",
            reply_markup=slide_kb
        )
    else:
        await message.answer('Вы уже находитесь на последнем слайде')


async def back_to_pres(message: types.Message):
    """This handler using for return to previous page"""
    await message.reply('Успешно', reply_markup=presentation_kb)


async def delete_slide(message: types.Message):
    user_config: dict = json.loads('\n'.join(open(config_path, 'r').readlines()))
    pr_path = os.path.join(presentations_path, str(message.chat.id),
                           user_config['chats'][str(message.chat.id)]['state']['presentation'])
    pm = PPTXMaker(pr_path, pr_path)
    slide = user_config['chats'][str(message.chat.id)]['state']['slide']
    if slide:
        pm.delete_slide(slide)
        pm.save()
        user_config['chats'][str(message.chat.id)]['state']['slide'] -= 1
        with open(config_path, 'w') as f:
            f.write(json.dumps(user_config, indent=4))
        await message.reply(
            'Успешно',
            reply_markup=(slide_kb if user_config['chats'][str(message.chat.id)]['state']['slide'] > 0 else header_kb)
        )
    else:
        await message.reply('Невозможно удалить первый слайд')


def register_slides_handlers(dp: Dispatcher):
    dp.register_message_handler(get_slide_content, lambda msg: msg.text == 'Посмотреть содержимое слайда')
    dp.register_message_handler(create_slide, lambda msg: msg.text == 'Создать новый слайд')
    dp.register_message_handler(delete_slide, lambda msg: msg.text.startswith('Удалить слайд'))
    dp.register_message_handler(to_pref, lambda msg: msg.text == 'К предыдущему слайду')
    dp.register_message_handler(to_next, lambda msg: msg.text == 'К следующему слайду')
    dp.register_message_handler(back_to_pres, lambda msg: msg.text.startswith('Вернуться к текущей презентации'))
    dp.register_message_handler(redact_text, lambda msg: msg.text == 'Изменить текст')
    dp.register_callback_query_handler(_redact_text, lambda c: c.data.startswith('/redact_text'))
    dp.register_message_handler(set_text, lambda msg: msg.text not in commands and msg.text.isdigit, state=TextWait.name)
    dp.register_message_handler(redact_img, lambda msg: msg.text == 'Добавить изображения')
    dp.register_message_handler(add_img, content_types=['photo'])
    dp.register_message_handler(switch_catching, commands=['switch_catching'])
