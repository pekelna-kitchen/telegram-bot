
from telegram import Update
from telegram.ext import ContextTypes

import logging

from hktg.constants import (
    Action,
    UserData,
    UserDataKey,
    State
)
from hktg import dbwrapper, util, callbacks
from hktg.strings import FILTERED_VIEW_TEXT, UNFILTERED_TEXT

class ViewWarehouse:
    @staticmethod
    async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        await update.callback_query.answer()

        user_data = context.user_data
        # logging.info( user_data['data'].dict() )

        # def constraint(product, location, amount, container, date, editor):
        #     if user_data[UserDataKey.FIELD_TYPE] == UserDataKey.PRODUCT:
        #         return product == user_data[UserDataKey.CURRENT_ID]
        #     if user_data[UserDataKey.FIELD_TYPE] == UserDataKey.LOCATION:
        #         return location == user_data[UserDataKey.CURRENT_ID]
        #     logging.error("unexpected filter type to filter by")
        #     return True

        buttons = []

        products = dbwrapper.get_table(dbwrapper.Tables.PRODUCT)
        locations = dbwrapper.get_table(dbwrapper.Tables.LOCATION)
        containers = dbwrapper.get_table(dbwrapper.Tables.CONTAINER)

        for product_id, product_sym, product_name, limit_container, limit_amount in products:
            product_info = ""
            for location_id, location_name, location_symbol in locations:
                entries = dbwrapper.get_table(dbwrapper.Tables.ENTRIES, {
                    'product_id': product_id,
                    'location_id': location_id
                })
                if not entries:
                    continue
                location_product_info = ""
                for (id, product, location, amount, container,  date, editor) in entries:
                    entry = dbwrapper.Entry(id, product, location, amount, container, date, editor)
                    location_product_info = " ".join([
                        location_product_info,
                        "%s%s" % (amount, entry.container_symbol(containers))
                    ])
                if location_product_info:
                    product_info += '%s %s [%s]' % (location_symbol, location_name, location_product_info)

            if product_info:
                buttons.append(InlineKeyboardButton(
                    text=" ".join([product_sym, product_name, product_info]),
                    callback_data=dbwrapper.Product(product_id, product_sym, product_name, limit_container, limit_amount)
                ))

        buttons = util.split_list(buttons, 3)

        buttons.append([
            util.action_button(Action.CREATE, dbwrapper.Entry()),
            util.action_button(Action.HOME)])

        keyboard = InlineKeyboardMarkup(buttons)

        await update.callback_query.edit_message_text(text=UNFILTERED_TEXT, reply_markup=keyboard)

        return State.VIEWING_WAREHOUSE

    @staticmethod
    async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

        await update.callback_query.answer()

        qdata = update.callback_query.data

        if isinstance(qdata, dbwrapper.Product):
            context.user_data['data'] = qdata
            return await callbacks.ViewProduct.ask(update, context)

        if isinstance(qdata, dbwrapper.Entry):
            context.user_data['data'] = qdata
            return await callbacks.ViewEntry.ask(update, context)

        if isinstance(qdata, UserData):
            if qdata.action == Action.HOME:
                return await callbacks.Home.ask(update, context)
