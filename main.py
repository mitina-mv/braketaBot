import logging
import telebot
from telebot import types
import os

token = os.environ.get("TOKEN")

bot=telebot.TeleBot(token)
@bot.message_handler(commands=['start'])
def start_message(message):
  bot.send_message(message.chat.id,"Привет ✌️ ")


@bot.message_handler(commands=['button'])
def button_message(message):
  markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
  item1=types.KeyboardButton("Кнопка")
  markup.add(item1)
  markup.add(item1)
  bot.send_message(message.chat.id,'Выберите что вам надо',reply_markup=markup)

bot.polling(none_stop=True)

# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     level=logging.INFO
# )

# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

# if __name__ == '__main__':
#     application = ApplicationBuilder().token(token).build()
    
#     start_handler = CommandHandler('start', start)
#     application.add_handler(start_handler)
    
#     application.run_polling()