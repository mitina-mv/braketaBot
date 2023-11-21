import logging
# import telebot
# from telebot import types
import os

# token = os.environ.get("TOKEN")

# bot=telebot.TeleBot(token)
# @bot.message_handler(commands=['start'])
# def start_message(message):
#   bot.send_message(message.chat.id,"Привет ✌️ ")


# @bot.message_handler(commands=['button'])
# def button_message(message):
#   markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
#   item1=types.KeyboardButton("Кнопка")
#   markup.add(item1)
#   markup.add(item1)
#   bot.send_message(message.chat.id,'Выберите что вам надо',reply_markup=markup)

# bot.polling(none_stop=True)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
# import telegram
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters, MessageHandler

# Замените 'YOUR_BOT_TOKEN' на токен вашего бота
TOKEN = os.environ.get("TOKEN")

# Обработка команды /start с использованием клавиатуры
# def start(update: Update, context: CallbackContext) -> None:
#     keyboard = [['Button 1', 'Button 2'], ['Button 3', 'Button 4']]
#     reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
#     update.message.reply_text('Выберите опцию:', reply_markup=reply_markup)

# def button_click(update: Update, context: CallbackContext) -> None:
#     text = update.message.text
#     update.message.reply_text(f'Вы нажали на кнопку: {text}')

# def main() -> None:
#     dp = ApplicationBuilder().token(TOKEN).build()

#     # Обработка команды /start
#     dp.add_handler(CommandHandler("start", start))
    
#     # Обработка нажатий на кнопки
#     dp.add_handler(MessageHandler(Filters.text & ~Filters.command, button_click))

#     # Запуск бота
#     dp.run_polling()

# if __name__ == '__main__':
#     main()

# async def start(update: Update, context: CallbackContext) -> None:
#     keyboard = [['Button 1', 'Button 2'], ['Button 3', 'Button 4']]
#     reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
#     update.message.reply_text('Выберите опцию:', reply_markup=reply_markup)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['Button 1', 'Button 2'], ['Button 3', 'Button 4']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Выберите опцию:", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_button = update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Вы нажали на кнопку: {text_button}')

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    application.add_handler(MessageHandler(filters.text & ~filters.command, button_click))
    
    application.run_polling()