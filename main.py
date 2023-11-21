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
db = sqlite3.connect('braketaDB.db')
cursor = db.cursor()

bot=telebot.TeleBot(token)

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id,"Привет ✌️  \n Бот начал работать!")
    telegram_id = message.from_user.id
    cursor.execute('SELECT * FROM Customers WHERE telegram_id = ?', (telegram_id,))
    user_data = cursor.fetchone()

bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    # Отправка клавиатуры с запросом контакта
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = types.KeyboardButton("Поделиться контактом", request_contact=True)
    markup.add(button)

    bot.send_message(message.chat.id, "Поделитесь своим контактом, нажав кнопку ниже.", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    # Обработка полученного контакта
    contact = message.contact
    phone_number = contact.phone_number
    user_id = message.from_user.id

    bot.send_message(message.chat.id, f"Спасибо за предоставленный контакт: {phone_number}")

@bot.message_handler(commands=['button'])
def button_message(message):
  markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
  item1=types.KeyboardButton("Кнопка")
  markup.add(item1, item1)
  markup.add(item1)
  bot.send_message(message.chat.id,'Выберите что вам надо',reply_markup=markup)

bot.polling(none_stop=True)

____
import telebot
from telebot import types
import os

token = os.environ.get("TOKEN")

bot = telebot.TeleBot(token)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    # Ваш код, который будет выполняться при каждом получении сообщения
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = types.KeyboardButton("Поделиться контактом", request_contact=True)
    markup.add(button)

    bot.send_message(message.chat.id, "Поделитесь своим контактом, нажав кнопку ниже.", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    # Обработка полученного контакта
    contact = message.contact
    phone_number = contact.phone_number
    user_id = message.from_user.id

    bot.send_message(message.chat.id, f"Спасибо за предоставленный контакт: {phone_number}")

# Запуск бота
bot.polling(none_stop=True)