import logging
import telebot
from telebot import types
import os
import sqlite3
import qrcode
import cv2

token = os.environ.get("TOKEN")
db_path = 'braketaDB.db'

bot = telebot.TeleBot(token)

keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
generate_qr = telebot.types.KeyboardButton(text="Сгенерировать qr код")
read_qr = telebot.types.KeyboardButton(text="Считать qr код")
keyboard.add(generate_qr, read_qr)

none_keyboard = telebot.types.ReplyKeyboardRemove()

@bot.message_handler(commands=['start'])
def start_message(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Добро пожаловать в бота для сотрудников НЛМК', reply_markup=keyboard)
    
@bot.message_handler(func=lambda message: message.text == 'Сгенерировать qr код')
def generate_qr_code(message):
    chat_id = message.chat.id
    
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
                    bot.send_message(chat_id, "В базе отсутствуют заказы", reply_markup=keyboard)
                else:
                    inline_keyboard = types.InlineKeyboardMarkup()
                    for row in result:
                        order_id = row[0]
                        order_name = row[1]
                        button = types.InlineKeyboardButton(text=order_name, callback_data=f'order_{order_id}')
                        inline_keyboard.add(button)
                    bot.send_message(chat_id, 'Выберите заказ', reply_markup=inline_keyboard)
    
                    @bot.callback_query_handler(func=lambda call: True)
                    def handle_order_selection(call):
                        order_id = int(call.data.split('_')[1])
                        qr = qrcode.QRCode(version=1, box_size=10, border=4)
                        qr.add_data(order_id)
                        qr.make()
                        img = qr.make_image(fill_color="black", back_color="white")
                        img.save("QR.png")
                        with open("QR.png", 'rb') as photo:
                            bot.send_photo(chat_id, photo)
                        os.remove("QR.png")
    
@bot.message_handler(func=lambda message: message.text == 'Считать qr код')
def read_qr_code(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Отправьте фото qr кода', reply_markup=none_keyboard)
    bot.register_next_step_handler(message, handle_qr)
    
@bot.message_handler(content_types=['photo'])
def handle_qr(message):
    photo = message.photo[-1]
    file_id = photo.file_id
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with open("qr_code.png", "wb") as new_file:
        new_file.write(downloaded_file)

    qrImg = cv2.imread("qr_code.png")
    if qrImg is None:
        bot.send_message(message.chat.id, "Не удалось загрузить изображение", reply_markup=keyboard)
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
                            WHERE Orders.id = ?;
                            ''', (decode_data,))

                result = cursor.fetchall()
                if not result:
                    bot.send_message(message.chat.id, "Вы отправили некорректный qr код", reply_markup=keyboard)
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
                    bot.send_message(message.chat.id, output, reply_markup=keyboard)

        else:
            bot.send_message(message.chat.id, "QR код не распознан", reply_markup=keyboard)
    os.remove("qr_code.png")

bot.polling(none_stop=True)
