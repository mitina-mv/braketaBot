import logging
import telebot
from telebot import types
import os
import sqlite3

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

token = os.environ.get("TOKEN")
db_path = 'braketaDB.db'

bot = telebot.TeleBot(token)

user = {}

@bot.message_handler(commands=['start'])
def start_message(message):
    telegram_id = message.from_user.id
    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        cursor.execute('SELECT * FROM Customers WHERE telegram_id = ?', (telegram_id,))
        user_data = cursor.fetchone()
        user['telegram_id'] = telegram_id

    if user_data:
        bot.send_message(message.chat.id, f"Привет {user_data[1]} ✌️  \nДобро пожаловать в систему!")
    else:
        contact_button(message.chat.id)

def contact_button(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = types.KeyboardButton("Поделиться контактом", request_contact=True)
    markup.add(button)
    bot.send_message(chat_id, "Поделитесь своим контактом, нажав кнопку ниже.", reply_markup=markup)

def get_full_name(chat_id):
    bot.send_message(chat_id, "Введите ваше полное имя: ")
    # This message should be handled in a separate function

@bot.message_handler(content_types=['text'])
def handle_full_name(message):
    full_name = message.text
    user['full_name'] = full_name
    
    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        cursor.execute('INSERT INTO Customers (full_name, phone, telegram_id) VALUES (?, ?, ?)', (user['full_name'], user['phone_number'], user['telegram_id'],))
        db.commit()
    bot.send_message(message.chat.id, f"Спасибо за предоставленное имя: {full_name}")

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    contact = message.contact
    phone_number = contact.phone_number
    user['phone_number'] = phone_number
    bot.send_message(message.chat.id, f"Спасибо за предоставленный контакт: {phone_number}")
    get_full_name(message.chat.id)

@bot.message_handler(commands=['button'])
def button_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Кнопка")
    markup.add(item1, item1)
    markup.add(item1)
    bot.send_message(message.chat.id, 'Выберите что вам надо', reply_markup=markup)

bot.polling(none_stop=True)