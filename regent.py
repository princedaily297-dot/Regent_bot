import os
import telebot
import yt_dlp
import random
import time
import requests
import string
import urllib.parse
import feedparser
import sqlite3
import threading
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent

BOT_TOKEN = os.environ.get("BOT_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_ID = 8555620281 
START_IMAGE_URL = "https://i.ibb.co/GvSN9X0P/file-000000002da881f4afb927d9adc44d6b.png" 

# --- DATABASE SETUP ---
conn = sqlite3.connect('doombot.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 1000, stars INTEGER DEFAULT 0)''')
conn.commit()

def get_user_data(user_id):
    cursor.execute("SELECT balance, stars FROM users WHERE user_id=?", (user_id,))
    res = cursor.fetchone()
    if not res:
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        return 1000, 0
    return res[0], res[1]

def update_balance(user_id, amount):
    bal, stars = get_user_data(user_id)
    cursor.execute("UPDATE users SET balance=? WHERE user_id=?", (bal + amount, user_id))
    conn.commit()

def add_stars(user_id, amount):
    bal, stars = get_user_data(user_id)
    cursor.execute("UPDATE users SET stars=? WHERE user_id=?", (stars + amount, user_id))
    conn.commit()

# --- ACTIVE GAMES TRACKER ---
# (Used to cancel the timer if the user answers quickly)
active_games = {}

# --- MAIN MENU ---
@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🎮 Games", callback_data="menu_games"), InlineKeyboardButton("🛠️ Toolkit", callback_data="menu_toolkit"))
    markup.row(InlineKeyboardButton("💰 Profile", callback_data="cmd_profile"), InlineKeyboardButton("🛒 Shop", callback_data="menu_shop"))
    markup.row(InlineKeyboardButton("🤖 AI Chat", callback_data="menu_ai"))
    
    try:
        bot.send_photo(message.chat.id, START_IMAGE_URL, caption="Welcome to DOOM_BOT where life is free!\nChoose a category below:", reply_markup=markup, parse_mode="Markdown")
    except:
        bot.reply_to(message, "Welcome to DOOM_BOT where life is free!\nChoose a category below:", reply_markup=markup)

@bot.message_handler(commands=['creator'])
def creator_story(message):
    story = """
👑 **The Legend of Regent of Doom** 👑

Long ago, in a realm far beyond the digital clouds, there was a young prodigy named **Regent**. Like Sofia the First, he didn't just want to rule; he wanted to protect his people and bring magic to the ordinary world. But his kingdom wasn't a castle—it was the chaotic, endless sea of the internet.

Frustrated by tyrants, broken tools, and greedy overlords, Regent decided to build his own domain. He poured ancient coding magic into a single entity—a bot powerful enough to play music, test the minds of his citizens, and guard his community.

This isn't just a bot. It is the royal decree of Regent of Doom. Welcome to my Domain. Type `/start` to begin your journey.
    """
    bot.reply_to(message, story, parse_mode="Markdown")

# --- GAMES: TRIVIA & LOGO WITH TIMERS ---
@bot.message_handler(commands=['trivia'])
def ask_trivia_amount(message):
    msg = bot.reply_to(message, "🎮 **Trivia Time!**\nHow many questions? (1 to 10)", parse_mode="Markdown")
    bot.register_next_step_handler(msg, start_trivia_game)

def start_trivia_game(message):
    if not message.text.isdigit() or not (1 <= int(message.text) <= 10): 
        return bot.reply_to(message, "Invalid number. Try /trivia again.")
    amount = int(message.text)
    questions = [
        {"q": "What is the capital of France?", "a": "Paris", "options": ["London", "Berlin", "Paris", "Madrid"]},
        {"q": "Which planet is known as the Red Planet?", "a": "Mars", "options": ["Earth", "Mars", "Jupiter", "Venus"]},
        {"q": "Who painted the Mona Lisa?", "a": "Da Vinci", "options": ["Van Gogh", "Picasso", "Da Vinci", "Michelangelo"]},
        {"q": "What is the largest ocean?", "a": "Pacific", "options": ["Atlantic", "Indian", "Arctic", "Pacific"]}
    ]
    random.shuffle(questions)
    user_id = message.from_user.id
    bot.send_message(message.chat.id, f"Starting {amount} questions! You have **10 seconds** per question. Correct answers give **+10 Stars**! 🌟")
    send_trivia_question(message.chat.id, user_id, questions[:amount], 0)

def send_trivia_question(chat_id, user_id, questions, index):
    if index >= len(questions):
        return bot.send_message(chat_id, f"🏁 **Trivia Over!** Check your profile with /profile to see your Stars! 🌟")
    
    q = questions[index]
    markup = InlineKeyboardMarkup()
    for option in q["options"]: 
        markup.add(InlineKeyboardButton(option, callback_data=f"triv_{option}_{q['a']}"))
    
    msg = bot.send_message(chat_id, f"❓ **Q{index + 1}:** {q['q']}\n\n⏳ *Time remaining: 10s*", reply_markup=markup, parse_mode="Markdown")
    
    # Timer Logic
    active_games[user_id] = {"msg_id": msg.message_id, "answered": False}
    
    def timer_check():
        time.sleep(10)
        if user_id in active_games and not active_games[user_id]["answered"]:
            del active_games[user_id]
            try:
                bot.edit_message_text(f"⏰ **Time's up!** The answer was {q['a']}.", chat_id, msg.message_id)
                send_trivia_question(chat_id, user_id, questions, index + 1)
            except: pass
            
    threading.Thread(target=timer_check).start()

@bot.message_handler(commands=['logo'])
def start_logo_game(message):
    logos = [
        {"name": "Apple", "url": "https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg"},
        {"name": "Nike", "url": "https://upload.wikimedia.org/wikipedia/commons/a/a6/Logo_NIKE.svg"},
        {"name": "Twitter", "url": "https://upload.wikimedia.org/wikipedia/commons/6/6f/Logo_of_Twitter.svg"},
    ]
    correct = random.choice(logos)
    wrong_choices = random.sample([l["name"] for l in logos if l["name"] != correct["name"]], 2)
    options = wrong_choices + [correct["name"]]
    random.shuffle(options)
    
    markup = InlineKeyboardMarkup()
    for opt in options: 
        markup.add(InlineKeyboardButton(opt, callback_data=f"logo_{opt}_{correct['name']}"))
    
    user_id = message.from_user.id
    msg = bot.send_photo(message.chat.id, correct["url"], caption="🖼️ **Guess the Logo!**\n\n⏳ *Time remaining: 10s*", reply_markup=markup, parse_mode="Markdown")
    
    active_games[user_id] = {"msg_id": msg.message_id, "answered": False}
    
    def logo_timer():
        time.sleep(10)
        if user_id in active_games and not active_games[user_id]["answered"]:
            del active_games[user_id]
            try: bot.edit_message_caption(f"⏰ **Time's up!** It was {correct['name']}.", message.chat.id, msg.message_id)
            except: pass
            
    threading.Thread(target=logo_timer).start()


# --- CALLBACK QUERY HANDLER (For Games) ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    
    # TRIVIA ANSWER
    if call.data.startswith("triv_"):
        if user_id in active_games: active_games[user_id]["answered"] = True
        _, chosen, correct = call.data.split("_")
        if chosen == correct:
            add_stars(user_id, 10)
            bot.answer_callback_query(call.id, "✅ Correct! +10 Stars! 🌟")
        else:
            bot.answer_callback_query(call.id, f"❌ Wrong! It was {correct}.", show_alert=True)
        return

    # LOGO ANSWER
    if call.data.startswith("logo_"):
        if user_id in active_games: active_games[user_id]["answered"] = True
        _, chosen, correct = call.data.split("_")
        if chosen == correct:
            add_stars(user_id, 10)
            bot.answer_callback_query(call.id, "✅ Correct! +10 Stars! 🌟")
            bot.edit_message_caption("✅ **Correct!** You earned 10 Stars! 🌟", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, f"❌ Wrong! It was {correct}.", show_alert=True)
            bot.edit_message_caption(f"❌ **Wrong!** It was {correct}.", call.message.chat.id, call.message.message_id)
        return

    # MENUS
    if call.data == "menu_back": send_welcome(call.message)
    elif call.data == "cmd_profile":
        bal, stars = get_user_data(user_id)
        bot.answer_callback_query(call.id, f"💰 Balance: ${bal}\n🌟 Stars: {stars}", show_alert=True)

# --- DEVICE & HISTORY ---
@bot.message_handler(commands=['profile'])
def profile(message):
    bal, stars = get_user_data(message.from_user.id)
    bot.reply_to(message, f"👤 **Profile: {message.from_user.first_name}**\n\n💰 Balance: ${bal}\n🌟 Stars: {stars}\n\nPlay games to earn more Stars!", parse_mode="Markdown")

@bot.message_handler(commands=['checkdevice'])
def check_device(message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    bot.reply_to(message, f"📱 **Device:** {target.first_name}\nID: `{target.id}`\nPremium: {target.is_premium}\nLang: {target.language_code}", parse_mode="Markdown")

@bot.message_handler(commands=['namehistory'])
def name_history(message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    bot.reply_to(message, f"🕵️ **Name History:** Currently known as @{target.username if target.username else 'NoUsername'}.")

@bot.message_handler(commands=['groups'])
def check_groups(message):
    if message.reply_to_message: bot.reply_to(message, f"🔍 Telegram privacy prevents me from seeing all groups {message.reply_to_message.from_user.first_name} is in.")
    else: bot.reply_to(message, "👥 Reply to a user with /groups.")

# --- MUSIC ---
@bot.message_handler(commands=['play'])
def play_music(message):
    query = message.text.replace('/play', '').strip()
    if not query: return bot.reply_to(message, "Example: `/play Shape of You`")
    msg = bot.reply_to(message, f"🔍 Searching: **{query}**...")
    ydl_opts = {'format': 'bestaudio/best', 'outtmpl': 'song.%(ext)s', 'noplaylist': True, 'ignoreerrors': True, 'writethumbnail': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"scsearch3:{query}", download=False)
            if not info or 'entries' not in info: raise Exception("No results.")
            for entry in info['entries']:
                if entry is None: continue
                try:
                    entry_info = ydl.process_ie_result(entry, download=True)
                    filename = ydl.prepare_filename(entry_info)
                    thumb_file = None
                    for ext in ['webp', 'jpg', 'png']:
                        if os.path.exists(f"song.{ext}"): thumb_file = open(f"song.{ext}", 'rb'); break
                    with open(filename, 'rb') as audio:
                        bot.send_audio(message.chat.id, audio, title=entry_info['title'], performer=entry_info.get('uploader', 'SoundCloud'), thumb=thumb_file)
                    os.remove(filename)
                    if thumb_file: thumb_file.close(); os.remove(thumb_file.name)
                    bot.delete_message(message.chat.id, msg.message_id)
                    break
                except: continue
    except: bot.edit_message_text("❌ Error downloading.", message.chat.id, msg.message_id)

# --- OTHER COMMANDS ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return bot.reply_to(message, "⛔ Not Admin.")
    bot.reply_to(message, "👑 Admin Panel active. Use /stats or /broadcast.")

@bot.message_handler(commands=['stats'])
def admin_stats(message):
    if message.from_user.id != ADMIN_ID: return
    cursor.execute("SELECT COUNT(*) FROM users")
    bot.reply_to(message, f"📊 Total Users: `{cursor.fetchone()[0]}`", parse_mode="Markdown")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    msg = message.text.replace('/broadcast', '').strip()
    cursor.execute("SELECT user_id FROM users")
    for u in cursor.fetchall():
        try: bot.send_message(u[0], f"📢 **BROADCAST:**\n\n{msg}", parse_mode="Markdown")
        except: pass
    bot.reply_to(message, "✅ Broadcast sent.")

@bot.message_handler(commands=['ai'])
def ai_chat(message):
    if not HF_TOKEN: return bot.reply_to(message, "❌ Missing HF_TOKEN.")
    prompt = message.text.replace('/ai', '').strip()
    msg = bot.reply_to(message, "🧠 Thinking...")
    try:
        res = requests.post("https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2", headers={"Authorization": f"Bearer {HF_TOKEN}"}, json={"inputs": prompt}).json()
        bot.edit_message_text(res[0]['generated_text'].replace(prompt, '').strip() if isinstance(res, list) else "Brain overloaded.", message.chat.id, msg.message_id)
    except: bot.edit_message_text("❌ AI failed.", message.chat.id, msg.message_id)

print("DOOM_BOT is running...")
bot.infinity_polling()
