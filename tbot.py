import logging
import asyncio
from queue import Queue
import time
from typing import Any

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import text, hbold, italic, code, pre
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton, ChatActions, ContentType

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
from keyboard import START_KB, GAN_KB, HELP_KB
from messages import START_MESSAGE, HELP_MESSAGE, ST_MESSAGE, CANCEL_MESSAGE, WAITING_FOR_CONTENT_MESSAGE, \
    GETTING_STYLE_ERROR_MESSAGE, PROCESSING_MESSAGE, GETTING_CONTENT_ERROR_MESSAGE, FINISHED_MESSAGE
from states import ST_States

API_TOKEN = os.environ.get('API_TOKEN')

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
st = Style_transfer()
task_queue = Queue()


# button_st = KeyboardButton('Style Transfer')
# st_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(button_st)
@dp.callback_query_handler(lambda c: c.data == "main_menu")
async def main_menu(callback_query):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_text("Мои возможности:")
    await callback_query.message.edit_reply_markup(reply_markup=START_KB)


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply(START_MESSAGE, reply_markup=START_KB)


@dp.message_handler(commands=["help"])
async def send_help(message):
    await bot.send_message(
        message.from_user.id, HELP_MESSAGE, reply_markup=HELP_KB
    )


# @dp.message_handler(commands=['st1'])
# async def process_file_command(message: types.Message):
#     user_id = str(message.from_user.id)
#     await ST_States.waiting_for_style.set()
#     if os.path.exists('content' + user_id + '.jpg') == False:
#         await bot.send_message(user_id, 'Отсутствует фотография контента')
#         return
#
#     if os.path.exists('style' + user_id + '.jpg') == False:
#         await bot.send_message(user_id, 'Отсутствует фотография стиля')
#         return
#
#     await bot.send_message(user_id, 'Перенос стиля запущен, через некоторое время вы получите результат')
#     while st.busy == 1:
#         await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
#         await asyncio.sleep(2)
#     x = threading.Thread(target=st.style_transfer_train,
#                          args=('content' + user_id + '.jpg', 'style' + user_id + '.jpg', user_id))
#     x.start()  # делаем style transfer
#     await st_transfer(user_id)


@dp.message_handler(commands=["st"])
async def choose_nst_command(message: types.Message):
    await ST_States.waiting_for_style.set()
    await message.answer(ST_MESSAGE)


@dp.message_handler(commands=["cancel"], state="*")
async def cancel_action_command(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.answer(CANCEL_MESSAGE)


@dp.message_handler(state=ST_States.waiting_for_style, content_types=ContentType.ANY)
async def handle_style_input_nst(message: types.message, state: FSMContext):
    if len(message.photo) > 0:
        await state.update_data(style=message.photo[-1])
        await ST_States.waiting_for_content.set()
        await message.answer(WAITING_FOR_CONTENT_MESSAGE)
    else:
        await message.answer(GETTING_STYLE_ERROR_MESSAGE)


@dp.message_handler(state=ST_States.waiting_for_content, content_types=ContentType.ANY)
async def handle_content_input_nst(message: types.message, state: FSMContext):
    if len(message.photo) > 0:
        await message.answer(PROCESSING_MESSAGE)
        data = await state.get_data()
        content = message.photo[-1]
        style = data["style"]

        style_path = f"images/{style.file_id}.jpg"
        content_path = f"images/{content.file_id}.jpg"

        await style.download(destination_file=style_path)
        await content.download(destination_file=content_path)

        task = {"id": message.chat.id, "type": "st",
                "style": style_path, "content": content_path,
                "loop": asyncio.get_event_loop()}
        task_queue.put(task)

        await state.finish()
    else:
        await message.answer(GETTING_CONTENT_ERROR_MESSAGE)


@dp.message_handler(content_types=["text"])
async def get_text(message):
    await bot.send_message(
        message.chat.id,
        "Я не понимаю. Мои возможности:",
        reply_markup=HELP_KB,
    )


# @dp.message_handler()
# async def echo(message: types.Message):
#     #    # old style:
#     #    # await bot.send_message(message.chat.id, message.text)
#     #
#     #    await message.answer(message.text)
#     if message.text == 'Style Transfer':
#         user_id = str(message.from_user.id)
#         await bot.send_chat_action(message.from_user.id, ChatActions.TYPING)
#         await bot.send_message(user_id, 'Перенос стиля запущен, через некоторое время вы получите результат')
#         while st.busy == 1:
#             await asyncio.sleep(2)
#             await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
#         x = threading.Thread(target=st.style_transfer_train,
#                              args=('content' + user_id + '.jpg', 'style' + user_id + '.jpg', user_id))
#         x.start()  # делаем style transfer
#         await st_transfer(user_id)
#
#
# @dp.message_handler(content_types=['photo'])
# async def handle_docs_photo(message):
#     print(message.caption)
#     await message.photo[-1].download(message.caption + str(message.from_user.id) + '.jpg')
#     user_id = str(message.from_user.id)
#     if os.path.exists('content' + user_id + '.jpg') and os.path.exists('style' + user_id + '.jpg'):
#         await message.reply("Стиль и контент получены")
#
#
# async def st_transfer(user_id):
#     while st.busy == 1:
#         await bot.send_chat_action(user_id, ChatActions.TYPING)
#         await asyncio.sleep(2)
#
#     with open('target' + user_id + '.png', 'rb') as photo:
#         await bot.send_photo(user_id, photo,
#                              caption='Получите и распишитесь!')


async def send_result(chat_id):
    # await bot.send_photo(chat_id, open("images/result/res.jpg", "rb"), FINISHED_MESSAGE)
    await bot.send_message(chat_id, FINISHED_MESSAGE)


def queue_loop():
    while True:
        if not task_queue.empty():
            task = task_queue.get()
            if task["type"] == "st":
                time.sleep(5)
                print(1)
                # nst.run(task["style"], task["content"])
            else:
                print(2)
                # gan.run(task["model"], task["content"])
            asyncio.run_coroutine_threadsafe(send_result(task["id"]), task["loop"]).result()
            task_queue.task_done()
        time.sleep(2)


if __name__ == '__main__':
    image_processing_thread = threading.Thread(target=queue_loop, args=())
    image_processing_thread.start()

    executor.start_polling(dp)
