import telebot
import os
import json
import settings

from sqlalchemy.orm import sessionmaker
from models import engine, User, Group

from schedule_repsonse import ScheduleCreator
from markup import keyboard_main

import logging

from core.types.button import create_group_buttons, ActionTypes, BtnTypes
from button_actions import ButtonActions

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

bot = telebot.TeleBot(os.getenv("SCHEDULE_BOT_TOKEN"))
telebot.apihelper.SESSION_TIME_TO_LIVE = 5 * 60

Session = sessionmaker()
Session.configure(bind=engine)


@bot.message_handler(commands=["start"])
def send_welcome(message: telebot.types.Message):
    with open("bot_answers/start.txt", "r", encoding="utf8") as start_text_file:
        start_message = start_text_file.read()
        bot.send_message(
            message.chat.id, start_message,
            reply_markup=keyboard_main
        )


@bot.message_handler(commands=["help"])
def send_help(message: telebot.types.Message):
    with open("bot_answers/help.txt", "r", encoding="utf8") as help_text_file:
        help_message = help_text_file.read()
        bot.send_message(
            message.chat.id,
            help_message,
            reply_markup=keyboard_main
        )


@bot.message_handler(func=lambda message: message.text == "Все расписания" or message.text.startswith("/schedule"))
def handle_schedule(message: telebot.types.Message):
    text = bot.send_message(message.chat.id, "Введи название своей группы, например БИ-2002")
    bot.register_next_step_handler(text, send_schedule)


@bot.message_handler(func=lambda message: message.text == "Выбрать мою группу" or message.text.startswith("/set_group"))
def set_group(message: telebot.types.Message):
    # User.get_user(message.chat.id).set_group()
    groups = Group.get_all()

    markup = create_group_buttons(groups, action=ActionTypes.SET_USER_GROUP)

    bot.send_message(message.chat.id, text="Выбери свою группу", reply_markup=markup)


def send_schedule(message: telebot.types.Message):
    session = Session()
    group_name = message.text

    group = session.query(Group).filter(Group.name == group_name).one_or_none()

    if group:
        group_id = group.id
        send_schedule_handler(message, group_id)
    else:
        bot.send_message(message.chat.id, "Группа не найдена")

    session.close()


def send_schedule_handler(message: telebot.types.Message, group_id: int):
    response_creator = ScheduleCreator(group_id)
    response = response_creator.form_response()
    if response.is_success():
        bot.send_message(message.chat.id, response.text, reply_markup=response.markup, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call: telebot.types.CallbackQuery):
    btn_data = json.loads(call.data)

    callback_btn_type = None
    for btn_type in BtnTypes:
        if btn_type.name == btn_data["type"]:
            callback_btn_type = btn_type

    if callback_btn_type in (BtnTypes.CHANGE_WEEK, BtnTypes.GET_FULL_DAY, BtnTypes.MORE):
        response_creator = ScheduleCreator(group_id=btn_data["group"], week=btn_data["week"])
        response = response_creator.form_on_button_click_response(btn_data, user_id=call.from_user.id)
        if response.is_success():
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  text=response.text,
                                  message_id=call.message.message_id,
                                  reply_markup=response.markup,
                                  parse_mode='HTML')
    elif callback_btn_type == BtnTypes.GROUP_BUTTON:
        ButtonActions.set_group(btn_data["group_id"], call.from_user.id)


@bot.message_handler(func=lambda message: message.text == "Мое расписание" or message.text.startswith("/my_schedule"))
def send_user_schedule(message):
    response = ButtonActions.get_my_schedule(message.chat.id)

    bot.send_message(chat_id=message.chat.id,
                     text=response.text,
                     reply_markup=response.markup,
                     parse_mode='HTML')


@bot.inline_handler(func=lambda query: len(query.query) > 0)
def send_schedule_inline(query):
    inline_response_creator = ScheduleCreator(group_id=12837)
    inline_response = inline_response_creator.form_inline_response()
    if inline_response.is_success():
        bot.answer_inline_query(query.id, inline_response.items)


@bot.message_handler(func=lambda message: True)
def offer_help(message):
    bot.send_message(
        message.chat.id,
        "Кажется такой команды нет, если нужна помощь, нажмите на /help",
        reply_markup=keyboard_main
    )


bot.infinity_polling()
