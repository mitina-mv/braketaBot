import logging
import time
import telebot
from telebot import types
import os
import sqlite3
import qrcode
import cv2

token = os.environ.get("TOKEN")
db_path = 'braketaDB.db'

bot = telebot.TeleBot(token)


generate_qr = telebot.types.KeyboardButton(text="Сгенерировать qr код")
read_qr = telebot.types.KeyboardButton(text="Считать qr код")
delivery = telebot.types.KeyboardButton(text="Оповещение о задержке")
change_role = telebot.types.KeyboardButton(text="Смена отдела (ТЕСТОВАЯ ФУНКЦИЯ)")

user = {}

logist_keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
logist_keyboard.add(generate_qr)
logist_keyboard.add(change_role)

warehouse_keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
warehouse_keyboard.add(read_qr)
warehouse_keyboard.add(change_role)

delivery_keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
delivery_keyboard.add(delivery)
delivery_keyboard.add(change_role)

none_keyboard = telebot.types.ReplyKeyboardRemove()

def get_department_by_telegram_id(telegram_id):
    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        cursor.execute('SELECT * FROM Workers WHERE telegram_id = ?', (telegram_id,))
        user_data = cursor.fetchone()
    if user_data:
        return user_data[3]
    return user_data

@bot.message_handler(commands=['start'])
def init_handler(message):
    telegram_id = message.chat.id
    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        cursor.execute('SELECT * FROM Workers WHERE telegram_id = ?', (telegram_id,))
        user_data = cursor.fetchone()

    if user_data:
        bot.send_message(message.chat.id, f"Здравствуйте, {user_data[1]}!  \nДобро пожаловать в бота для сотрудников НЛМК.")
        send_welcome_message(message, user_data[3])
    else:
    
        with sqlite3.connect(db_path) as db:
            cursor = db.cursor()
            cursor.execute('''
                SELECT 
                    Departments.id,
                    Departments.name
                FROM Departments
            ''')

            result = cursor.fetchall()
            
            inline_keyboard = types.InlineKeyboardMarkup()
            for row in result:
                department_id = row[0]
                department_name = row[1]
                button = types.InlineKeyboardButton(text=department_name, callback_data=f'department_{department_id}')
                inline_keyboard.add(button)
            bot.send_message(message.chat.id, 'Выберите ваш отдел', reply_markup=inline_keyboard)

def handle_department_selection(call):
    department_id = int(call.data.split('_')[1])
    bot.send_message(call.message.chat.id, 'Введите ваше полное имя')
    telegram_id = call.message.chat.id
    
    @bot.message_handler(content_types=['text'])
    def handle_full_name(message):
        with sqlite3.connect(db_path) as db:
            cursor = db.cursor()
            cursor.execute('INSERT INTO Workers (full_name, department_id, telegram_id) VALUES (?, ?, ?)', (message.text, department_id, telegram_id,))
            db.commit()
            bot.send_message(message.chat.id, f"Вы успешно зарегистрированы в системе! \nДобро пожаловать в бота для сотрудников НЛМК.")
            send_welcome_message(message, department_id)

def send_welcome_message(message, department):
    if department == 1:
        bot.send_message(message.chat.id, 'Главное меню:', reply_markup=logist_keyboard)
    elif department == 2:
        bot.send_message(message.chat.id, 'Главное меню:', reply_markup=warehouse_keyboard)
    elif department == 3:
        bot.send_message(message.chat.id, 'Главное меню:', reply_markup=delivery_keyboard)
        
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    if call.data.startswith('department'):
        handle_department_selection(call)
    elif call.data.startswith('delivery'):
        handle_order_delivery(call)
    elif call.data.startswith('order'):
        handle_order_selection(call)
    elif call.data.startswith('newdep'):
        handle_newdep_delivery(call)

@bot.message_handler(func=lambda message: message.text == 'Сгенерировать qr код')
def generate_qr_code(message):
    department_id = get_department_by_telegram_id(message.chat.id)

    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        cursor.execute('''
            SELECT 
                Orders.id AS order_id,
                Orders.name AS order_name
            FROM Orders
        ''')

        result = cursor.fetchall()
        if not result:
            bot.send_message(message.chat.id, "В базе отсутствуют заказы")
            send_welcome_message(message, department_id)
        else:
            inline_keyboard = types.InlineKeyboardMarkup()
            for row in result:
                order_id = row[0]
                order_name = row[1]
                button = types.InlineKeyboardButton(text=f"Заказ №{order_id}", callback_data=f'order_{order_id}')
                inline_keyboard.add(button)
            bot.send_message(message.chat.id, 'Выберите заказ', reply_markup=inline_keyboard)

@bot.message_handler(func=lambda message: message.text == 'Смена отдела (ТЕСТОВАЯ ФУНКЦИЯ)')
def change_department(message):
    
    with sqlite3.connect(db_path) as db:
            cursor = db.cursor()
            cursor.execute('''
                SELECT 
                    Departments.id,
                    Departments.name
                FROM Departments
            ''')

            result = cursor.fetchall()
            
            inline_keyboard = types.InlineKeyboardMarkup()
            for row in result:
                department_id = row[0]
                department_name = row[1]
                button = types.InlineKeyboardButton(text=department_name, callback_data=f'newdep_{department_id}')
                inline_keyboard.add(button)
            bot.send_message(message.chat.id, 'Выберите новый отдел', reply_markup=inline_keyboard)

def handle_order_selection(call):
    order_id = int(call.data.split('_')[1])
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(order_id)
    qr.make()
    img = qr.make_image(fill_color="black", back_color="white")
    img.save("QR.png")
    with open("QR.png", 'rb') as photo:
        bot.send_photo(call.message.chat.id, photo)
    os.remove("QR.png")
    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        cursor.execute('''
            UPDATE Orders
            SET status_id = 4,
                timestamp_update = ?
            WHERE id = ?
        ''', (time.time(), order_id))
        db.commit()
    department_id = get_department_by_telegram_id(call.message.chat.id)

    send_welcome_message(call.message, department_id)

@bot.message_handler(func=lambda message: message.text == 'Считать qr код')
def read_qr_code(message):
    bot.send_message(message.chat.id, 'Отправьте фото qr кода', reply_markup=none_keyboard)
    bot.register_next_step_handler(message, handle_qr)

@bot.message_handler(content_types=['photo'])
def handle_qr(message):
    photo = message.photo[-1]
    file_id = photo.file_id
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    department_id = get_department_by_telegram_id(message.chat.id)

    with open("qr_code.png", "wb") as new_file:
        new_file.write(downloaded_file)

    qrImg = cv2.imread("qr_code.png")
    if qrImg is None:
        bot.send_message(message.chat.id, "Не удалось загрузить изображение")
        send_welcome_message(message, department_id)
    else:
        qcd = cv2.QRCodeDetector()
        decode_data, bbox, straight_qrcode = qcd.detectAndDecode(qrImg)

        if bbox is not None:
            with sqlite3.connect(db_path) as db:
                cursor = db.cursor()
                cursor.execute('''
                            SELECT 
                                Orders.id AS order_id,
                                Orders.name AS order_name,
                                Orders.order_date,
                                Orders.planned_delivery_date,
                                Statuses.name AS status_name,
                                Managers.full_name AS manager_name,
                                Customers.full_name AS customer_name,
                                Customers.phone,
                                OrderItems.quantity,
                                Items.name AS item_name
                            FROM Orders
                            JOIN Statuses ON Orders.status_id = Statuses.id
                            JOIN Managers ON Orders.manager_id = Managers.id
                            JOIN Customers ON Orders.customer_id = Customers.id
                            JOIN OrderItems ON Orders.id = OrderItems.order_id
                            JOIN Items ON OrderItems.item_id = Items.id
                            WHERE order_id = ?
                            ''', (decode_data,))

                result = cursor.fetchall()
                
                if not result:
                    bot.send_message(message.chat.id, "Вы отправили некорректный qr код")
                    send_welcome_message(message, department_id)
                else:
                    order_details = {
                        'order_name': result[0][1],
                        'order_date': result[0][2],
                        'planned_delivery_date': result[0][3],
                        'status_name': result[0][4],
                        'manager_name': result[0][5],
                        'customer_name': result[0][6],
                        'customer_phone': result[0][7],
                        'order_items': []
                    }

                    for row in result:
                        order_items_details = {'item_name': row[9], 'quantity': row[8]}
                        order_details['order_items'].append(order_items_details)

                    output = (
                        f"Название заказа: {order_details['order_name']}\n"
                        f"Дата заказа: {order_details['order_date']}\n"
                        f"Плановая дата доставки: {order_details['planned_delivery_date']}\n"
                        f"Статус: {order_details['status_name']}\n"
                        f"Менеджер: {order_details['manager_name']}\n"
                        "Клиент:\n"
                        f"  Полное имя: {order_details['customer_name']}\n"
                        f"  Телефон: {order_details['customer_phone']}\n"
                        "Состав заказа:\n"
                    )

                    for item in order_details['order_items']:
                        output += f"- {item['item_name']}: {item['quantity']}\n"
                    bot.send_message(message.chat.id, output)
                    with sqlite3.connect(db_path) as db:
                        cursor = db.cursor()
                        cursor.execute('''
                                UPDATE Orders
                                SET status_id = 6,
                                    timestamp_update = ?
                                WHERE id = ?
                        ''', (time.time(), result[0][0]))
                        db.commit()
                    send_welcome_message(message, department_id)

        else:
            bot.send_message(message.chat.id, "QR код не распознан")
            send_welcome_message(message, department_id)
    os.remove("qr_code.png")

@bot.message_handler(func=lambda message: message.text == "Оповещение о задержке")
def delivery_delay(message):
    department_id = get_department_by_telegram_id(message.chat.id)
    
    with sqlite3.connect(db_path) as db:
                cursor = db.cursor()
                cursor.execute('''
                    SELECT 
                        Orders.id AS order_id,
                        Orders.name AS order_name
                    FROM Orders
                    WHERE Orders.status_id >= 7
                ''')

                result = cursor.fetchall()
                if not result:
                    bot.send_message(message.chat.id, "В базе отсутствуют заказы")
                    send_welcome_message(message, department_id)
                else:
                    inline_keyboard = types.InlineKeyboardMarkup()
                    for row in result:
                        order_id = row[0]
                        order_name = row[1]
                        button = types.InlineKeyboardButton(text=f"Заказ №{order_id}", callback_data=f'delivery_{order_id}')
                        inline_keyboard.add(button)
                    bot.send_message(message.chat.id, 'Выберите заказ', reply_markup=inline_keyboard)

def handle_order_delivery(call):
    order_id = int(call.data.split('_')[1])
    department_id = get_department_by_telegram_id(call.message.chat.id)

    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        cursor.execute('''
                       UPDATE Orders
                       SET status_id = 10,
                           timestamp_update = ?
                       WHERE id = ?
                       ''', (time.time(), order_id))
        db.commit()
        cursor.execute('''
                    SELECT 
                        Orders.id AS order_id,
                        Orders.name,
                        Customers.full_name AS customer_name,
                        Customers.phone,
                        Customers.telegram_id
                    FROM Orders
                    JOIN Customers ON Orders.customer_id = Customers.id
                    WHERE Orders.id = ?;
                ''', (order_id,))
        result = cursor.fetchone()
        bot.send_message(call.message.chat.id, f'Уведомление {result[2]} отправлено. Номер для связи с клиентом: {result[3]}')
    send_welcome_message(call.message, department_id)

def handle_newdep_delivery(call):
    department_id = int(call.data.split('_')[1])
    
    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        cursor.execute('UPDATE Workers SET department_id = ? WHERE telegram_id = ?', (department_id, call.message.chat.id,))
        db.commit()
        bot.send_message(call.message.chat.id, f"Вы успешно изменили роль!")
        send_welcome_message(call.message, department_id)

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logging.error(e)