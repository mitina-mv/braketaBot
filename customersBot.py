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
    global user

    telegram_id = message.from_user.id
    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        cursor.execute('SELECT * FROM Customers WHERE telegram_id = ?', (telegram_id,))
        user_data = cursor.fetchone()
        user['telegram_id'] = telegram_id

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
    markup = types.InlineKeyboardMarkup(row_width=1)
    history_button = types.InlineKeyboardButton("📚 История заказов", callback_data='history')
    orders_button = types.InlineKeyboardButton("📦 Актуальные заказы", callback_data='orders')
    help_button = types.InlineKeyboardButton("❓ Помощь", callback_data='help')

    markup.add(history_button, orders_button, help_button)

    bot.send_message(chat_id, "Выберите один из вариантов:", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    contact = message.contact
    phone_number = contact.phone_number
    user['phone_number'] = phone_number
    bot.send_message(message.chat.id, "Введите ваше полное имя: ")
    

# Обработчик для команды /history
@bot.message_handler(commands=['history'])
def history_command(message):
    global user

    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        cursor.execute('SELECT * FROM Orders WHERE customer_id = ?', (user[0],))
        # Получение всех результатов запроса
        results = cursor.fetchall()

        # Вывод результатов
        orders_str = ''
        count = 1
        for row in results:
            print(row)
            orders_str += f"""{count}. **Заказ № {row[0]} \"{row[1]}\" **\n 
            Статус: {row[2]}
            Дата заказа: {row[3]}
            Дата доставки: {row[4]} 
            Менеджер: {row[5]}"""
        
        bot.send_message(message.chat.id, f"Все ваши заказы:\n\n{orders_str}")
    

# Обработчик для команды /orders
@bot.message_handler(commands=['orders'])
def orders_command(message):
    bot.send_message(message.chat.id, "Отправляю информацию о ваших заказах...")

# Обработчик для команды /help
@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, "Помощь: Как я могу вам помочь?")

# Обработчик коллбека
@bot.callback_query_handler(func=lambda call:True)
def callback_query(call):
    req = call.data.split('_')
    
    if req[0] == 'history':
        history_command(call.message)
    
    elif req[0] == 'orders':
        orders_command(call.message)
    
    elif req[0] == 'help':
        help_command(call.message)

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

        bot.send_message(message.chat.id, f"Спасибо, {full_name}! Мы создали вам демо-заказ.")
        status_bot = 'start'

        send_menu(message.chat.id)

    elif status_bot == 'start':
        bot.send_message(message.chat.id, f"Что-то сделаем")
    else:
        bot.send_message(message.chat.id, f"мы вас не поняли")


bot.polling(none_stop=True)