from dotenv import load_dotenv
import os
import logging
import json
import sqlite3
import csv
from telegram import Update, constants, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# Load environment variables from .env file
load_dotenv()
API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Load messages from JSON file
with open('messages.json', 'r') as f:
    messages = json.load(f)

# Helper to safely retrieve messages
def get_message(lang_code, key):
    """Safely get a message with fallback to English."""
    # Try the requested language, fallback to 'en' if not found
    lang_data = messages.get(lang_code)
    if not lang_data:
        lang_data = messages.get('en', {})
    
    # Try the key, fallback to 'en' key if not found
    text = lang_data.get(key)
    if not text:
        text = messages.get('en', {}).get(key, "Message not found")
        
    return text

def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Create table with language support
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            language_code TEXT DEFAULT 'en'
        )
    ''')
    
    # Simple migration: checking if column exists (pragmatic approach for sqlite)
    cursor.execute("PRAGMA table_info(users)")
    columns = [info[1] for info in cursor.fetchall()]
    if 'language_code' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN language_code TEXT DEFAULT "en"')
        
    conn.commit()
    conn.close()

# Save user information to CSV file
async def save_user(user_id, first_name, last_name, language_code):
    with open('users.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([user_id, first_name, last_name, language_code])

# Check if user exists in database and return if new
async def check_user(user_id, language_code='en'):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
    exists = cursor.fetchone() is not None
    
    if not exists:
        cursor.execute('INSERT INTO users (user_id, language_code) VALUES (?, ?)', (user_id, language_code))
        conn.commit()
    conn.close()
    return not exists

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    lang = update.effective_user.language_code
    is_new = await check_user(update.effective_user.id, lang)
    msg_key = 'welcome_new' if is_new else 'welcome_back'
    
    raw_text = get_message(lang, msg_key)
    formatted_text = raw_text.format(name=update.effective_user.full_name)
    await update.message.reply_html(
        text = formatted_text
    )
    # Only save to CSV if it's a new user to avoid duplicates
    if is_new:
        await save_user(update.effective_user.id, update.effective_user.first_name, update.effective_user.last_name, lang)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    lang = update.effective_user.language_code
    raw_text = get_message(lang, 'help')
    formatted_text = raw_text.format(name=update.effective_user.full_name)
    await update.message.reply_html(
        text = formatted_text
    )

# Change the Language of the bot
# First show the languages available
async def show_languages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Show the languages available
    keyboard = [
        [
            InlineKeyboardButton("English", callback_data="en"),
            InlineKeyboardButton("Spanish", callback_data="es")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose a language:", reply_markup=reply_markup)

# Set the language of the user from show_languages query
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    # Callback data is just the language code ("en" or "es")
    new_lang = query.data
    user_id = query.from_user.id
    
    # Update the language in the database
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET language_code = ? WHERE user_id = ?', (new_lang, user_id))
    conn.commit()
    conn.close()
    
    await query.edit_message_text(text=f"Language changed to {new_lang}")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text(update.message.text)

def main() -> None:
    """Start the bot."""
    # Initialize the database
    init_db()

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(API_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("language", show_languages))
    application.add_handler(CallbackQueryHandler(set_language))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until you press Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()