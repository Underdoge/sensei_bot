# Telegram bot token
BOT_TOKEN = "5952679331:AAGahm9XoYDx4p841b6EQWlkpi0SwNWBIv4"

# Path to Google service account Json file , e.g., 'My First Project-XXX.json'
# See more details at: https://cloud.google.com/iam/docs/creating-managing-service-account-keys#creating_service_account_keys
GOOGLE_APPLICATION_CREDENTIALS = "/home/underdoge/sensei_bot/veryopeninglichbot.json"

# Google Storage bucket name
BUCKET_NAME = "veryopeninglichbot"

# Telegram user ID, steps to get ID see: https://www.wikihow.com/Know-Chat-ID-on-Telegram-on-Android
# Putting a telegram ID will allow only the specified ID to talk to bot
TELEGRAM_ID = None

# See supported language code and texttospeech name here:
# https://cloud.google.com/text-to-speech/docs/voices
LANGUAGE_CODE = "en-US"
TEXTTOSPEECH_NAME = "en-US-Neural2-G"

# Options for the Telegram menu buttons 
menu_options = {'1': {
                        'option':"1) How to pronounce English word(s)",
                        'reply': "Ok, let's hear the pronunciation of English word(s). \n\nEnter the English word(s) into the chat box"
                },
                '2': {
                        'option':"2) Translate a word from Spanish to English",
                        'reply': "Ok, let's say (SP) in English. \n\nWhat is/are the SP word(s)?"
                }
}
