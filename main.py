from dotenv import load_dotenv
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler

from database import init_db, get_setting
import commands
import remote_control
import admin

# Load environment variables from .env file
load_dotenv()
API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def post_init(application: Application) -> None:
    """Task to run after bot initialization."""
    await application.bot.set_my_commands([
        ("start", "Start the bot & see welcome message"),
        ("language", "Change display language"),
        ("remote", "Open Interactive Control Panel"),
        ("help", "Show all commands"),
        ("broadcast", "Admin: Broadcast message (Admins only)"),
        ("sudo", "Admin: Execute sudo commands (Admins only)"),
    ])

def main() -> None:
    """Initializes and runs the bot."""
    # Ensure the database is set up
    init_db()

    # Create the Application
    application = Application.builder().token(API_TOKEN).post_init(post_init).build()

    # --- Broadcast Conversation ---
    broadcast_handler = ConversationHandler(
        entry_points=[CommandHandler("broadcast", admin.broadcast_start)],
        states={
            admin.SELECT_TARGET: [CallbackQueryHandler(admin.receive_target, pattern="^target_")],
            admin.SELECT_FILE: [MessageHandler(filters.ALL & ~filters.COMMAND, admin.receive_file)],
            admin.GET_CAPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.receive_caption),
                CommandHandler("skip", admin.receive_caption)
            ],
            admin.CONFIRM_SEND: [CallbackQueryHandler(admin.admin_callback_handler, pattern="^admin_")]
        },
        fallbacks=[CommandHandler("cancel", admin.cancel)]
    )

    # Register handlers
    application.add_handler(broadcast_handler)
    application.add_handler(CommandHandler("start", commands.start))
    application.add_handler(CommandHandler("help", commands.help_command))
    application.add_handler(CommandHandler("language", commands.show_languages))
    application.add_handler(CommandHandler("remote", remote_control.remote_control_panel))
    application.add_handler(CommandHandler("sudo", admin.sudo_command))
    
    # Register callback handlers
    application.add_handler(CallbackQueryHandler(remote_control.remote_callback_handler, pattern="^(rc_|lang_)"))
    application.add_handler(CallbackQueryHandler(commands.set_language, pattern="^(en|es|ta)$"))
    
    # Register relay handler for admins (must be before unknown_command)
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, admin.relay_handler))
    
    # Register message handler for unknown input
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, commands.unknown_command))

    # Start the bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()