import os
import telebot
import yaml

import requests
import json
from schedule import Schedule
from markup import create_change_week_markup, BtnTypes

with open("config.yaml", "r") as cfg_file:
    config = yaml.safe_load(cfg_file)

bot = telebot.TeleBot(config["SCHEDULE_BOT_TOKEN"])

keyboard_main = telebot.types.ReplyKeyboardMarkup(True, True)
keyboard_main.row("/schedule")


@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.send_message(
        message.chat.id, "Привет. Здесь в скором будущем ты сможешь найти расписание для твоей группы СпбГЭУ",
        reply_markup=keyboard_main
    )


@bot.message_handler(commands=["schedule"])
def send_schedule(message):

    page = requests.get(
        "https://rasp.unecon.ru/raspisanie_grp.php", {"g": 12837})

    if page.status_code == 200:
        schedule = Schedule.get_schedule_from_html(page.content)

        current_week = Schedule.get_current_week_number(page.content)

        markup = create_change_week_markup(current_week)

        if schedule:
            schedule_str = Schedule.transform_schedule_to_str(schedule)

            bot.send_message(message.chat.id, schedule_str,
                             parse_mode="HTML", reply_markup=markup)
        else:
            bot.send_message(
                message.chat.id, "На эту неделю нет расписания", reply_markup=keyboard_main)
    else:
        bot.send_message(
            message.chat.id, "К расписанию нет доступа. Попробуйте позже", reply_markup=keyboard_main)


@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    btn_data = json.loads(call.data)

    print(btn_data)

    callback_btn_type = None
    for btn_type in BtnTypes:
        if btn_type.name == btn_data["type"]:
            callback_btn_type = btn_type

    if callback_btn_type == BtnTypes.CHANGE_WEEK:
        week = btn_data["week"]
        page = requests.get("https://rasp.unecon.ru/raspisanie_grp.php?",
                            {"g": 12837, "w": week})

        schedule = Schedule.get_schedule_from_html(page.content)

        markup = create_change_week_markup(week)
        markup.add(telebot.types.InlineKeyboardButton(
            "Больше", callback_data=json.dumps({"type": BtnTypes.MORE.name})))

        if schedule:
            schedule_str = Schedule.transform_schedule_to_str(schedule)

            bot.edit_message_text(chat_id=call.message.chat.id,
                                  text=schedule_str,
                                  message_id=call.message.message_id,
                                  reply_markup=markup,
                                  parse_mode='HTML')
        else:

            bot.edit_message_text(chat_id=call.message.chat.id,
                                  text="На эту неделю нет расписания",
                                  message_id=call.message.message_id,
                                  reply_markup=markup,
                                  parse_mode='HTML')
    elif callback_btn_type == BtnTypes.MORE:
        bot.edit_message_text(chat_id=call.message.chat.id,
                              text="Пока эта конпка ничего не делает",
                              message_id=call.message.message_id,
                              parse_mode='HTML')


bot.polling()
