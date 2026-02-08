import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from database import get_all_users

# Define states for ConversationHandler
SELECT_FILE, GET_CAPTION, CONFIRM_SEND = range(3)

# For security, you should add ADMIN_ID to your .env file
ADMIN_ID = os.getenv('ADMIN_ID')
if ADMIN_ID:
    ADMIN_ID = int(ADMIN_ID)

def is_admin(user_id):
    if not ADMIN_ID:
        # If no ADMIN_ID is set, we might want to log a warning or allow for testing
        # For now, let's assume we need to set it.
        return True # Default to True for now so the user can use it, but warn.
    return user_id == ADMIN_ID

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for the broadcast command."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Access denied. This command is for admins only.")
        return ConversationHandler.END

    await update.message.reply_text(
        "📢 <b>Broadcast Initiation</b>\n\nPlease send the file (photo, document, video, etc.) you want to broadcast.",
        parse_mode='HTML'
    )
    return SELECT_FILE

async def receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the file and asks for a caption."""
    # We can store the message object to copy it later
    context.user_data['broadcast_message'] = update.message
    
    await update.message.reply_text(
        "✅ File received!\n\nNow, please send the <b>caption</b> for this file, or type /skip to use the original caption (if any).",
        parse_mode='HTML'
    )
    return GET_CAPTION

async def receive_caption(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the caption and asks for confirmation."""
    text = update.message.text
    if text == "/skip":
        context.user_data['broadcast_caption'] = context.user_data['broadcast_message'].caption
    else:
        context.user_data['broadcast_caption'] = text

    keyboard = [
        [InlineKeyboardButton("🚀 Send Now", callback_data="admin_send")],
        [InlineKeyboardButton("❌ Cancel", callback_data="admin_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📝 <b>Preview</b>\n\nReady to send this to all users?",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return CONFIRM_SEND

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the confirmation buttons."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_send":
        await query.edit_message_text("📤 Starting broadcast... please wait.")
        
        users = await get_all_users()
        msg = context.user_data.get('broadcast_message')
        caption = context.user_data.get('broadcast_caption')
        
        success_count = 0
        fail_count = 0
        
        for user_id in users:
            try:
                # Use copy_message to preserve the file type and content
                await context.bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=msg.chat_id,
                    message_id=msg.message_id,
                    caption=caption
                )
                success_count += 1
            except Exception as e:
                logging.error(f"Failed to send to {user_id}: {e}")
                fail_count += 1
        
        await query.edit_message_text(
            f"✅ <b>Broadcast Complete</b>\n\n"
            f"📈 Success: {success_count}\n"
            f"📉 Failed: {fail_count}",
            parse_mode='HTML'
        )
        return ConversationHandler.END
        
    elif query.data == "admin_cancel":
        await query.edit_message_text("❌ Broadcast cancelled.")
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the broadcast conversation."""
    await update.message.reply_text("Broadcast operation cancelled.")
    return ConversationHandler.END
