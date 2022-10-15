
from telegram import Update
from telegram.ext import ContextTypes

from hktg.constants import State
from hktg import db, warehouse, strings

class AskText:
    @staticmethod
    async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

        user_data = context.user_data['data']

        message = strings.NAME_TEXT

        if update.callback_query:
            await update.callback_query.edit_message_text(text=message)
        else:
            await update.message.reply_text(text=message)

        return State.ENTERING_TEXT

    @staticmethod
    async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

        user_data = context.user_data['data']
        if isinstance(user_data, db.Product):
            user_data.name = update.message.text
            return await warehouse.ViewProduct.ask(update, context)
