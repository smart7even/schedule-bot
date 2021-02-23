import os
import json
import settings
from button_actions import ButtonActions
from core.types.response import DefaultResponse

from models import Group, Session
from schedule_repsonse import ScheduleCreator

from markup import keyboard_main

from telegram import Update
from telegram.ext import (
    Updater,
    CallbackContext,
    CommandHandler,
    ConversationHandler,
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


def send_help(update: Update, context: CallbackContext):
    with open("bot_answers/help.txt", "r", encoding="utf8") as help_text_file:
        help_message = help_text_file.read()

        update.message.reply_text(help_message, reply_markup=keyboard_main)


def offer_help(update: Update, context: CallbackContext):
    update.message.reply_text("Кажется, такой команды нет. Если нужна помощь, то нажми на /help")


def handle_schedule(update: Update, context: CallbackContext):
    update.message.reply_text("Введи название своей группы, например, БИ-2002")

    return 1


def handle_schedule_menu(update: Update, context: CallbackContext):
    response = DefaultResponse()
    response.text = "Выберите факультет"
    response.markup = ButtonActions.get_faculties_choice_form(ActionTypes.GET_SCHEDULE)

    update.message.reply_text(text=response.text, reply_markup=response.markup)


def set_group(update: Update, context: CallbackContext):
    markup = ButtonActions.get_faculties_choice_form(ActionTypes.SET_USER_GROUP)

    update.message.reply_text(text="Выбери факультет", reply_markup=markup)


def send_schedule(update: Update, context: CallbackContext):
    session = Session()
    group_name = update.message.text

    group = session.query(Group).filter(Group.name == group_name).one_or_none()

    if group:
        group_id = group.id
        response_creator = ScheduleCreator(group_id)
        response = response_creator.form_response(group_name)
        if response.is_success():
            update.message.reply_text(response.text, reply_markup=response.markup, parse_mode="HTML")
    else:
        update.message.reply_text("Группа не найдена")

    session.close()

    return ConversationHandler.END


def handle_buttons(update: Update, context: CallbackContext):
    query = update.callback_query

    btn_data = json.loads(query.data)

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
        response_creator = ScheduleCreator(group_id=btn_data["group"], week=btn_data["week"])
        response = response_creator.form_on_button_click_response(btn_data)
        if response.is_success():
            query.edit_message_text(text=response.text, reply_markup=response.markup, parse_mode='HTML')
    elif callback_btn_type == BtnTypes.GROUP_BTN:

        if callback_action_type == ActionTypes.SET_USER_GROUP:
            response = ButtonActions.set_group(btn_data["group_id"], query.from_user.id)
            query.answer(text=f"Группа {response.text} установлена!")
        elif callback_action_type == ActionTypes.GET_SCHEDULE:
            response = ButtonActions.get_schedule(btn_data["group_id"])
            if response.is_success():
                query.edit_message_text(text=response.text, reply_markup=response.markup, parse_mode="html")
            else:
                query.edit_message_text(text="Похоже на эту неделю нет расписания", reply_markup=response.markup)
    elif callback_btn_type == BtnTypes.FACULTY_BTN:
        response = DefaultResponse()
        response.markup = ButtonActions.get_courses_choice_form(btn_data["f_id"], callback_action_type)
        response.text = "Выберите курс"

        query.edit_message_text(text=response.text, reply_markup=response.markup)
    elif callback_btn_type == BtnTypes.COURSE_BTN:

        response = DefaultResponse()
        response.markup = ButtonActions.get_group_choice_form(btn_data["f_id"], btn_data["c_id"], callback_action_type)
        response.text = "Выберите группу"

        query.edit_message_text(text=response.text, reply_markup=response.markup, parse_mode="html")
    query.answer()


def send_user_schedule(update: Update, context: CallbackContext):
    response = ButtonActions.get_user_schedule(update.message.from_user.id)

    update.message.reply_text(
        text=response.text,
        reply_markup=response.markup,
        parse_mode='HTML'
    )


def send_schedule_inline(update: Update, context: CallbackContext):
    inline_response_creator = ScheduleCreator(group_id=12837)
    inline_response = inline_response_creator.form_inline_response()
    if inline_response.is_success():
        update.inline_query.answer(inline_response.items)


def main():
    updater = Updater(os.getenv("SCHEDULE_BOT_TOKEN"))

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", send_welcome))
    dispatcher.add_handler(CommandHandler("help", send_help))

    dispatcher.add_handler(CommandHandler("set_group", set_group))
    dispatcher.add_handler(MessageHandler(Filters.regex('Выбрать мою группу'), set_group))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('schedule', handle_schedule)],
        states={
            1: [
                MessageHandler(Filters.text, send_schedule)
            ]
        },
        fallbacks=[]
    )

    dispatcher.add_handler(MessageHandler(Filters.regex("Все расписания"), handle_schedule_menu))
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CallbackQueryHandler(handle_buttons))
    dispatcher.add_handler(CommandHandler("my_schedule", send_user_schedule))
    dispatcher.add_handler(MessageHandler(Filters.regex('Мое расписание'), send_user_schedule))
    dispatcher.add_handler(InlineQueryHandler(send_schedule_inline))
    dispatcher.add_handler(MessageHandler(Filters.text, offer_help))

    updater.start_polling()


if __name__ == "__main__":
    main()
