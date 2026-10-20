import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🎮 Trivia", callback_data="trivia"), 
               InlineKeyboardButton("⚙️ Button editor", callback_data="btn_editor"))
    markup.row(InlineKeyboardButton("🔨 Ban tool", callback_data="ban_tool"))
    markup.row(InlineKeyboardButton("✏️ Posts Editor", callback_data="posts"), 
               InlineKeyboardButton("💰 Balance", callback_data="balance"))
    markup.row(InlineKeyboardButton("🔒 Admin", callback_data="admin"))
    bot.reply_to(message, "Welcome to Regent Domain where life is free!", reply_markup=markup)

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "Here is the help menu. Use /start to see the main options.")

@bot.message_handler(commands=['ping'])
def send_ping(message):
    bot.reply_to(message, "🏓 Pong! The bot is online and fast.")

@bot.message_handler(commands=['id'])
def send_id(message):
    bot.reply_to(message, f"Your Telegram ID is: {message.from_user.id}")

@bot.message_handler(commands=['play', 'namehistory', 'checkdevice', 'trivia', 'buttons', 'ban', 'posts', 'balance', 'admin'])
def coming_soon(message):
    bot.reply_to(message, f"The {message.text} feature is under construction!")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "trivia":
        bot.answer_callback_query(call.id, "Trivia game is coming soon!")
    elif call.data == "balance":
        bot.answer_callback_query(call.id, "Your balance is $0.00")
    else:
        bot.answer_callback_query(call.id, "This feature is under construction.")

print("Bot is running...")
bot.infinity_polling()
