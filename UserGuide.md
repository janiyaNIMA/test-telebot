# 🤖 Bot User Guide

Welcome! This guide will show you how to use the bot in the simplest way possible.

---

## 🌟 For Everyone (Basic Commands)

These commands can be used by any user.

### 1. Start the Bot
Send `/start` to see the welcome message. This is like the "Home" button.

### 2. Change Your Language
Send `/language` to choose between English, Spanish, or Tamil.
> **Example:** Click the "Tamil" button to see all bot messages in Tamil.

### 3. Use the Control Panel
Send `/remote` to open a visual menu. You can check your profile or change settings by clicking buttons instead of typing commands.

---

## 🛠 For Admins (Manager Commands)

If you are an admin, you have special powers to manage the bot and talk to users.

### 1. Sending a Quick Message
If you want to send a fast text message to everyone:
> **Example:** `/sudo send -g all -m Hello everyone, hope you have a great day!`

### 2. Live Broadcast (Forwarding Mode)
This is the coolest feature! You can "link" your chat to a group of users. Anything you send (photos, videos, or text) will be copied to them.

*   **Step 1:** Choose who to talk to.
    *   Example: `/sudo send -g all` (Talks to everyone)
*   **Step 2:** Send whatever you want. The bot will send it to the users.
*   **Step 3:** When you are done, send `/sudo send -s` to stop the link.

### 3. Managing Users
*   **Creating a Category (Group):**
    *   Example: `/sudo mkgrp -n vip` (Creates a group named 'vip')
*   **Adding someone to a Category:**
    *   Example: `/sudo setgrp 1234567 vip` (Puts user #1234567 into the 'vip' group)
*   **Listing Users:**
    *   Example: `/sudo getusers -a` (See a list of everyone using the bot)
*   **Stopping a Troublemaker:**
    *   Example: `/sudo ban 1234567` (Blocks user #1234567 from using the bot)

---

## 💡 Quick Tips
*   **Commands:** All special instructions start with a slash `/`.
*   **Help:** If you forget what to do, just type `/help`.
*   **Cancel:** If you are in the middle of a setup (like `/broadcast`) and want to stop, just type `/cancel`.
