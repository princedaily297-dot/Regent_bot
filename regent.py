import os
import telebot
import yt_dlp
import random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# A temporary memory to store user balances (resets when bot restarts)
user_balances = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🎮 Trivia", callback_data="cmd_trivia"), 
               InlineKeyboardButton("⚙️ Button editor", callback_data="btn_editor"))
    markup.row(InlineKeyboardButton("🔨 Ban tool", callback_data="ban_tool"))
    markup.row(InlineKeyboardButton("✏️ Posts Editor", callback_data="posts"), 
               InlineKeyboardButton("💰 Balance", callback_data="cmd_balance"))
    markup.row(InlineKeyboardButton("🔒 Admin", callback_data="admin"))
    bot.reply_to(message, "Welcome to Regent Domain where life is free!", reply_markup=markup)

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "Use /play <song name> for music, /trivia for a game, or /balance!")

@bot.message_handler(commands=['ping'])
def send_ping(message):
    bot.reply_to(message, "🏓 Pong! The bot is online and fast.")

@bot.message_handler(commands=['id'])
def send_id(message):
    bot.reply_to(message, f"Your Telegram ID is: {message.from_user.id}")

@bot.message_handler(commands=['checkdevice'])
def check_device(message):
    # Telegram hides exact device models, but we can check OS via language or flags
    user = message.from_user
    is_premium = "Yes (Premium User)" if user.is_premium else "No (Free User)"
    bot.reply_to(message, f"📱 **Device Info:**\nUser ID: {user.id}\nName: {user.first_name}\nTelegram Premium: {is_premium}\nLanguage: {user.language_code}")

@bot.message_handler(commands=['play'])
def play_music(message):
    query = message.text.replace('/play', '').strip()
    if not query:
        bot.reply_to(message, "Please provide a song name. Example:\n`/play Shape of You`", parse_mode="Markdown")
        return
    
    msg = bot.reply_to(message, f"🔍 Searching and downloading: **{query}**...", parse_mode="Markdown")
    
    # Configure YouTube downloader
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio',
        'outtmpl': 'song.%(ext)s',
        'noplaylist': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Search YouTube and get the first result
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)['entries'][0]
            filename = ydl.prepare_filename(info)
            
        with open(filename, 'rb') as audio:
            bot.send_audio(message.chat.id, audio, title=info['title'], performer="YouTube")
            
        os.remove(filename) # Delete the file after sending to save space
        bot.delete_message(message.chat.id, msg.message_id) # Delete the "Searching" message
        
    except Exception as e:
        bot.edit_message_text(f"❌ Failed to download. YouTube might be blocking the server.", message.chat.id, msg.message_id)

@bot.message_handler(commands=['balance'])
def check_balance(message):
    user_id = message.from_user.id
    if user_id not in user_balances:
        user_balances[user_id] = 1000 # Give new users $1000
    
    bot.reply_to(message, f"💰 Your current balance is: **${user_balances[user_id]}**", parse_mode="Markdown")

@bot.message_handler(commands=['trivia'])
def start_trivia(message):
    questions = [
        {"q": "What is the capital of France?", "a": "Paris", "options": ["London", "Berlin", "Paris", "Madrid"]},
        {"q": "Which planet is known as the Red Planet?", "a": "Mars", "options": ["Earth", "Mars", "Jupiter", "Venus"]},
        {"q": "Who painted the Mona Lisa?", "a": "Leonardo da Vinci", "options": ["Van Gogh", "Picasso", "Da Vinci", "Michelangelo"]}
    ]
    
    q = random.choice(questions)
    markup = InlineKeyboardMarkup()
    
    # Create a button for each option
    for option in q["options"]:
        markup.add(InlineKeyboardButton(option, callback_data=f"trivia_{option}_{q['a']}"))
        
    bot.reply_to(message, f"🎮 **Trivia Time!**\n\n{q['q']}", reply_markup=markup, parse_mode="Markdown")

# This handles all button clicks
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    # Handle Trivia Answers
    if call.data.startswith("trivia_"):
        _, chosen, correct = call.data.split("_")
        if chosen == correct:
            bot.answer_callback_query(call.id, "✅ Correct! You win $50!")
            # Add balance
            user_id = call.from_user.id
            user_balances[user_id] = user_balances.get(user_id, 1000) + 50
        else:
            bot.answer_callback_query(call.id, f"❌ Wrong! The answer was {correct}.", show_alert=True)
        return

    # Handle Main Menu Buttons
    if call.data == "cmd_trivia":
        start_trivia(call.message)
    elif call.data == "cmd_balance":
        check_balance(call.message)
    else:
        bot.answer_callback_query(call.id, "This feature is still under construction!")

print("Bot is running...")
bot.infinity_polling()
