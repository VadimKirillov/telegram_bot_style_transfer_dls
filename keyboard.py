from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

START_KB = ReplyKeyboardMarkup(resize_keyboard=True)
START_KB.add("/help")
START_KB.add("/nst")
START_KB.add("/gan")
START_KB.add("/cancel")

GAN_KB = InlineKeyboardMarkup()
GAN_KB.add(InlineKeyboardButton("Сезанн", callback_data="cezanne"))
GAN_KB.add(InlineKeyboardButton("Моне", callback_data="monet"))
GAN_KB.add(InlineKeyboardButton("Ван Гог", callback_data="vangogh"))