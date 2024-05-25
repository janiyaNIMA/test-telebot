import telebot
import requests

API_TOKEN = '6463336436:AAGyGh-ANYPjMDqRLkIsCS5LjOurXvJAqDs'
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Hey..! How's it going?")

@bot.message_handler(commands=['weather'])
def weather(message):
    city = "Kegalle"
    API_key = 'b8a0131cac0cc7e9d7b6ba1c386f8f26'
    units = 'metric'
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_key}&units={units}'
    resp = requests.get(url)
    msg = resp.json()
    reply = f'''
    <b>{msg['name']}</b>
    Temp: {msg['main']['temp']}°C
    Pressure: {msg['main']['pressure']} hPa
    Humidity: {msg['main']['humidity']}%
    Wind Speed: {msg['wind']['speed']} m/s
    '''
    bot.reply_to(message, reply, parse_mode='html')

bot.polling()
