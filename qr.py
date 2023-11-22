

# data = "787"

# qr = qrcode.QRCode(version=1, box_size=10, border=4)
# qr.add_data(data)
# qr.make()
# img = qr.make_image(fill_color="black", back_color="white")
# img.save("QR.png")


# qrImg = cv2.imread('QR.png')
# if qrImg is None:
#     print("Не удалось загрузить изображение")
# else:
#     qcd = cv2.QRCodeDetector()
#     decode_data, bbox, straight_qrcode = qcd.detectAndDecode(qrImg)
#     if bbox is not None:
#         print(decode_data)
#     else:
#         print("QR код не распознан")

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

@bot.message_handler(commands=['start'])
def start_message(message):
    chat_id = message.chat.id
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    generate_qr = telebot.types.KeyboardButton(text="Сгенерировать qr код")
    read_qr = telebot.types.KeyboardButton(text="Считать qr код")
    keyboard.add(generate_qr, read_qr)
    bot.send_message(chat_id, 'Добро пожаловать в бота для сотрудников НЛМК', reply_markup=keyboard)
    
@bot.message_handler(func=lambda message: message.text == 'Сгенерировать qr код')
def generate_qr_code(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Введите своё имя')
    users[chat_id] = {}
    bot.register_next_step_handler(message, save_username)
    
@bot.message_handler(func=lambda message: message.text == 'Считать qr код')
def read_qr_code(message):
    chat_id = message.chat.id
    keyboard = telebot.types.ReplyKeyboardRemove()
    bot.send_message(chat_id, 'Отправьте фото qr кода', reply_markup=keyboard)
    bot.register_next_step_handler(message, handle_qr)
    
@bot.message_handler(content_types=['photo'])
def handle_qr(message):
    if message.photo[-1].file_id not in photo_list:
        photo_list.append(message.photo[-1].file_id)
        if len(photo_list) == 1:
            send = bot.send_message(message.from_user.id, "Photos received...")
            bot.register_next_step_handler(send, process_messages())
            return
    
    # telegram_id = message.from_user.id
    # with sqlite3.connect(db_path) as db:
    #     cursor = db.cursor()
    #     cursor.execute('SELECT * FROM Customers WHERE telegram_id = ?', (telegram_id,))
    #     user_data = cursor.fetchone()
    #     user['telegram_id'] = telegram_id

    # if user_data:
    #     bot.send_message(message.chat.id, f"Привет {user_data[1]} ✌️  \nДобро пожаловать в систему!")
    # else:
    #     contact_button(message.chat.id)

# def contact_button(chat_id):
#     markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
#     button = types.KeyboardButton("Поделиться контактом", request_contact=True)
#     markup.add(button)
#     bot.send_message(chat_id, "Поделитесь своим контактом, нажав кнопку ниже.", reply_markup=markup)

# def get_full_name(chat_id):
#     bot.send_message(chat_id, "Введите ваше полное имя: ")
#     # This message should be handled in a separate function

# @bot.message_handler(content_types=['text'])
# def handle_full_name(message):
#     full_name = message.text
#     user['full_name'] = full_name
    
#     with sqlite3.connect(db_path) as db:
#         cursor = db.cursor()
#         cursor.execute('INSERT INTO Customers (full_name, phone, telegram_id) VALUES (?, ?, ?)', (user['full_name'], user['phone_number'], user['telegram_id'],))
#         db.commit()
#     bot.send_message(message.chat.id, f"Спасибо за предоставленное имя: {full_name}")

# @bot.message_handler(content_types=['contact'])
# def handle_contact(message):
#     contact = message.contact
#     phone_number = contact.phone_number
#     user['phone_number'] = phone_number
#     bot.send_message(message.chat.id, f"Спасибо за предоставленный контакт: {phone_number}")
#     get_full_name(message.chat.id)

# @bot.message_handler(commands=['button'])
# def button_message(message):
#     markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
#     item1 = types.KeyboardButton("Кнопка")
#     markup.add(item1, item1)
#     markup.add(item1)
#     bot.send_message(message.chat.id, 'Выберите что вам надо', reply_markup=markup)

bot.polling(none_stop=True)
