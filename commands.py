import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_user_language, check_and_register_user, update_user_language, get_setting, is_admin_in_db, is_user_banned
import os

# Load messages from JSON file
with open('messages.json', 'r', encoding='utf-8') as f:
    messages = json.load(f)

# For security, you should add ADMIN_ID to your .env file
ADMIN_ID = os.getenv('ADMIN_ID')
if ADMIN_ID:
    ADMIN_ID = int(ADMIN_ID)

async def is_admin(user_id):
    """Check if a user is an admin from the database or environment."""
    # Check environment ADMIN_ID first
    if ADMIN_ID and user_id == ADMIN_ID:
        return True
    # Check database
    return await is_admin_in_db(user_id)

async def is_bot_disabled(user_id):
    """Check if bot is disabled for this user or if user is banned."""
    # Check if user is banned first
    if await is_user_banned(user_id):
        return True
        
    bot_disabled = await get_setting("bot_disabled", "false")
    if bot_disabled == "true":
        # Check if user is admin - admins can always use the bot
        return not await is_admin(user_id)
    return False

def get_message(lang_code: str, key: str, default: str = "Message not found.") -> str:
    """Safely retrieves a message from the loaded JSON data, with fallbacks."""
    return messages.get(lang_code, {}).get(key) or messages.get('en', {}).get(key, default)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command."""
    user = update.effective_user
    
    # Check if bot is disabled for this user
    if await is_bot_disabled(user.id):
        await update.message.reply_text("🛑 The bot is currently disabled for regular users.")
        return
    
    is_new = await check_and_register_user(user)
    
    msg_key = 'welcome_new' if is_new else 'welcome_back'
    lang = await get_user_language(user.id)
    
    raw_text = get_message(lang, msg_key)
    formatted_text = raw_text.format(name=user.full_name)
    await update.message.reply_html(text=formatted_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /help command."""
    user = update.effective_user
    
    # Check if bot is disabled for this user
    if await is_bot_disabled(user.id):
        await update.message.reply_text("🛑 The bot is currently disabled for regular users.")
        return
    
    lang = await get_user_language(user.id)
    text = get_message(lang, 'help')
    await update.message.reply_html(text=text)

async def show_languages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows a keyboard for language selection."""
    user = update.effective_user
    
    # Check if bot is disabled for this user
    if await is_bot_disabled(user.id):
        await update.message.reply_text("🛑 The bot is currently disabled for regular users.")
        return
    
    lang = await get_user_language(user.id)
    text = get_message(lang, 'language_select')
    
    keyboard = [
        [
            InlineKeyboardButton("English", callback_data="en"), 
            InlineKeyboardButton("Spanish", callback_data="es"),
            InlineKeyboardButton("Tamil", callback_data="ta")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_html(text, reply_markup=reply_markup)

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Updates the user's language choice from a callback query."""
    query = update.callback_query
    await query.answer()
    
    new_lang = query.data
    user_id = query.from_user.id
    
    await update_user_language(user_id, new_lang)
    
    text = get_message(new_lang, 'language_changed').format(language=new_lang.upper())
    await query.edit_message_text(text=text, parse_mode='HTML')

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles messages that aren't recognized commands."""
    user = update.effective_user
    
    # Check if bot is disabled for this user
    if await is_bot_disabled(user.id):
        await update.message.reply_text("🛑 The bot is currently disabled for regular users.")
        return
    
    lang = await get_user_language(user.id)
    text = get_message(lang, 'unknown_command')
    await update.message.reply_html(text)
