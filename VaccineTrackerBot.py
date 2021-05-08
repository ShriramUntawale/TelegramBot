#!/usr/bin/env python
# pylint: disable=C0116
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import requests
import json
import pandas as pd
from telegram import *
from telegram.ext import *
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

GENDER, LOCATION, BIO = range(3)


def start(update: Update, _: CallbackContext) -> int:
    reply_keyboard = [['PinCode', 'District']]

    update.message.reply_text(
        'Hi! My name is Professor Bot. I will hold a conversation with you. '
        'Send /cancel to stop talking to me.\n\n'
        'How do you want to search the vaccination center?',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

    return GENDER


def gender(update: Update, _: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User choice is %s: %s", user.first_name, update.message.text)
    update.message.reply_text(
        'I see! Please send me pincode of your place, '
        'so I know what you are looking for, or send /skip if you don\'t want to.',
        reply_markup=ReplyKeyboardRemove(),
    )

    return LOCATION

def location(update: Update, _: CallbackContext) -> int:
    user = update.message.from_user
    user_location = update.message.text
    logger.info(
        "Location of %s: %s", user.first_name, user_location
    )
    
    url = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByPin"
    payload={}
    parameters ={'pincode':user_location ,'date':'06-05-2021'}
    headers = {
	  'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36'
	}

    response = requests.request("GET", url, headers=headers, data=payload,params= parameters)
    response_api_data=json.loads(response.text)
    df =pd.json_normalize(response_api_data['centers'],meta=['name','address','fee_type'])
    print(df.head())
    update.message.reply_text(
         response_api_data
    )

    return BIO


def skip_location(update: Update, _: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s did not send a location.", user.first_name)
    update.message.reply_text(
        'You seem a bit paranoid! At last, tell me something about yourself.'
    )

    return BIO


def bio(update: Update, _: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("Bio of %s: %s", user.first_name, update.message.text)
    update.message.reply_text('Thank you! I hope we can talk again some day.')

    return ConversationHandler.END


def cancel(update: Update, _: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main() -> None:
    # Create the Updater and pass it your bot's token.
    updater = Updater("Token")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            GENDER: [MessageHandler(Filters.regex('^(PinCode|District)$'), gender)],
            LOCATION: [
                MessageHandler(Filters.text, location),
                CommandHandler('skip', skip_location),
            ],
            BIO: [MessageHandler(Filters.text & ~Filters.command, bio)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
