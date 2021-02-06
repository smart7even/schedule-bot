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
        markup.add(telebot.types.InlineKeyboardButton(
            "Больше", callback_data=json.dumps({"type": BtnTypes.MORE.name})))

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
    week = btn_data["week"]

    print(btn_data)

    callback_btn_type = None
    for btn_type in BtnTypes:
        if btn_type.name == btn_data["type"]:
            callback_btn_type = btn_type

    schedule = None
    if callback_btn_type in (BtnTypes.CHANGE_WEEK, BtnTypes.MORE, BtnTypes.GET_FULL_DAY):
        page = requests.get("https://rasp.unecon.ru/raspisanie_grp.php?",
                            {"g": 12837, "w": week})
        schedule = Schedule.get_schedule_from_html(page.content)

    if callback_btn_type == BtnTypes.CHANGE_WEEK:
        markup = create_change_week_markup(week)
        markup.add(telebot.types.InlineKeyboardButton(
            "Больше", callback_data=json.dumps({"type": BtnTypes.MORE.name, "group": 12837, "week": week})))

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
        if schedule:
            markup = create_change_week_markup(week)
            day = None
            day_count = 0
            for lesson in schedule:
                if day != lesson.day:
                    day = lesson.day
                    day_count += 1
                    markup.add(
                        telebot.types.InlineKeyboardButton(
                            day,
                            callback_data=json.dumps(
                                {
                                    "type": BtnTypes.GET_FULL_DAY.name,
                                    "group": 12837,
                                    "week": week,
                                    "day": day_count
                                })
                        )
                    )

            schedule_str = Schedule.transform_schedule_to_str(schedule)
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  text=schedule_str,
                                  message_id=call.message.message_id,
                                  reply_markup=markup,
                                  parse_mode='HTML')
    elif callback_btn_type == BtnTypes.GET_FULL_DAY:
        if schedule:
            lessons_at_this_day = Schedule.get_info_about_day(schedule, btn_data["day"])
            lessons_str = Schedule.transform_schedule_to_str(lessons_at_this_day, is_detail_mode=True)
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(
                telebot.types.InlineKeyboardButton(
                    "Назад к расписанию недели",
                    callback_data=json.dumps(
                        {
                            "type": BtnTypes.CHANGE_WEEK.name,
                            "group": btn_data["group"],
                            "week": btn_data["week"]
                        })
                )
            )
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  text=lessons_str,
                                  message_id=call.message.message_id,
                                  reply_markup=markup,
                                  parse_mode='HTML')


@bot.inline_handler(func=lambda query: len(query.query) > 0)
def query_text(query):
    page = requests.get(
        "https://rasp.unecon.ru/raspisanie_grp.php", {"g": 12837})

    if page.status_code == 200:
        schedule = Schedule.get_schedule_from_html(page.content)
        if schedule:
            schedule_str = Schedule.transform_schedule_to_str(schedule)
            this_week = telebot.types.InlineQueryResultArticle(
                id="1",
                title="Расписание на эту неделю",
                input_message_content=telebot.types.InputTextMessageContent(
                    message_text=schedule_str,
                    parse_mode="HTML"
                )
            )
            current_week_number = Schedule.get_current_week_number(page.content)
            next_week_page = requests.get(
                "https://rasp.unecon.ru/raspisanie_grp.php", {"g": 12837, "w": current_week_number+1})
            next_week_schedule = Schedule.get_schedule_from_html(next_week_page.content)
            next_week_schedule_str = Schedule.transform_schedule_to_str(next_week_schedule)
            next_week = telebot.types.InlineQueryResultArticle(
                id="2",
                title="Расписание на следующую неделю",
                input_message_content=telebot.types.InputTextMessageContent(
                    message_text=next_week_schedule_str,
                    parse_mode="HTML"
                )
            )
            bot.answer_inline_query(query.id, [this_week, next_week])


bot.polling()
