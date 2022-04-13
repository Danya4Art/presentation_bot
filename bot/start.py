from handlers.slide import register_slides_handlers
from handlers.presentation import register_presentation_handlers
from handlers.main import register_main_handlers

from stuff.paths import api_token_path

from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import os
import logging


if __name__ == '__main__':
    if not os.path.exists(api_token_path):
        logging.error('There is no token for Bot, please contact developer')
        logging.error(api_token_path)
        raise FileNotFoundError('Telegram handlers token not found')
    storage = MemoryStorage()
    API_TOKEN = open(api_token_path).readline()
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(bot=bot, storage=storage)
    register_slides_handlers(dp)
    register_presentation_handlers(dp)
    register_main_handlers(dp)
    executor.start_polling(dp, skip_updates=True)
