"""Language Teacher Bot on Telegram

Using Google APIs, this main script runs a Telegram bot that helps to teach one 
how to speak a language (English in our example).

Usage:
main()

Press Ctrl-C on the command line to stop the bot.
"""

import logging
import html
from functools import wraps

from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters

from google_api import synthesize_text, translate_text, upload_file, transcribe_voice
import ftransc.core as ft
import pykakasi

from config import BOT_TOKEN, BUCKET_NAME, LANGUAGE_CODE, menu_options, TELEGRAM_ID

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def send_typing_action(func):
    """
    Sends typing action while processing func command
    """

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(update, context,  *args, **kwargs)

    return command_func


@send_typing_action
def menu(update, context):
    """
    Send a message when the command /menu is issued
    """
    status = check_id(update)
    if status:
        show_menu(update, context)


def show_menu(update, context):
    """
    Show menu buttons
    """
    keyboard = [
        [InlineKeyboardButton(menu_options['1']['option'], callback_data='1')],
        [InlineKeyboardButton(menu_options['2']['option'], callback_data='2')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Hi! Let's start learning English together :) Select an option below:", reply_markup=reply_markup)


def menu_option(update, context):
    """
    Send follow-up message after menu option is selected
    """
    query = update.callback_query
    context.chat_data['option'] = [query.data]
    query.edit_message_text(text=menu_options[query.data]['reply'])
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()

@send_typing_action
def pronounce(update, context):
    filename = 'pronunciation.mp3'
    synthesize_text(update.message.text[3::], filename)
    send_audio(update, context, filename)

@send_typing_action
def translate(update, context):
    filename = 'pronunciation.mp3'
    translated_text = html.unescape(translate_text(update.message.text[3::]))
    update.message.reply_text(f"\"{update.message.text[3::]}\" translates to \"{translated_text}\".")
    synthesize_text(translated_text, filename)
    send_audio(update, context, filename)

@send_typing_action
def help(update, context):
    """
    Send a message when the command /help is issued
    """
    status = check_id(update)
    if status:
        update.message.reply_text('Type /p <text in English> to get the pronunciation.\n\n Type /t <text in Spanish> to translate from Spanish to English.\n\n Type /menu or /start for more options.')

@send_typing_action
def send_audio(update, context, filename):
    """
    Send an audio message
    """
    if 'message_id' in context.user_data.keys():
        try:
            # delete previous audio message, if any, so that Telegram's auto-play does not drive user crazy
            context.bot.delete_message(chat_id=context.user_data['chat_id'][0], message_id=context.user_data['message_id'][0])
        except Exception as e:
            print(e)
    message = context.bot.send_audio(chat_id=update.effective_message.chat_id, audio=open(filename, 'rb'))
    context.user_data['chat_id'] = [message.chat.id]
    context.user_data['message_id'] = [message.message_id]

def message_reply(update, context):
    """
    Response to normal messages
    """
    status = check_id(update)
    if status:
        filename = 'pronunciation.mp3'
        if 'option' in context.chat_data.keys():
            if context.chat_data['option'][0]=='1':  # option 1 selected in previous step        
                synthesize_text(update.message.text, filename)
                send_audio(update, context, filename)
            #    followup_line = f"""Hope that helps :) \nIs there anything else you would like to do?"""
            #    update.message.reply_text(followup_line)
            #    show_menu(update, context)
                followup_line = f"""Please repeat after me and send your recorded voice over the chat to check if you pronounced it correctly."""
                update.message.reply_text(followup_line)
                context.chat_data['translated_text'] = [update.message.text]
                context.chat_data['filename'] = [filename]
                context.chat_data['option'] = ['']
            elif context.chat_data['option'][0]=='2': # option 2 selected in previous step 
                translated_text = html.unescape(translate_text(update.message.text))
                update.message.reply_text(f"\"{update.message.text}\" translates to \"{translated_text}\".")
                synthesize_text(translated_text, filename)
                send_audio(update, context, filename)
                followup_line = f"""Please repeat after me and send your recorded voice over the chat to check if you pronounced it correctly."""
                update.message.reply_text(followup_line)
                context.chat_data['translated_text'] = [translated_text]
                context.chat_data['text'] = [update.message.text]
                context.chat_data['filename'] = [filename]
                context.chat_data['option'] = ['']

def voice_check(update, context):
    """
    Check user's pronunciations against correct answer
    """
    status = check_id(update)
    if status:
        # Fetch voice message
        voice = context.bot.getFile(update.message.voice.file_id)

        # Transcode the voice message from audio/x-opus+ogg to audio/x-wav
        filename = 'pronunciation' + '_2.ogg'
        ft.transcode(voice.download(filename), 'wav')

        new_filename = filename[:-3] + 'wav'
        upload_file(new_filename, BUCKET_NAME)
        response_text = transcribe_voice(new_filename, BUCKET_NAME)

        if LANGUAGE_CODE=='ja-JP':  # only applicable for Japanese language
            # Convert Japanese to romaji so that comparison against correct answer can be made.
            # E.g., without conversion, delicious may be おいしい or 美味しい
            kks = pykakasi.kakasi()
            correct = ''.join(item['hepburn'] for item in kks.convert(context.chat_data['translated_text'][0]))
            response = ''.join(item['hepburn'] for item in kks.convert(response_text))
        else:
            correct = context.chat_data['translated_text'][0]
            response = response_text

        if response.lower()==correct.lower():
            update.message.reply_text("That's correct! Good job!")
            context.chat_data['option'] = ['']
        else:
            update.message.reply_text(f"Oops! That's not correct. You said \"{response}\". Please try saying \"{correct}\" again.")
            translated_voice_filename = context.chat_data['filename'][0]
            send_audio(update, context, translated_voice_filename)

def error(update, context):
    """Log Errors"""
    logger.warning(f"Update {update} caused error {context.error}")

def check_id(update):
    """
    Check sender's ID is allowed
    """
    verification = False
    id = int(update.message.from_user.id)
    for ID in TELEGRAM_ID:
        if id==ID:
            verification = True
            break
    if not verification:
        update.message.reply_text("Oops! I don't really know you so I cannot talk to you. \n\nSorry about that!")
    print("User allowed:",verification)
    return verification

def main():
    """
    Main function to start the bot
    """
    # Create the Updater and pass it your bot's token.
    updater = Updater(BOT_TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("p", pronounce))
    dp.add_handler(CommandHandler("t", translate))
    dp.add_handler(CommandHandler("menu", menu))
    dp.add_handler(CommandHandler("start", menu))
    dp.add_handler(CallbackQueryHandler(menu_option))
    dp.add_handler(CommandHandler("help", help))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, message_reply))

    # Attach voiemessage handler to dispatcher. Note the filter as we ovly want the voice mesages to be transcribed
    dp.add_handler(MessageHandler(Filters.voice, voice_check))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()