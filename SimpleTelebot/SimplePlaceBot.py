import telebot
import redis
import os
from telebot import apihelper.ApiException

TOKEN = os.getenv('telebot_key')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['add'])
def add_location(message):
    if not message.text[5:]:
        bot.send_message(chat_id=message.chat.id, text='Вы не написали адресс.')
    r = redis.Redis()
    r.lpush(message.chat.id, message.text[5:])
    try:
        bot.send_photo(chat_id=message.chat.id, photo=None, caption='Hi! Bro')
    except apihelper.ApiException as e:
        bot.send_message(chat_id=message.chat.id, text='упс, у тебя ошибка(')
    bot.send_message(chat_id=message.chat.id, text='Адресс сохранён.')


@bot.message_handler(commands=['list'])
def show_list(message):
    r = redis.Redis()
    place_list = r.lrange(message.chat.id, 0, 9)
    if place_list:
        for place in place_list:
            bot.send_message(chat_id=message.chat.id, text=place.decode('utf-8'))
    else:
        bot.send_message(chat_id=message.chat.id, text='Список адрессов пуст.')


@bot.message_handler(commands=['reset'])
def delete_list(message):
    r = redis.Redis()
    user_id = message.chat.id
    r.delete(user_id)
    bot.send_message(chat_id=message.chat.id, text='Список адрессов удалён')


bot.polling()