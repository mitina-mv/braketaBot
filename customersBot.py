import logging
import telebot
from telebot import types
import os
import sqlite3
from datetime import datetime, timedelta

token = os.environ.get("TOKEN_CUSTOMERS")
db_path = 'braketaDB.db'

bot = telebot.TeleBot(token)

user = {}

status_bot = ''

@bot.message_handler(commands=['start'])
def start_message(message):
    global status_bot

    telegram_id = message.from_user.id
    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        cursor.execute('SELECT * FROM Customers WHERE telegram_id = ?', (telegram_id,))
        user_data = cursor.fetchone()
        user['telegram_id'] = telegram_id

    if user_data:
        bot.send_message(message.chat.id, f"Привет {user_data[1]} ✌️  \nДобро пожаловать в систему!")
    else:
        status_bot = 'register'
        contact_button(message.chat.id)

def contact_button(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = types.KeyboardButton("Поделиться контактом", request_contact=True)
    markup.add(button)
    bot.send_message(chat_id, "Поделитесь своим контактом, нажав кнопку ниже.", reply_markup=markup)

@bot.message_handler(content_types=['text'])
def handle_full_name(message):
    global status_bot
    global user
    
    if status_bot == 'register':
        full_name = message.text
        user['full_name'] = full_name
        
        with sqlite3.connect(db_path) as db:
            # записываем нового пользователя
            cursor = db.cursor()
            cursor.execute('INSERT INTO Customers (full_name, phone, telegram_id) VALUES (?, ?, ?)', (user['full_name'], user['phone_number'], user['telegram_id'],))
            db.commit()

            # получаем данные нового пользователя 
            cursor = db.cursor()
            cursor.execute('SELECT * FROM Customers WHERE telegram_id = ?', (user['telegram_id'],))
            user = cursor.fetchone()
            print(user)

            # создаем демо заказ
            current_date = datetime.now().date()
            planned_delivery_date = current_date + timedelta(days=10)

            cursor.execute('INSERT INTO Orders (name, status_id, order_date, planned_delivery_date, manager_id, customer_id) VALUES (?, ?, ?, ?, ?, ?)', ('Тестовый заказ', 1, current_date, planned_delivery_date, 1, user[0],))
            db.commit()

        bot.send_message(message.chat.id, f"Спасибо, {full_name}! Мы создали вам демо-заказ.")
        status_bot = 'start'

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    contact = message.contact
    phone_number = contact.phone_number
    user['phone_number'] = phone_number
    bot.send_message(message.chat.id, "Введите ваше полное имя: ")


bot.polling(none_stop=True)