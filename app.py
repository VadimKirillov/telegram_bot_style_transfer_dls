import logging
import asyncio
from queue import Queue
import time
import cv2

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import ChatActions, ContentType

import threading
import os

from models import nst
from models.StyleLoss import Style_transfer
from bot_components.keyboard import START_KB, HELP_KB, PICK_STYLE_KB
from bot_components.messages import START_MESSAGE, HELP_MESSAGE, ST_MESSAGE, CANCEL_MESSAGE, WAITING_FOR_CONTENT_MESSAGE, \
    GETTING_STYLE_ERROR_MESSAGE, PROCESSING_MESSAGE, GETTING_CONTENT_ERROR_MESSAGE, FINISHED_MESSAGE, \
    STANDART_STYLE_MESSAGE
from bot_components.states import ST_States, Standart_Styles_States

API_TOKEN = os.environ.get('API_TOKEN')

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
st = Style_transfer()
task_queue = Queue()


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


@dp.message_handler(commands=["transfer_style"], state="*")
async def choose_nst_command(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await ST_States.waiting_for_style.set()
    await message.answer(ST_MESSAGE)


@dp.callback_query_handler(lambda c: c.data == "transfer_style")
async def choose_button_nst_command(call: types.CallbackQuery):

    await ST_States.waiting_for_style.set()
    await bot.send_message(call.message.chat.id, ST_MESSAGE)


@dp.message_handler(commands=["styles"])
async def choose_style_command(message: types.Message):
    media = types.MediaGroup()
    media.attach_photo(types.InputFile('standart_styles/calzado.png'), '1')
    media.attach_photo(types.InputFile('standart_styles/matiss.png'), '2')
    media.attach_photo(types.InputFile('standart_styles/picasso.png'), '3')
    media.attach_photo(types.InputFile('standart_styles/van_gog.png'), '4')

    await bot.send_media_group(message.chat.id, media=media)
    await message.answer(STANDART_STYLE_MESSAGE, reply_markup=PICK_STYLE_KB)
    await Standart_Styles_States.waiting_for_style.set()


@dp.callback_query_handler(lambda c: c.data == "style")
async def choose_button_style_command(call: types.CallbackQuery):
    media = types.MediaGroup()
    media.attach_photo(types.InputFile('standart_styles/calzado.png'), '1')
    media.attach_photo(types.InputFile('standart_styles/matiss.png'), '2')
    media.attach_photo(types.InputFile('standart_styles/picasso.png'), '3')
    media.attach_photo(types.InputFile('standart_styles/van_gog.png'), '4')

    await bot.send_media_group(call.message.chat.id, media=media)
    await call.message.answer(STANDART_STYLE_MESSAGE, reply_markup=PICK_STYLE_KB)
    await Standart_Styles_States.waiting_for_style.set()


@dp.message_handler(commands=["cancel"], state="*")
async def cancel_action_command(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.answer(CANCEL_MESSAGE)


@dp.callback_query_handler(lambda c: c.data == "1", state=Standart_Styles_States.waiting_for_style)
async def process_callback_calzado(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await Standart_Styles_States.waiting_for_content.set()
    await bot.send_message(callback_query.from_user.id, "Вы выбрали стиль Кальзадо.\nЖду изображение.")
    await state.update_data(model="style_calzado")


@dp.callback_query_handler(lambda c: c.data == "2", state=Standart_Styles_States.waiting_for_style)
async def process_callback_matiss(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await Standart_Styles_States.waiting_for_content.set()
    await bot.send_message(callback_query.from_user.id, "Вы выбрали стиль Матисса.\nЖду изображение.")
    await state.update_data(model="style_matiss")


@dp.callback_query_handler(lambda c: c.data == "3", state=Standart_Styles_States.waiting_for_style)
async def process_callback_picasso(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await Standart_Styles_States.waiting_for_content.set()
    await bot.send_message(callback_query.from_user.id, "Вы выбрали стиль Пикассо.\nЖду изображение.")
    await state.update_data(model="style_picasso")


@dp.callback_query_handler(lambda c: c.data == "4", state=Standart_Styles_States.waiting_for_style)
async def process_callback_van_gog(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await Standart_Styles_States.waiting_for_content.set()
    await bot.send_message(callback_query.from_user.id, "Вы выбрали стиль Ван Гога.\nЖду изображение.")
    await state.update_data(model="style_van_gog")


@dp.message_handler(state=Standart_Styles_States.waiting_for_content, content_types=ContentType.ANY)
async def handle_content_input_standart_style(message: types.message, state: FSMContext):
    if len(message.photo) > 0:
        await message.answer(PROCESSING_MESSAGE)
        data = await state.get_data()
        content = message.photo[-1]

        style = data["model"]
        if style == "style_calzado":
            style_path = f"standart_styles/calzado.png"
        elif style == "style_matiss":
            style_path = f"standart_styles/matiss.png"
        elif style == "style_picasso":
            style_path = f"standart_styles/picasso.png"
        elif style == "style_van_gog":
            style_path = f"standart_styles/van_gog.png"
        else:
            style_path = f"standart_styles/van_gog.png"

        img_24bit = cv2.imread(style_path)
        cv2.imwrite(f"images/style/{message.chat.id}.png", img_24bit)

        style_path = f"images/style/{message.chat.id}.png"
        content_path = f"images/content/{content.file_id}.png"

        await content.download(destination_file=content_path)

        task = {"id": message.chat.id, "type": "st",
                "style": style_path, "content": content_path,
                "loop": asyncio.get_event_loop()}
        task_queue.put(task)

        await state.finish()
        await bot.send_chat_action(message.chat.id, ChatActions.TYPING)

    else:
        await message.answer(GETTING_CONTENT_ERROR_MESSAGE)


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

        style_path = f"images/style/{style.file_id}.png"
        content_path = f"images/content/{content.file_id}.png"

        await style.download(destination_file=style_path)
        await content.download(destination_file=content_path)

        task = {"id": message.chat.id, "type": "st",
                "style": style_path, "content": content_path,
                "loop": asyncio.get_event_loop()}
        task_queue.put(task)

        await state.finish()
        await bot.send_chat_action(message.chat.id, ChatActions.TYPING)



    else:
        await message.answer(GETTING_CONTENT_ERROR_MESSAGE)


@dp.message_handler(content_types=["text"])
async def get_text(message):
    await bot.send_message(
        message.chat.id,
        "Я не понимаю. Мои возможности:",
        reply_markup=HELP_KB,
    )


async def send_result(chat_id):
    await bot.send_photo(chat_id, open("images/target/res.jpg", "rb"), FINISHED_MESSAGE)


def queue_loop():
    while True:
        if not task_queue.empty():
            task = task_queue.get()
            if task["type"] == "st":
                # x = threading.Thread(target=st.style_transfer_train,
                # args=(task["content"], task["style"], task["id"]))
                # x.start()  # делаем style transfer
                while st.busy == 1:
                    time.sleep(2)

                nst.run(task["style"], task["content"])
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
