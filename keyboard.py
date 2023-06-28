from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

START_KB = ReplyKeyboardMarkup(resize_keyboard=True)
START_KB.add("/start")
START_KB.add("/st")
START_KB.add("/help")
START_KB.add("/cancel")


HELP_KB = InlineKeyboardMarkup()
HELP_KB.add(
    InlineKeyboardButton("Перенос одного стиля (NST)", callback_data="/start")
)
HELP_KB.add(
    InlineKeyboardButton("Стиль Моне (GAN)", callback_data="photo2monet")
)
GAN_KB = InlineKeyboardMarkup()
GAN_KB.add(InlineKeyboardButton("Сезанн", callback_data="cezanne"))
GAN_KB.add(InlineKeyboardButton("Моне", callback_data="monet"))
GAN_KB.add(InlineKeyboardButton("Ван Гог", callback_data="vangogh"))