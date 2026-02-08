import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from database import (
    get_all_users, is_admin_in_db, add_admin, remove_admin, 
    get_all_admins, get_setting, set_setting, get_users_by_filter,
    toggle_user_ban, add_group, remove_group, add_user_to_group, 
    get_all_groups, get_users_in_group
)

# Define states for ConversationHandler
SELECT_TARGET, SELECT_FILE, GET_CAPTION, CONFIRM_SEND = range(4)

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

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for the broadcast command: Ask for Target."""
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Access denied. This command is for admins only.")
        return ConversationHandler.END

    groups = await get_all_groups()
    keyboard = [[InlineKeyboardButton("📢 All Users", callback_data="target_all")]]
    
    # Add group buttons in rows of 2
    for i in range(0, len(groups), 2):
        row = [InlineKeyboardButton(f"📁 {g}", callback_data=f"target_grp_{g}") for g in groups[i:i+2]]
        keyboard.append(row)
        
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📢 <b>Broadcast Initiation</b>\n\nPlease select the <b>Target Audience</b> for this broadcast:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return SELECT_TARGET

async def receive_target(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the target selection."""
    query = update.callback_query
    await query.answer()
    
    target = query.data
    context.user_data['broadcast_target'] = target
    
    target_display = "All Users" if target == "target_all" else f"Group: {target.replace('target_grp_', '')}"
    
    await query.edit_message_text(
        f"🎯 <b>Target:</b> {target_display}\n\nNow, please <b>send the file</b> (photo, document, video, etc.) you want to broadcast.",
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
        
        target = context.user_data.get('broadcast_target', 'target_all')
        if target == "target_all":
            users = await get_all_users()
        else:
            group_name = target.replace('target_grp_', '')
            users = await get_users_in_group(group_name)
            
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

async def sudo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /sudo command with subcommands."""
    user_id = update.effective_user.id
    
    # Check if user is admin
    if not await is_admin(user_id):
        await update.message.reply_text("⛔ Access denied. This command is for admins only.")
        return
    
    args = context.args
    
    # Check if there are arguments
    if not args:
        help_text = (
            "⚠️ <b>Sudo Command Help:</b>\n\n"
            "<b>Structure:</b> /sudo [function] [-flags] [arguments]\n\n"
            "🔧 <b>System:</b>\n"
            "• <code>break -a, --all</code> - Disable bot for all users\n\n"
            "👤 <b>Admins:</b>\n"
            "• <code>add --admin &lt;id&gt;</code> - Promote user to admin\n"
            "• <code>remove --admin &lt;id&gt;</code> - Remove admin status\n\n"
            "📊 <b>Users:</b>\n"
            "• <code>getusers -a, --all</code> - List all users\n"
            "• <code>getusers -b, --banned</code> - List banned users\n"
            "• <code>getusers -l, --lang &lt;code&gt;</code> - Filter by language\n\n"
            "🛡 <b>Moderation:</b>\n"
            "• <code>ban &lt;id&gt;</code> - Ban a user\n"
            "• <code>unban &lt;id&gt;</code> - Unban a user\n\n"
            "📁 <b>Groups:</b>\n"
            "• <code>mkgrp -n &lt;name&gt;</code> - Create a group\n"
            "• <code>rmgrp -n &lt;name&gt;</code> - Remove a group\n"
            "• <code>setgrp &lt;id&gt; &lt;grp&gt;</code> - Add user to group\n\n"
            "📨 <b>Broadcast & Sessions:</b>\n"
            "• <code>send -g &lt;grp&gt; -m &lt;msg&gt;</code> - Quick broadcast\n"
            "• <code>send -g &lt;grp&gt;</code> - Start live session\n"
            "• <code>send -s</code> - Stop live session"
        )
        await update.message.reply_text(help_text, parse_mode='HTML')
        return
    
    command = args[0].lower()
    
    if command == "break":
        if "-a" in args or "--all" in args:
            await set_setting("bot_disabled", "true")
            await update.message.reply_text("🛑 Bot is now disabled for regular users.")
        else:
            await update.message.reply_text("⚠️ Usage: /sudo break -a")
            
    elif command == "add":
        if "--admin" in args:
            try:
                idx = args.index("--admin")
                target_id = int(args[idx + 1])
                if await add_admin(target_id):
                    await update.message.reply_text(f"✅ User {target_id} promoted to admin.")
                else:
                    await update.message.reply_text(f"⚠️ User {target_id} is already admin.")
            except:
                await update.message.reply_text("❌ Invalid usage. Example: /sudo add --admin 123456")
        else:
            await update.message.reply_text("⚠️ Usage: /sudo add --admin <chat_id>")

    elif command == "remove":
        if "--admin" in args:
            try:
                idx = args.index("--admin")
                target_id = int(args[idx + 1])
                if await remove_admin(target_id):
                    await update.message.reply_text(f"✅ User {target_id} removed from admins.")
                else:
                    await update.message.reply_text(f"⚠️ User {target_id} is not an admin.")
            except:
                await update.message.reply_text("❌ Invalid usage. Example: /sudo remove --admin 123456")
        else:
            await update.message.reply_text("⚠️ Usage: /sudo remove --admin <chat_id>")

    elif command == "getusers":
        filter_type = "all"
        filter_val = None
        
        if "-b" in args or "--banned" in args:
            filter_type = "banned"
        elif "-l" in args or "--lang" in args:
            filter_type = "lang"
            try:
                idx = args.index("-l") if "-l" in args else args.index("--lang")
                filter_val = args[idx + 1]
            except:
                await update.message.reply_text("❌ Please specify a language code.")
                return
        
        users = await get_users_by_filter(filter_type, filter_val)
        if not users:
            await update.message.reply_text("ℹ️ No users found matching criteria.")
            return
            
        text = f"📋 <b>User List ({filter_type})</b>\n\n"
        for u in users[:50]: # Limit to 50 for telegram message size
            text += f"• <code>{u['user_id']}</code> - {u['first_name']} (@{u['username'] or 'N/A'})\n"
        
        if len(users) > 50:
            text += f"\n<i>... and {len(users)-50} more users.</i>"
        
        await update.message.reply_text(text, parse_mode='HTML')

    elif command in ["ban", "unban"]:
        is_ban = command == "ban"
        try:
            target_id = int(args[1])
            if await toggle_user_ban(target_id, is_ban):
                status = "banned" if is_ban else "unbanned"
                await update.message.reply_text(f"✅ User {target_id} has been {status}.")
            else:
                await update.message.reply_text(f"❌ Could not perform action on User {target_id}.")
        except:
            await update.message.reply_text(f"⚠️ Usage: /sudo {command} <chat_id>")

    elif command == "mkgrp":
        if "-n" in args or "--name" in args:
            try:
                idx = args.index("-n") if "-n" in args else args.index("--name")
                grp_name = args[idx + 1]
                if await add_group(grp_name):
                    await update.message.reply_text(f"✅ Group '{grp_name}' created.")
                else:
                    await update.message.reply_text(f"⚠️ Group '{grp_name}' already exists.")
            except:
                await update.message.reply_text("❌ Please specify a group name.")
        else:
            await update.message.reply_text("⚠️ Usage: /sudo mkgrp -n <name>")

    elif command == "rmgrp":
        if "-n" in args or "--name" in args:
            try:
                idx = args.index("-n") if "-n" in args else args.index("--name")
                grp_name = args[idx + 1]
                if await remove_group(grp_name):
                    await update.message.reply_text(f"✅ Group '{grp_name}' removed.")
                else:
                    await update.message.reply_text(f"⚠️ Group '{grp_name}' not found.")
            except:
                await update.message.reply_text("❌ Please specify a group name.")
        else:
            await update.message.reply_text("⚠️ Usage: /sudo rmgrp -n <name>")

    elif command == "setgrp":
        try:
            target_id = int(args[1])
            grp_name = args[2]
            if await add_user_to_group(target_id, grp_name):
                await update.message.reply_text(f"✅ User {target_id} added to group '{grp_name}'.")
            else:
                await update.message.reply_text(f"❌ Failed to add User {target_id} to group '{grp_name}'. Ensure group exists.")
        except:
            await update.message.reply_text("⚠️ Usage: /sudo setgrp <chat_id> <group_name>")

    elif command == "send":
        # Handle /sudo send -g <group> [-m <msg>] OR /sudo send -s
        if "-s" in args or "--stop" in args:
            await set_setting(f"relay_target_{user_id}", "")
            await update.message.reply_text("🛑 Relay mode deactivated. Messages will no longer be forwarded.")
            return

        target_grp = None
        if "-g" in args: target_grp = args[args.index("-g") + 1]
        elif "--group" in args: target_grp = args[args.index("--group") + 1]

        message_text = None
        if "-m" in args:
            idx = args.index("-m")
            message_text = " ".join(args[idx + 1:])
        elif "--message" in args:
            idx = args.index("--message")
            message_text = " ".join(args[idx + 1:])

        if not target_grp:
            await update.message.reply_text("⚠️ Usage: /sudo send -g <group> [-m <message>] (or use -s to stop)")
            return

        # Check if group exists (except for 'all')
        if target_grp != "all":
            all_grps = await get_all_groups()
            if target_grp not in all_grps:
                await update.message.reply_text(f"❌ Group '{target_grp}' does not exist.")
                return

        if message_text:
            # One-shot broadcast
            users = await get_all_users() if target_grp == "all" else await get_users_in_group(target_grp)
            success_count = 0
            for u_id in users:
                try:
                    await context.bot.send_message(chat_id=u_id, text=message_text, parse_mode='HTML')
                    success_count += 1
                except: continue
            await update.message.reply_text(f"✅ One-shot message sent to {success_count} users in '{target_grp}'.")
        else:
            # Activate Relay mode
            await set_setting(f"relay_target_{user_id}", target_grp)
            await update.message.reply_text(
                f"🚀 <b>Live Relay Activated</b>\n\n"
                f"Target: <code>{target_grp}</code>\n"
                f"Status: Any text or media you send now will be forwarded to this group.\n\n"
                f"💡 Use <code>/sudo send -s</code> to terminate the session.",
                parse_mode='HTML'
            )

    else:
        await update.message.reply_text("❓ Unknown sudo command. Type /sudo for help.")

async def relay_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Relays messages from admins in relay mode to their target group."""
    if not update.message or update.message.text and update.message.text.startswith('/'):
        return

    user_id = update.effective_user.id
    target_grp = await get_setting(f"relay_target_{user_id}")
    
    if not target_grp:
        return

    # Secondary admin check
    if not await is_admin(user_id):
        return

    users = await get_all_users() if target_grp == "all" else await get_users_in_group(target_grp)
    if not users:
        return

    success_count = 0
    for u_id in users:
        if u_id == user_id: continue
        try:
            # Use copy_message to support all media types
            await update.message.copy(chat_id=u_id)
            success_count += 1
        except: continue
    
    # Optional: confirm relay to admin (maybe only for the first few?)
    # await update.message.reply_text(f"📡 Relayed to {success_count} users.")
