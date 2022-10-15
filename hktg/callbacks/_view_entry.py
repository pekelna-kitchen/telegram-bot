
from telegram import Update
from telegram.ext import ContextTypes
from dataclasses import dataclass

import humanize
from enum import Enum
from datetime import datetime

from hktg.constants import (
    Action,
    UserData,
    State
)
from hktg import dbwrapper, util, callbacks
from hktg.strings import ENTRY_MESSAGE

def create_button(text, callback_data):
    from telegram import InlineKeyboardButton
    if not text:
        text = "➕"
    return InlineKeyboardButton(text, callback_data=callback_data)


@dataclass
class ViewEntry:

    class FieldType(Enum):
        Product = 1,
        Location = 2,
        Amount = 3,
        Container = 4,

    field_type : FieldType | None = None

    @staticmethod
    async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:

        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        # query_data = update.callback_query.data

        entry : dbwrapper.Entry = None
        if isinstance(context.user_data['data'], dbwrapper.Entry):
            entry = context.user_data['data']

        buttons = []
        # if not product_info.id:
        buttons.append([
            create_button(entry.product_symbol(), ViewEntry(ViewEntry.FieldType.Product)),
            create_button(entry.location_symbol(), ViewEntry(ViewEntry.FieldType.Location)),
            create_button(entry.amount, ViewEntry(ViewEntry.FieldType.Amount)),
            create_button(entry.container_symbol(), ViewEntry(ViewEntry.FieldType.Container)),
        ])
        # else:
        if entry.id:
            entries = dbwrapper.get_table(dbwrapper.Tables.ENTRIES)
            result_entry = util.find_tuple_element(entries, {0: entry.id})
            entry_id, product_id, location_id, amount, container_id, date, editor = result_entry
            origin = dbwrapper.Entry(entry_id, product_id, location_id, amount, container_id, date, editor)
            if not origin == entry:
                buttons.append([ util.action_button(Action.MODIFY) ])
        elif entry.is_valid():
            buttons.append([ util.action_button(Action.CREATE) ])


        buttons.append([
            util.action_button(Action.BACK),
        ])
        keyboard = InlineKeyboardMarkup(buttons)

        editor_tuple = (entry.editor, humanize.naturaltime(entry.date.replace(tzinfo=None))) if entry.editor else ('ніхто', 'ніколи')

        if update.callback_query:
            await update.callback_query.edit_message_text(text=ENTRY_MESSAGE % editor_tuple, reply_markup=keyboard)
        else:
            await update.message.reply_text(text=ENTRY_MESSAGE % editor_tuple, reply_markup=keyboard)

        return State.VIEWING_ENTRY

    @staticmethod
    async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

        await update.callback_query.answer()

        query_data = update.callback_query.data
        user_data = context.user_data['data']

        if isinstance(query_data, UserData):
            if query_data.action == Action.BACK:
                return await callbacks.ViewWarehouse.ask(update, context)

            entry_data : dbwrapper.Entry = context.user_data['data']
            datadict = entry_data.to_sql()

            if query_data.action == Action.MODIFY:
                dbwrapper.update_entry(user_data.id, update.effective_user.name, datadict)
            if query_data.action == Action.CREATE:
                dbwrapper.insert_value(dbwrapper.Tables.ENTRIES, datadict)

            del context.user_data['data']
            return await callbacks.ViewWarehouse.ask(update, context)

        # if user_data[UserDataKey.ACTION] == Action.BACK:
        #     return ConversationHandler.END

        # async def create(u, c):
        #     dbwrapper.update_entry(None, update.effective_user.name, {
        #         "product_id": user_data[UserDataKey.PRODUCT],
        #         "location_id": user_data[UserDataKey.LOCATION],
        #         "container_id": user_data[UserDataKey.CONTAINER],
        #         "amount": update.message.text,
        #     })
        #     util.reset_data(context)
        #     return await callbacks.ViewWarehouse.ask(update, context)

        if isinstance(query_data, ViewEntry):
            if query_data.field_type == ViewEntry.FieldType.Product:
                return await callbacks.SelectProduct.ask(update, context)
            if query_data.field_type == ViewEntry.FieldType.Location:
                return await callbacks.SelectLocation.ask(update, context)
            if query_data.field_type == ViewEntry.FieldType.Amount:
                return await callbacks.AskAmount.ask(update, context)
            if query_data.field_type == ViewEntry.FieldType.Container:
                return await callbacks.SelectContainer.ask(update, context)
