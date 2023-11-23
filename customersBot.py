import logging
import telebot
from telebot import types
import os
import sqlite3
from datetime import datetime, timedelta
import random

token = os.environ.get("TOKEN_CUSTOMERS")
db_path = 'braketaDB.db'

bot = telebot.TeleBot(token)

user = {}

status_bot = ''

def get_user_from_db(telegram_id):
    global user

    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        cursor.execute('SELECT * FROM Customers WHERE telegram_id = ?', (telegram_id,))
        user_data = cursor.fetchone()
        user['telegram_id'] = telegram_id
    
    return user_data

@bot.message_handler(commands=['start'])
def start_message(message):
    global status_bot
    global user

    telegram_id = message.from_user.id
    user_data = get_user_from_db(telegram_id)

    if user_data:
        bot.send_message(message.chat.id, f"Привет, {user_data[1]} ✌️  \nДобро пожаловать в систему!")
        status_bot = 'start'
        user = user_data
        send_menu(message.chat.id)
    else:
        status_bot = 'register'
        contact_button(message.chat.id)

def contact_button(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = types.KeyboardButton("Поделиться контактом", request_contact=True)
    markup.add(button)
    bot.send_message(chat_id, "Поделитесь своим контактом, нажав кнопку ниже.", reply_markup=markup)

def send_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    history_button = types.KeyboardButton("📚 История заказов")
    orders_button = types.KeyboardButton("📦 Актуальные заказы")
    help_button = types.KeyboardButton("❓ Помощь")

    markup.add(history_button)
    markup.add(orders_button)
    markup.add(help_button)

    bot.send_message(chat_id, "Главное меню:", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    contact = message.contact
    phone_number = contact.phone_number
    user['phone_number'] = phone_number
    bot.send_message(message.chat.id, "Введите ваше полное имя: ")
    

# Обработчик для команды /history
@bot.message_handler(commands=['history'])
@bot.message_handler(func=lambda message: message.text == '📚 История заказов')
def history_command(message):
    global user

    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        cursor.execute("""SELECT  
            Orders.id AS order_id,
            Orders.name AS order_name,
            Orders.order_date AS create_date,
            Orders.planned_delivery_date AS delivery_date,
            Statuses.name AS status_name,
            Managers.full_name AS manager_name
        FROM Orders
        JOIN Statuses ON Orders.status_id = Statuses.id
        JOIN Managers ON Orders.manager_id = Managers.id
        WHERE Orders.customer_id = ?
        ORDER BY Orders.order_date DESC
                       
        """, (user[0],))
        # Получение всех результатов запроса
        results = cursor.fetchall()

        # Вывод результатов
        orders_str = ''
        count = 1
        for row in results:
            orders_str += f"""{count}. *Заказ № {row[0]} \"{row[1]}\" *\n 
    Статус: {row[4]}
    Дата заказа: {row[2]}
    Дата доставки: {row[3]} 
    Менеджер: {row[5]}"""

            ++count
        
    bot.send_message(message.chat.id, f"История Ваших заказов:\n\n{orders_str}", parse_mode="Markdown")
    send_menu(message.chat.id)
    

# Обработчик для команды /orders
@bot.message_handler(commands=['orders'])
@bot.message_handler(func=lambda message: message.text == '📦 Актуальные заказы')
def orders_command(message):
    global user

    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        cursor.execute("""SELECT  
            Orders.id AS order_id,
            Orders.name AS order_name
        FROM Orders
        WHERE Orders.customer_id = ?
        AND Orders.status_id != 7
        ORDER BY Orders.order_date DESC
                       
        """, (user[0],))
        # Получение всех результатов запроса
        results = cursor.fetchall()

    markup = types.InlineKeyboardMarkup(row_width=2)
    for row in results:
        markup.add(types.InlineKeyboardButton(f"Заказ № {row[0]}", callback_data=f"order_{row[0]}"))
    
    bot.send_message(message.chat.id, "Ваши актуальные заказы: \n", reply_markup=markup)

# Обработчик для команды /help
@bot.message_handler(commands=['help'])
@bot.message_handler(func=lambda message: message.text == '❓ Помощь')
def help_command(message):
    bot.send_message(message.chat.id, "Помощь: Как я могу вам помочь?")

# главный обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
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

            # создаем позиции в заказе
            new_order_id = cursor.lastrowid
            for i in range(2):
                cursor.execute('INSERT INTO OrderItems (order_id, item_id, quantity) VALUES (?, ?, ?)', (new_order_id, random.randint(1, 6), random.randint(15, 1000),))
                # db.commit()

        bot.send_message(message.chat.id, f"Спасибо, {full_name}! Мы создали вам демо-заказ.")
        status_bot = 'start'

        send_menu(message.chat.id)

    elif status_bot == 'start':
        bot.send_message(message.chat.id, f"Что-то сделаем")
    else:
        telegram_id = message.from_user.id
        user_data = get_user_from_db(telegram_id)
        if user_data:
            user = user_data
        bot.send_message(message.chat.id, f"мы вас не поняли")


bot.polling(none_stop=True)