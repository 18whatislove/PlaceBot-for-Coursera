import googlemaps
import telebot
import time
import os
from user_template import *
from googlemaps_managers import *
from storage import *
from telebot.apihelper import ApiException
from telebot import types


TOKEN = os.getenv('telebot_key')
bot = telebot.TeleBot(TOKEN)

API_KEY = os.getenv('google_api_key')
cli = googlemaps.Client(API_KEY)

storage = create_storage()

user = User()


#Commands
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    description = """Здравствуй, я PlaceBot. Расскажите мне про места, которые Вы бы хотели посетить, а я их запишу!\n
                    Воспользуйтесь командами для взаимодействия со мной :\n
                    \t/add – пошаговое добавление нового места, с добавлением фото и локации;\n
                    \t/list – отображение добавленных мест;\n
                    \t/reset позволяет пользователю удалить все его добавленные локации;\n
                    ID нашего чата будет записан для дальнеших действий.
                    """
    user.id = add_user(message.chat.id)
    bot.send_message(chat_id=user.id, text=description)


@bot.message_handler(commands=['add'], func=lambda message: user.get_stage() == User.lobby)
def adding_mode(message):
    user.set_stage(User.stage1)
    bot.send_message(chat_id=user.id, text='Напишите название вашего места.')


@bot.message_handler(commands=['list'], func=lambda message: user.get_stage() == User.lobby)
def show_saved_places(message):
    addresses = show_list_of_places(user.id)
    if addresses:
        for address in addresses:
            bot.send_message(chat_id=user.id, text=f"{address[0]}, {address[1]}")
            bot.send_location(chat_id=user.id, latitude=address[2], longitude=address[3])
            time.sleep(2)
    else:
        bot.send_message(chat_id=user.id, text='Ваш список мест пуст!')


@bot.message_handler(commands=['reset'], func=lambda message: user.get_stage() == User.lobby)
def remove_saved_places(message):
    user.id = message.chat.id
    clear_list(user.id)
    bot.send_message(chat_id=user.id, text='Список адрессов удалён')


#NAMING MODE
@bot.message_handler(func=lambda message: user.get_stage() == User.stage1)
def name_handler(message):
    user.keyword = message.text
    user.set_stage(User.stage2)
    bot.send_message(chat_id=user.id, text='Отправьте ваши геоданные для уточнения адреса.')


#LOCATION MODE
@bot.message_handler(content_types=['location'], func=lambda message: user.get_stage() == User.stage2)
def location_handler(message):
    place_description = get_place_info(cli, [message.location.latitude, message.location.longitude], user.keyword)
    if place_description['message'] == 'OK!':
        user.filling_query(place_description['place_info'])
        user.set_stage(User.stage3)
        bot.send_message(chat_id=user.id, text='Хотите сохранить фотографию места?',
                         reply_markup=create_keyboard('Да, давай!', 'Нет, не хочу.'))
    else:
        user.set_stage(User.lobby)
        bot.send_message(chat_id=user.id, text=f"{place_description['message']} \
                                               Проверьте правильность названия и повторите попытку.")


#PHOTO MODE
@bot.message_handler(content_types=['photo'], func=lambda message: user.get_stage() == User.stage3)
def photo_handler(message):
    user.attaching_photo_id(message.photo)
    user.set_stage(User.confirmation)
    confirmation(user.query, with_photo=True)


#SEARCHING MODE
@bot.message_handler(content_types=['text', 'location'], func=lambda message: user.get_stage() == User.lobby)
def show_place_nearby(message):
    if message.text:
        bot.send_message(chat_id=user.id, text='Отправьте ваши геоданные, и я скажу если поблизости есть ваши места.')
    elif message.location:
        result = get_nearby_place(cli, [message.location.latitude, message.location.longitude], user.id)
        if result['message'] == 'Места в радиусе 500 метров':
            for place in result['places']:
                snapshot = get_photo(user.id, place['name'])[0]
                try:
                    bot.send_photo(chat_id=user.id, photo=snapshot[0], caption=f"{place['name']}, {place['vicinity']}")
                except ApiException:
                    bot.send_message(chat_id=user.id, text=f"{place['name']}, {place['vicinity']}")
                except TypeError:
                    bot.send_message(chat_id=user.id, text=f"{place['name']}, {place['vicinity']}")
                bot.send_location(chat_id=user.id, latitude=place['geometry']['location']['lat'],
                                  longitude=place['geometry']['location']['lng'])
                time.sleep(2)
        else:
            bot.send_message(chat_id=user.id, text=result['message'])


# Обработчики текстовых сообщенй
@bot.message_handler(content_types=['text'], func=lambda message: message.text in ['Да, давай!', 'Нет, не хочу.'])
def decision_handler(message):
    if message.text == 'Да, давай!':
        user.set_stage(User.stage3)
        bot.send_message(chat_id=user.id, text='Отправьте фотографию.')
    elif message.text == 'Нет, не хочу.':
        user.set_stage(user.confirmation)
        confirmation(user.show_query())
    else:
        bot.send_message(chat_id=user.id, text='Не был выбран ответ из предложенных варинатов. Данные не будут сохранены!')
        user.set_stage(User.lobby)


def confirmation(user_query, with_photo=False):
    user.set_stage(User.confirmation)
    if with_photo:
        bot.send_photo(chat_id=user.id, photo=user_query['photo_id'],
                       caption=f"Дайте согласие на сохранение данных. \
                                Название места: {user_query['name']};Адрес: {user_query['address']}.",
                       reply_markup=create_keyboard('Согласен!', 'Отказываюсь!'))
    else:
        bot.send_message(chat_id=user.id,
                         text=f"Дайте согласие на сохранение данных. \
                                Название места:{user_query['name']};Адрес: {user_query['address']}.",
                         reply_markup=create_keyboard('Согласен!', 'Отказываюсь!'))


@bot.message_handler(func=lambda message: user.get_stage() == User.confirmation)
def confirmation_decision_handler(message):
    if message.text == 'Согласен!':
        add_place(user.send_query())
        bot.send_message(chat_id=user.id, text='Ваши данные сохранены!')
    elif message.text == 'Отказываюсь!':
        bot.send_message(chat_id=user.id, text='Ваши данные не сохранены!')
    else:
        bot.send_message(chat_id=user.id, text='Не был выбран ответ из предложенных варинатов. Данные не будут сохранены!')
    user.set_stage(User.lobby)


def warnings_filter(message):  # Проверяет, если тип контента соответствует этапу добавления места
    stage = user.get_stage()
    if stage != User.lobby:
        stages = {User.stage1: 'text', User.stage2: 'location',
                  User.stage3: 'photo', User.confirmation: 'text'}
        return False if stages[stage] == message.content_type else True


@bot.message_handler(content_types=['text', 'location', 'photo'], func=warnings_filter)
def warnings(message):
    stage = user.get_stage()
    warnings = {User.stage1: "Вы не закончили заполнять анкету. Отправьте, пожалуйста, название места.",
                User.stage2: "Вы не закончили заполнять анкету. Отправьте, пожалуйста, ваши геоданные.",
                User.stage3: "Вы не закончили заполнять анкету. Отправьте, пожалуйста, фотографию места.",
                User.confirmation: "Вы не дали ответ на сохранение данных. Откройте клавиатуру и выберите вариант ответа."}
    bot.send_message(chat_id=user.id, text=warnings[stage])


def create_keyboard(first_button, second_button):
    keyboard = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    button1 = types.KeyboardButton(first_button)
    button2 = types.KeyboardButton(second_button)
    keyboard.add(button1, button2)
    return keyboard


bot.polling(timeout=60)