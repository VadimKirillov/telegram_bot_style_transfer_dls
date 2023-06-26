import logging
import asyncio

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.markdown import text, hbold, italic, code, pre
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton, ChatActions


import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import transforms, models
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
import threading
import os
import copy

from StyleLoss import Style_transfer
from keyboard import START_KB, GAN_KB

API_TOKEN = "6185039145:AAEXfP0atpaRK9yCDewpjoJ4lTmBf5vcgho"

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
st = Style_transfer()

button_st = KeyboardButton('Style Transfer')
st_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(button_st)


@dp.message_handler(commands=['st'])
async def process_file_command(message: types.Message):
    user_id = str(message.from_user.id)
    if os.path.exists('content' + user_id + '.jpg') == False:
        await bot.send_message(user_id, 'Отсутствует фотография контента')
        return

    if os.path.exists('style' + user_id + '.jpg') == False:
        await bot.send_message(user_id, 'Отсутствует фотография стиля')
        return

    await bot.send_message(user_id, 'Перенос стиля запущен, через некоторое время вы получите результат')
    while st.busy == 1:
        await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
        await asyncio.sleep(2)
    x = threading.Thread(target=st.style_transfer_train,
                         args=('content' + user_id + '.jpg', 'style' + user_id + '.jpg', user_id))
    x.start()  # делаем style transfer
    await st_transfer(user_id)


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply('Бот для переноса стиля готов к работе!\nИспользуй /help, '
                        'чтобы узнать как со мной общаться!', reply_markup=GAN_KB)


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    msg = text('Чтобы всё произошло, отправьте боту картинку со стилем с подписью style',
               'отправьте боту картинку с контентом с подписью content',
               'дайте боту команду /st и через некоторое время вы получите результат', sep='\n')
    await message.reply(msg, parse_mode=types.ParseMode.HTML)


@dp.message_handler()
async def echo(message: types.Message):
    #    # old style:
    #    # await bot.send_message(message.chat.id, message.text)
    #
    #    await message.answer(message.text)
    if message.text == 'Style Transfer':
        user_id = str(message.from_user.id)
        await bot.send_chat_action(message.from_user.id, ChatActions.TYPING)
        await bot.send_message(user_id, 'Перенос стиля запущен, через некоторое время вы получите результат')
        while st.busy == 1:
            await asyncio.sleep(2)
            await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
        x = threading.Thread(target=st.style_transfer_train,
                             args=('content' + user_id + '.jpg', 'style' + user_id + '.jpg', user_id))
        x.start()  # делаем style transfer
        await st_transfer(user_id)


@dp.message_handler(content_types=['photo'])
async def handle_docs_photo(message):
    print(message.caption)
    await message.photo[-1].download(message.caption + str(message.from_user.id) + '.jpg')
    user_id = str(message.from_user.id)
    if os.path.exists('content' + user_id + '.jpg') and os.path.exists('style' + user_id + '.jpg'):
        await message.reply("Стиль и контент получены", reply_markup=st_kb)


async def st_transfer(user_id):
    while st.busy == 1:
        await bot.send_chat_action(user_id, ChatActions.TYPING)
        await asyncio.sleep(2)

    with open('target' + user_id + '.png', 'rb') as photo:
        await bot.send_photo(user_id, photo,
                             caption='Получите и распишитесь!')


if __name__ == '__main__':
    executor.start_polling(dp)