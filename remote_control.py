from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_user_language, update_user_language, get_user_profile
from commands import get_message

async def remote_control_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the Remote Control dashboard."""
    user = update.effective_user
    lang = await get_user_language(user.id)
    
    text = "🎮 <b>Remote Control Panel</b>\nSelect an option below:"
    
    keyboard = [
        [InlineKeyboardButton("👤 My Profile", callback_data="rc_profile")],
        [InlineKeyboardButton("🌐 Change Language", callback_data="rc_lang")],
        [InlineKeyboardButton("📊 Bot Status", callback_data="rc_status")],
        [InlineKeyboardButton("❌ Close", callback_data="rc_close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.message.reply_html(text, reply_markup=reply_markup)

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the user's stored profile information."""
    query = update.callback_query
    user_id = query.from_user.id
    profile = await get_user_profile(user_id)
    
    if profile:
        text = (
            f"👤 <b>Your Profile</b>\n\n"
            f"🆔 <b>ID:</b> <code>{profile['user_id']}</code>\n"
            f"👤 <b>Username:</b> @{profile['username'] or 'None'}\n"
            f"📛 <b>Name:</b> {profile['first_name']} {profile['last_name'] or ''}\n"
            f"🌐 <b>Language:</b> {profile['language_code'].upper()}\n"
            f"💎 <b>Premium:</b> {'Yes' if profile['is_premium'] else 'No'}"
        )
    else:
        text = "❌ Profile not found."

    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="rc_main")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

async def change_language_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the language selection menu within the remote control."""
    query = update.callback_query
    user = query.from_user
    lang = await get_user_language(user.id)
    
    text = get_message(lang, 'language_select')
    
    keyboard = [
        [InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"), 
         InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"),
         InlineKeyboardButton("🇮🇳 தமிழ்", callback_data="lang_ta")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="rc_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def remote_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Router for all remote control related callbacks."""
    query = update.callback_query
    data = query.data
    await query.answer()
    
    if data == "rc_main":
        await remote_control_panel(update, context)
    elif data == "rc_profile":
        await show_profile(update, context)
    elif data == "rc_lang":
        await change_language_method(update, context)
    elif data == "rc_status":
        status_text = "✨ <b>Bot Status</b>\n\n✅ Database: Connected\n✅ Polling: Active\n🕒 Uptime: Running"
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="rc_main")]]
        await query.edit_message_text(status_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    elif data == "rc_close":
        await query.delete_message()
    elif data.startswith("lang_"):
        new_lang = data.split("_")[1]
        user_id = query.from_user.id
        await update_user_language(user_id, new_lang)
        
        success_msg = get_message(new_lang, 'language_changed').format(language=new_lang.upper())
        keyboard = [[InlineKeyboardButton("🏠 Back to Control Panel", callback_data="rc_main")]]
        await query.edit_message_text(success_msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
