from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

START_KB = ReplyKeyboardMarkup(resize_keyboard=True)
START_KB.add("/nst")
START_KB.add("/styles")
START_KB.add("/help")
START_KB.add("/cancel")


HELP_KB = InlineKeyboardMarkup()
HELP_KB.add(
    InlineKeyboardButton("Перенос своего стиля", callback_data="nst")
)
HELP_KB.add(
    InlineKeyboardButton("Готовые стили", callback_data="style")
)


PICK_STYLE_KB = InlineKeyboardMarkup()
PICK_STYLE_KB.add(InlineKeyboardButton("1) Дали", callback_data="1"))
PICK_STYLE_KB.add(InlineKeyboardButton("2) Матисс", callback_data="2"))
PICK_STYLE_KB.add(InlineKeyboardButton("3) Пикассо", callback_data="3"))
PICK_STYLE_KB.add(InlineKeyboardButton("4) Ван Гог", callback_data="4"))
