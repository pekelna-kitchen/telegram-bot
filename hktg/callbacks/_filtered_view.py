
from telegram import Update
from telegram.ext import ContextTypes

from hktg.constants import (
    Action,
    UserDataKey,
    State
)
from hktg import dbwrapper, util, callbacks
from hktg.strings import FILTERED_VIEW_TEXT

class FilteredView:
    @staticmethod
    async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        await update.callback_query.answer()

        user_data = context.user_data

        def constraint(product, location, amount, container, date, editor):
            if user_data[UserDataKey.FIELD_TYPE] == UserDataKey.PRODUCT:
                return product == user_data[UserDataKey.CURRENT_ID]
            if user_data[UserDataKey.FIELD_TYPE] == UserDataKey.LOCATION:
                return location == user_data[UserDataKey.CURRENT_ID]
            logging.error("unexpected filter type to filter by")
            return True

        buttons = []

        instances = dbwrapper.get_table(dbwrapper.Tables.INSTANCE)
        for (id, product, location, amount, container,  date, editor) in instances:
            if UserDataKey.FIELD_TYPE in user_data:
                if not constraint(product, location, amount, container, date, editor):
                    continue

            location_str = str(util.find_in_table(dbwrapper.Tables.LOCATION, 0, location)[1])
            product_str = str(util.find_in_table(dbwrapper.Tables.PRODUCT, 0, product)[1])
            container_str = str(util.find_in_table(dbwrapper.Tables.CONTAINER, 0, container)[1])

            buttons.append(InlineKeyboardButton(text=" ".join([location_str, product_str, str(amount), container_str]), callback_data={
                UserDataKey.ACTION: Action.VIEW_ENTRY,
                UserDataKey.CURRENT_ID: id
            }))
        buttons = util.split_list(buttons, 2)

        buttons.append([util.action_button(Action.MODIFY), util.action_button(Action.HOME)])

        keyboard = InlineKeyboardMarkup(buttons)

        message = "Ось що є:"
        if UserDataKey.FIELD_TYPE in user_data:
            if user_data[UserDataKey.FIELD_TYPE] == UserDataKey.PRODUCT:
                product_str = util.find_in_table(
                    dbwrapper.PRODUCT, 0, user_data[UserDataKey.CURRENT_ID])[1]
                message = FILTERED_VIEW_TEXT % product_str

            elif user_data[UserDataKey.FIELD_TYPE] == UserDataKey.LOCATION:
                location_str = util.find_in_table(dbwrapper.Tables.LOCATION, 0, user_data[UserDataKey.CURRENT_ID])[1]
                message = FILTERED_VIEW_TEXT % location_str

        await update.callback_query.edit_message_text(text=message, reply_markup=keyboard)

        return State.FILTERED_VIEW

    @staticmethod
    async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

        await update.callback_query.answer()
    
        query_data = update.callback_query.data
        for key in query_data:
            context.user_data[key] = query_data[key]

        if query_data[UserDataKey.ACTION] == Action.FILTER:
            return await callbacks.FilteredView.ask(update, context)

        elif query_data[UserDataKey.ACTION] == Action.CREATE:
            return await callbacks.SelectContainer.ask(update, context)

        elif query_data[UserDataKey.ACTION] == Action.VIEW_ENTRY:
            return await callbacks.ViewEntry.ask(update, context)

        return await callbacks.Home.ask(update, context)
