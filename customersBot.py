import logging
import telebot
from telebot import types
import os
import sqlite3
from datetime import datetime, timedelta
import random
import schedule
import threading
import time

token = os.environ.get("TOKEN_CUSTOMERS")
db_path = 'braketaDB.db'

bot = telebot.TeleBot(token)

user = {}

status_bot = ''

last_checked_timestamp = time.time() - 120

def get_user_from_db(telegram_id):
    global user

    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        cursor.execute('SELECT * FROM Customers WHERE telegram_id = ?', (telegram_id,))
        user_data = cursor.fetchone()
    
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

    with sqlite3.connect(db_path) as db:        
        # записываем нового пользователя
        cursor = db.cursor()
        cursor.execute('INSERT INTO Customers (phone, telegram_id) VALUES (?, ?)', (phone_number, message.chat.id,))
        db.commit()

    status_bot = 'register'
    bot.send_message(message.chat.id, "Введите ваше полное имя: ")
    

# Обработчик для команды /history
@bot.message_handler(commands=['history'])
@bot.message_handler(func=lambda message: message.text == '📚 История заказов')
def history_command(message):
    with sqlite3.connect(db_path) as db:        
        # получаем id пользователя
        user_id = get_user_from_db(message.chat.id)[0]

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
                       
        """, (user_id,))
        # Получение всех результатов запроса
        results = cursor.fetchall()

        if results == []:
            bot.send_message(message.chat.id, "Вы еще не совершали заказов, история пуста.")
            return

        # Вывод результатов
        orders_str = ''
        count = 1
        for row in results:
            orders_str += f"""\n\n{count}. *Заказ № {row[0]} \"{row[1]}\" *\n 
    Статус: {row[4]}
    Дата заказа: {row[2]}
    Дата доставки: {row[3]} 
    Менеджер: {row[5]}"""

            count += 1
        
    bot.send_message(message.chat.id, f"История Ваших заказов:{orders_str}", parse_mode="Markdown")
    send_menu(message.chat.id)
    

# Обработчик для команды /orders
@bot.message_handler(commands=['orders'])
@bot.message_handler(func=lambda message: message.text == '📦 Актуальные заказы')
def orders_command(message):
    global user

    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        # получаем id пользователя
        user_id = get_user_from_db(message.chat.id)[0]

        cursor.execute("""SELECT  
            Orders.id AS order_id,
            Orders.name AS order_name
        FROM Orders
        WHERE Orders.customer_id = ?
        AND Orders.status_id != 7
        AND Orders.status_id != 8
        AND Orders.status_id != 9
        ORDER BY Orders.order_date DESC          
        """, (user_id,))
        # Получение всех результатов запроса
        results = cursor.fetchall()

    if results:
        markup = types.InlineKeyboardMarkup(row_width=2)
        for row in results:
            markup.add(types.InlineKeyboardButton(f"Заказ № {row[0]}", callback_data=f"order_{row[0]}"))
        
        bot.send_message(message.chat.id, "Ваши актуальные заказы: \n", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Мы не нашли у Вас актуальных заказов.")
        send_menu(message.chat.id)


# Обработчик для команды /help
@bot.message_handler(commands=['help'])
@bot.message_handler(func=lambda message: message.text == '❓ Помощь')
def help_command(message):
    bot.send_message(message.chat.id, """*Доступные команды*\n
/start - если что-то идет не так, попробуйте перезапустить бота
/help - покажет все команды
/history - история заказов
/orders - список актуальных заказов. Нажмите на кнопку под сообщением, чтобы увидеть подробности по заказу.
""", parse_mode="Markdown")

# Обработчик коллбека
@bot.callback_query_handler(func=lambda call:True)
def callback_query(call):
    req = call.data.split('_')

    if req[0] == 'order':
        # получаем детальный заказ по его id
        with sqlite3.connect(db_path) as db:
            cursor = db.cursor()
            cursor.execute("""SELECT 
                Orders.id AS order_id,
                Orders.name AS order_name,
                Orders.order_date,
                Orders.planned_delivery_date,
                Statuses.name AS status_name,
                Managers.full_name AS manager_name,
                OrderItems.quantity,
                Items.units,
                Items.name AS item_name
            FROM Orders
            JOIN Statuses ON Orders.status_id = Statuses.id
            JOIN Managers ON Orders.manager_id = Managers.id
            JOIN OrderItems ON Orders.id = OrderItems.order_id
            JOIN Items ON OrderItems.item_id = Items.id
            WHERE Orders.id = ?;          
            """, (req[1],))
            # Получение всех результатов запроса
            result = cursor.fetchall()

        if not result:
            bot.send_message(call.message.chat.id, "Мы не определили Ваш заказ. Свяжитесь с компанией.")
            return
        
        order_details = {
            'order_id': result[0][0],
            'order_name': result[0][1],
            'order_date': result[0][2],
            'planned_delivery_date': result[0][3],
            'status_name': result[0][4],
            'manager_name': result[0][5],
            'order_items': []
        }

        for row in result:
            print(row)
            order_items_details = {'item_name': row[8], 'quantity': row[6], 'units': row[7]}
            order_details['order_items'].append(order_items_details)

        output = (
            f"*Заказ № {order_details['order_id']} \"{order_details['order_name']}\" *\n\n"
            f"Статус: {order_details['status_name']}\n"
            f"Дата заказа: {order_details['order_date']}\n"
            f"Плановая дата доставки: {order_details['planned_delivery_date']}\n"
            f"Менеджер: {order_details['manager_name']}\n\n"
            "*Состав заказа:*\n"
        )

        count = 1;
        for item in order_details['order_items']:
            output += f"{count}. {item['item_name']} ({item['quantity']} {item['units']})\n"
            count += 1

        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_{row[0]}"))

        bot.send_message(call.message.chat.id, output, parse_mode="Markdown", reply_markup=markup)

    elif req[0] == 'cancel':
        # обновляем статус заказа по его id
        with sqlite3.connect(db_path) as db:
            cursor = db.cursor()
            # получаем текущий id статуса
            cursor.execute("""SELECT  
                Orders.status_id
            FROM Orders
            WHERE Orders.id = ?                        
            """, (req[1],))

            order_status = cursor.fetchone()

            if order_status and (order_status[0] == 7 or order_status[0] == 8 or order_status[0] == 9):
                bot.send_message(call.message.chat.id, "Изменение статуса недопустимо!")
                return

            # обновляем статус
            cursor.execute("UPDATE Orders SET status_id = 9, timestamp_update = ? WHERE id = ?", (time.time() + 30, req[1],))
            db.commit()

        bot.send_message(call.message.chat.id, "Заявка на отмену заказа направлена менеджеру заказа! Ожидайте обратной связи.")
        send_menu(call.message.chat.id)

     

# главный обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_full_name(message):
    global status_bot
    global user
    
    if status_bot == 'register':
        full_name = message.text
        
        with sqlite3.connect(db_path) as db:
            # получаем id пользователя
            user_id = get_user_from_db(message.chat.id)[0]

            # записываем нового пользователя
            cursor = db.cursor()
            cursor.execute('UPDATE Customers SET full_name = ? WHERE id = ?', (full_name, user_id,))
            db.commit()

            current_date = datetime.now().date()
            planned_delivery_date = current_date + timedelta(days=10)

            cursor.execute('INSERT INTO Orders (name, status_id, order_date, planned_delivery_date, manager_id, customer_id) VALUES (?, ?, ?, ?, ?, ?)', ('Тестовый заказ', 1, current_date, planned_delivery_date, 1, user_id,))
            db.commit()

            # создаем позиции в заказе
            new_order_id = cursor.lastrowid
            for i in range(random.randint(3, 6)):
                cursor.execute('INSERT INTO OrderItems (order_id, item_id, quantity) VALUES (?, ?, ?)', (new_order_id, random.randint(1, 17), random.randint(15, 1000),))
                db.commit()

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

# Функция для проверки изменений в базе данных и отправки сообщений
def check_database_changes():
    global bot
    global last_checked_timestamp

    with sqlite3.connect('braketaDB.db') as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT
                Orders.id AS order_id,
                Orders.name AS order_name,
                Statuses.name AS status_name,
                Customers.telegram_id as telega
            FROM Orders
            JOIN Statuses ON Orders.status_id = Statuses.id
            JOIN Customers ON Orders.customer_id = Customers.id
            WHERE Orders.timestamp_update > ?
            AND Orders.status_id != 1
            ORDER BY Orders.order_date DESC
        ''', (last_checked_timestamp,))

        results = cursor.fetchall()

        for row in results:
            order_id = row[0]
            order_name = row[1]
            status_name = row[2]
            telega = row[3]

            # Если есть изменения, отправьте сообщения пользователям
            bot.send_message(telega, f"Заказ №{order_id} \"{order_name}\". Статус обновлен: {status_name}")

        last_checked_timestamp = time.time()

# Функция для выполнения фоновой задачи
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# планировщик просмотра бд
schedule.every(1).minutes.do(check_database_changes)

# Создать и запустить фоновую задачу в отдельном потоке
background_thread = threading.Thread(target=run_schedule)
background_thread.start()

while True:
    try:
        bot.polling(none_stop=True)
        time.sleep(1)
    except Exception as e:
        logging.error(e)
        time.sleep(5)

