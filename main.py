import telebot
import os
import json
import settings

from schedule_repsonse import ResponseCreator
from markup import keyboard_main

import logging

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

bot = telebot.TeleBot(os.getenv("SCHEDULE_BOT_TOKEN"))
telebot.apihelper.SESSION_TIME_TO_LIVE = 5 * 60


@bot.message_handler(commands=["start"])
def send_welcome(message):
    with open("bot_answers/start.txt", "r", encoding="utf8") as start_text_file:
        start_message = start_text_file.read()
        bot.send_message(
            message.chat.id, start_message,
            reply_markup=keyboard_main
        )


@bot.message_handler(commands=["help"])
def send_help(message):
    with open("bot_answers/help.txt", "r", encoding="utf8") as help_text_file:
        help_message = help_text_file.read()
        bot.send_message(
            message.chat.id,
            help_message,
            reply_markup=keyboard_main
        )


@bot.message_handler(commands=["schedule"])
def send_schedule(message):
    response_creator = ResponseCreator(group=12837)
    response = response_creator.form_response()
    bot.send_message(message.chat.id, response.message, reply_markup=response.markup, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    btn_data = json.loads(call.data)
    response_creator = ResponseCreator(group=btn_data["group"], week=btn_data["week"])

    response = response_creator.form_on_button_click_response(btn_data)

    bot.edit_message_text(chat_id=call.message.chat.id,
                          text=response.text,
                          message_id=call.message.message_id,
                          reply_markup=response.markup,
                          parse_mode='HTML')


@bot.inline_handler(func=lambda query: len(query.query) > 0)
def send_schedule_inline(query):
    inline_response_creator = ResponseCreator(group=12837)
    inline_response = inline_response_creator.form_inline_response()
    if inline_response.is_success:
        bot.answer_inline_query(query.id, inline_response.items)


bot.infinity_polling()
