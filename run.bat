#!/bin/bash

# 1. Activate the virtual environment
source ./venv/bin/activate

# 2. Run the bot in a detached screen session (Background)
# -d -m creates the screen without "jumping" into it
screen -dmS telebot python3 main.py

# 3. Check if the screen command started successfully
if [ $? -ne 0 ]; then
    echo "================================================================"
    echo "                      ERROR STARTING SCREEN                     "
    echo "================================================================"
else
    echo "================================================================"
    echo "               BOT IS RUNNING IN SCREEN: telebot                "
    echo "   Use 'screen -r telebot' to see logs, 'Ctrl+A, D' to detach   "
    echo "================================================================"
fi