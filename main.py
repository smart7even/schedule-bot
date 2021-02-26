import os
import json
import settings
from button_actions import ButtonActions
from button_handlers import handle_set_group_btn, handle_get_schedule_btn, handle_faculty_btn, handle_course_btn, \
    handle_schedule_btns
from core.types.response import DefaultResponse

from schedule_repsonse import ScheduleCreator

from markup import keyboard_main

from telegram import Update
from telegram.ext import (
    Updater,
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    CallbackQueryHandler,
    InlineQueryHandler
)

from core.types.button import ActionTypes, BtnTypes


def send_welcome(update: Update, context: CallbackContext):
    with open("bot_answers/start.txt", "r", encoding="utf8") as start_text_file:
        start_message = start_text_file.read()

        update.message.reply_text(start_message, reply_markup=keyboard_main)

    send_help(update, context)


def send_help(update: Update, context: CallbackContext):
    with open("bot_answers/help.txt", "r", encoding="utf8") as help_text_file:
        help_message = help_text_file.read()

        update.message.reply_text(help_message, reply_markup=keyboard_main)


def offer_help(update: Update, context: CallbackContext):
    update.message.reply_text("Кажется, такой команды нет. Если нужна помощь, то нажми на /help")


def handle_schedule_menu(update: Update, context: CallbackContext):
    response = DefaultResponse()
    response.text = "Выберите факультет"
    response.markup = ButtonActions.get_faculties_choice_form(ActionTypes.GET_SCHEDULE)

    update.message.reply_text(text=response.text, reply_markup=response.markup)


def set_group(update: Update, context: CallbackContext):
    markup = ButtonActions.get_faculties_choice_form(ActionTypes.SET_USER_GROUP)

    update.message.reply_text(text="Выберите факультет", reply_markup=markup)


def handle_buttons(update: Update, context: CallbackContext):
    query = update.callback_query

    btn_data: dict = json.loads(query.data)

    callback_btn_type = None
    for btn_type in BtnTypes:
        if btn_type.name == btn_data["type"]:
            callback_btn_type = btn_type

    callback_action_type = None
    if "action" in btn_data:
        for action_type in ActionTypes:
            if action_type.value == btn_data["action"]:
                callback_action_type = action_type

    if callback_btn_type in (BtnTypes.CHANGE_WEEK, BtnTypes.GET_FULL_DAY, BtnTypes.MORE):
        day = btn_data.get("day")

        response = handle_schedule_btns(callback_btn_type, btn_data["group"], btn_data["week"], day)
        if response.is_valid():
            query.edit_message_text(text=response.text, reply_markup=response.markup, parse_mode='HTML')

    elif callback_btn_type == BtnTypes.GROUP_BTN:
        if callback_action_type == ActionTypes.SET_USER_GROUP:
            response = handle_set_group_btn(btn_data["group_id"], user_id=query.from_user.id)
            query.answer(text=response.text)
        elif callback_action_type == ActionTypes.GET_SCHEDULE:
            response = handle_get_schedule_btn(btn_data["group_id"])
            if response.is_valid():
                query.edit_message_text(text=response.text, reply_markup=response.markup, parse_mode="html")
            else:
                query.edit_message_text(text="Похоже на эту неделю нет расписания", reply_markup=response.markup)

    elif callback_btn_type == BtnTypes.FACULTY_BTN:
        response = handle_faculty_btn(callback_action_type, faculty_id=btn_data["f_id"])
        if response.is_valid():
            query.edit_message_text(text=response.text, reply_markup=response.markup)

    elif callback_btn_type == BtnTypes.COURSE_BTN:
        response = handle_course_btn(callback_action_type, faculty_id=btn_data["f_id"], course=btn_data["c_id"])

        query.edit_message_text(text=response.text, reply_markup=response.markup, parse_mode="html")
    query.answer()


def send_user_schedule(update: Update, context: CallbackContext):
    response = ButtonActions.get_user_schedule(update.message.from_user.id)

    if not response.is_valid():
        response.text = "Вы не выбрали группу. Нажмите на /set_group и выберите свою группу"

    update.message.reply_text(
        text=response.text,
        reply_markup=response.markup,
        parse_mode='HTML'
    )


def send_schedule_inline(update: Update, context: CallbackContext):
    inline_response_creator = ScheduleCreator(group_id=12837)
    inline_response = inline_response_creator.form_inline_response()
    if inline_response.is_valid():
        update.inline_query.answer(inline_response.items)


def main():
    updater = Updater(os.getenv("SCHEDULE_BOT_TOKEN"))

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", send_welcome))
    dispatcher.add_handler(CommandHandler("help", send_help))

    dispatcher.add_handler(CommandHandler("set_group", set_group))
    dispatcher.add_handler(MessageHandler(Filters.regex('Выбрать мою группу'), set_group))

    dispatcher.add_handler(CommandHandler("schedule", handle_schedule_menu))
    dispatcher.add_handler(MessageHandler(Filters.regex("Все расписания"), handle_schedule_menu))

    dispatcher.add_handler(CommandHandler("my_schedule", send_user_schedule))
    dispatcher.add_handler(MessageHandler(Filters.regex('Мое расписание'), send_user_schedule))

    dispatcher.add_handler(CallbackQueryHandler(handle_buttons))

    dispatcher.add_handler(InlineQueryHandler(send_schedule_inline))
    dispatcher.add_handler(MessageHandler(Filters.text, offer_help))

    updater.start_polling()


if __name__ == "__main__":
    main()
