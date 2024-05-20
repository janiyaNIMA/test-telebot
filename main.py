import os
import telebot
import requests
from telegram import *

API_TOKEN = '6463336436:AAGyGh-ANYPjMDqRLkIsCS5LjOurXvJAqDs'
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def strat(massage):
    bot.reply_to(massage, "Hey..! Hows it going?")

@bot.message_handler(commands=['weather'])
def weather(massage):
    city = "kegalle"
    API_key = 'b8a0131cac0cc7e9d7b6ba1c386f8f26'
    units = 'standard'
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_key}&units={units}'
    resp = requests.get(url)
    msg = resp.json()
    reply = f'''
    <b>{msg['name']}</b>
    temp = {int(msg['main']['temp'])-273}°C
    pressure = {msg['main']['pressure']} Pa
    humidity = {msg['main']['humidity']} %
    wind speed = {msg['wind']['speed']} km/h
    '''
    bot.reply_to(massage, reply, parse_mode='html')

bot.polling()
