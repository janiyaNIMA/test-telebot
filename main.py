import telebot
import requests

API_TOKEN = '6463336436:AAGyGh-ANYPjMDqRLkIsCS5LjOurXvJAqDs'
bot = telebot.TeleBot(API_TOKEN)

# Dictionary to store user states
user_states = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Hey..! How's it going? Type /weather to get weather information.")

@bot.message_handler(commands=['weather'])
def ask_location(message):
    chat_id = message.chat.id
    user_states[chat_id] = 'waiting_for_location'
    bot.reply_to(message, "Please provide the location for which you want the weather information.")

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'waiting_for_location')
def get_weather(message):
    chat_id = message.chat.id
    city = message.text
    API_key = 'b8a0131cac0cc7e9d7b6ba1c386f8f26'
    units = 'metric'
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_key}&units={units}'
    
    resp = requests.get(url)
    if resp.status_code == 200:
        msg = resp.json()
        reply = f'''
        <b>{msg['name']}</b>
        Temp: {msg['main']['temp']}°C
        Pressure: {msg['main']['pressure']} hPa
        Humidity: {msg['main']['humidity']}%
        Wind Speed: {msg['wind']['speed']} m/s
        '''
    else:
        reply = f"Sorry, I couldn't find the weather for {city}. Please check the city name and try again."
    
    bot.reply_to(message, reply, parse_mode='html')
    user_states[chat_id] = None  # Reset the user state

bot.polling()
