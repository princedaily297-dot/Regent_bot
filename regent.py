import os
import telebot
import yt_dlp
import random
import time
import requests
import string
import urllib.parse
import feedparser
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# Memory storage
user_balances = {}
trivia_state = {} 

# --- MAIN MENU & HELP ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🎮 Trivia", callback_data="cmd_trivia"), 
               InlineKeyboardButton("🖼️ Logo Game", callback_data="cmd_logo"))
    markup.row(InlineKeyboardButton("🎵 Play Music", callback_data="cmd_play"))
    markup.row(InlineKeyboardButton("💰 Balance", callback_data="cmd_balance"))
    bot.reply_to(message, "Welcome to Regent Domain where life is free!\nUse the buttons below or type /help to see all commands.", reply_markup=markup)

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
🤖 **Regent Bot Commands:**
**News & Story:** /news, /creator
**Group Admin:** /delete (reply to msg), /welcome (auto)
**Games:** /trivia, /logo, /roll, /flip, /8ball
**Utilities:** /weather <city>, /translate <lang> <text>, /qr <text>, /calc <math>, /bmi, /country, /color, /time
**Text Tools:** /font <text>, /reverse, /mock, /ascii
**Media:** /play <song>, /meme, /cat, /dog
**Fun:** /joke, /quote, /fact, /slap, /hug, /bug
**Stickers:** Just send a sticker to the bot to save it for WhatsApp!
    """
    bot.reply_to(message, help_text, parse_mode="Markdown")

# --- GROUP MANAGEMENT (WELCOME/GOODBYE) ---
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    for new_member in message.new_chat_members:
        if new_member.is_bot: continue
        bot.reply_to(message, f"👋 Welcome {new_member.first_name} to Regent Domain! Type /help to see my powers.")

@bot.message_handler(content_types=['left_chat_member'])
def goodbye_member(message):
    bot.send_message(message.chat.id, f"👋 Goodbye {message.left_chat_member.first_name}. The Domain will miss you.")

@bot.message_handler(commands=['delete'])
def delete_message(message):
    if message.chat.type == 'private':
        return bot.reply_to(message, "This command only works in groups.")
    if not message.reply_to_message:
        return bot.reply_to(message, "Reply to a message you want to delete.")
    try:
        bot.delete_message(message.chat.id, message.reply_to_message.message_id)
        bot.delete_message(message.chat.id, message.message_id) 
    except Exception:
        bot.reply_to(message, "❌ Failed. Make sure I am an admin with 'Delete Messages' permission.")

# --- CREATOR STORY & NEWS ---
@bot.message_handler(commands=['creator'])
def creator_story(message):
    story = """
👑 **The Legend of Regent of Doom** 👑

Long ago, in the digital shadows, a legend was born. **Regent of Doom** was not just a coder, but a visionary who saw the potential of bringing order to the chaos of the internet. Frustrated by bots that were slow, limited, or broken, Regent locked himself in his laboratory and forged this very bot. 

He poured his knowledge of Python into its core, giving it the power to play music, solve trivia, and manage communities. This bot is his legacy—a tool for the people, free from the chains of subscription fees. 

I am the Regent. And my Domain is open to you.
    """
    bot.reply_to(message, story, parse_mode="Markdown")

@bot.message_handler(commands=['news'])
def get_news(message):
    msg = bot.reply_to(message, "📰 Fetching latest news...")
    try:
        feed = feedparser.parse("https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en")
        articles = feed.entries[:5]
        text = "📰 **Latest Global News:**\n\n"
        for i, article in enumerate(articles):
            text += f"{i+1}. [{article.title}]({article.link})\n\n"
        bot.edit_message_text(text, message.chat.id, msg.message_id, parse_mode="Markdown", disable_web_page_preview=True)
    except:
        bot.edit_message_text("❌ Failed to fetch news.", message.chat.id, msg.message_id)

# --- STICKER SAVER ---
@bot.message_handler(content_types=['sticker'])
def handle_sticker(message):
    if message.chat.type != 'private':
        return bot.reply_to(message, "Please send stickers to me in a private message.")
    msg = bot.reply_to(message, "⏳ Saving sticker...")
    try:
        file_info = bot.get_file(message.sticker.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_name = "sticker.webp"
        with open(file_name, 'wb') as new_file:
            new_file.write(downloaded_file)
        with open(file_name, 'rb') as f:
            bot.send_document(message.chat.id, f, caption="✅ **Sticker saved!**\nDownload this file and import it to WhatsApp.", parse_mode="Markdown")
        os.remove(file_name)
        bot.delete_message(message.chat.id, msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)[:100]}", message.chat.id, msg.message_id)

# --- TEXT TOOLS ---
@bot.message_handler(commands=['font'])
def generate_font(message):
    text = message.text.replace('/font', '').strip()
    if not text: return bot.reply_to(message, "Example: `/font Hello World`", parse_mode="Markdown")
    normal = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    bold_lower, bold_upper = "𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳", "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙"
    cursive_lower, cursive_upper = "𝒶𝒷𝒸𝒹ℯ𝒻ℊ𝒽𝒾𝒿𝓀𝓁𝓂𝓃ℴ𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏", "𝒜ℬ𝒞𝒟ℰℱ𝒢ℋℐ𝒥𝒦ℒℳ𝒩𝒪𝒫𝒬ℛ𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵"
    def translate(txt, low, up):
        res = ""
        for char in txt:
            if char.islower() and char in normal: res += low[normal.index(char)]
            elif char.isupper() and char in normal: res += up[normal.index(char) - 26]
            else: res += char
        return res
    bot.reply_to(message, f"**Bold:**\n`{translate(text, bold_lower, bold_upper)}`\n\n**Cursive:**\n`{translate(text, cursive_lower, cursive_upper)}`", parse_mode="Markdown")

@bot.message_handler(commands=['reverse'])
def reverse_text(message):
    text = message.text.replace('/reverse', '').strip()
    bot.reply_to(message, text[::-1] if text else "Example: `/reverse Hello`", parse_mode="Markdown")

@bot.message_handler(commands=['mock'])
def mock_text(message):
    text = message.text.replace('/mock', '').strip()
    if not text: return bot.reply_to(message, "Example: `/mock Hello`", parse_mode="Markdown")
    bot.reply_to(message, "".join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(text)))

@bot.message_handler(commands=['ascii'])
def ascii_text(message):
    text = message.text.replace('/ascii', '').strip()
    if not text: return bot.reply_to(message, "Example: `/ascii Hello`", parse_mode="Markdown")
    try:
        res = requests.get(f"http://artii.herokuapp.com/make?text={urllib.parse.quote(text)}").text
        bot.reply_to(message, f"```\n{res}\n```", parse_mode="Markdown")
    except: bot.reply_to(message, "Failed to generate ASCII art.")

# --- UTILITIES ---
@bot.message_handler(commands=['weather'])
def get_weather(message):
    city = message.text.replace('/weather', '').strip()
    if not city: return bot.reply_to(message, "Example: `/weather London`", parse_mode="Markdown")
    try:
        res = requests.get(f"https://wttr.in/{city}?format=3").text
        bot.reply_to(message, f"🌍 {res}")
    except: bot.reply_to(message, "Could not fetch weather.")

@bot.message_handler(commands=['translate'])
def translate_text(message):
    parts = message.text.split(' ', 2)
    if len(parts) < 3: return bot.reply_to(message, "Example: `/translate es Hello World`", parse_mode="Markdown")
    lang, text = parts[1], parts[2]
    try:
        res = requests.get(f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair=en|{lang}").json()
        bot.reply_to(message, f"🌐 **Translation ({lang}):**\n{res['responseData']['translatedText']}", parse_mode="Markdown")
    except: bot.reply_to(message, "Translation failed.")

@bot.message_handler(commands=['qr'])
def generate_qr(message):
    text = message.text.replace('/qr', '').strip()
    if not text: return bot.reply_to(message, "Example: `/qr https://google.com`", parse_mode="Markdown")
    bot.send_photo(message.chat.id, f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(text)}", caption="📸 Scan this QR code!")

@bot.message_handler(commands=['calc'])
def calculator(message):
    expr = message.text.replace('/calc', '').strip()
    if not expr: return bot.reply_to(message, "Example: `/calc 5 * 10 + 2`", parse_mode="Markdown")
    try:
        result = eval(expr, {"__builtins__": None}, {})
        bot.reply_to(message, f"🧮 **Result:** `{result}`", parse_mode="Markdown")
    except: bot.reply_to(message, "Invalid math expression.")

@bot.message_handler(commands=['bmi'])
def calc_bmi(message):
    parts = message.text.replace('/bmi', '').strip().split()
    if len(parts) != 2: return bot.reply_to(message, "Example: `/bmi 70 1.75`", parse_mode="Markdown")
    try:
        w, h = float(parts[0]), float(parts[1])
        bmi = w / (h * h)
        bot.reply_to(message, f"⚖️ **Your BMI:** `{bmi:.1f}`\n{('Underweight' if bmi < 18.5 else 'Normal' if bmi < 25 else 'Overweight')}")
    except: bot.reply_to(message, "Invalid numbers.")

@bot.message_handler(commands=['country'])
def country_info(message):
    country = message.text.replace('/country', '').strip()
    if not country: return bot.reply_to(message, "Example: `/country Nigeria`", parse_mode="Markdown")
    try:
        res = requests.get(f"https://restcountries.com/v3.1/name/{country}?fullText=true").json()[0]
        bot.reply_to(message, f"🏳️ **{res['name']['common']}**\nCapital: {res['capital'][0]}\nPopulation: {res['population']:,}\nRegion: {res['region']}", parse_mode="Markdown")
    except: bot.reply_to(message, "Country not found.")

@bot.message_handler(commands=['color'])
def color_info(message):
    hex_code = message.text.replace('/color', '').strip().replace('#', '')
    if len(hex_code) != 6: return bot.reply_to(message, "Example: `/color FF0000`", parse_mode="Markdown")
    try:
        r, g, b = int(hex_code[0:2], 16), int(hex_code[2:4], 16), int(hex_code[4:6], 16)
        bot.send_photo(message.chat.id, f"https://dummyimage.com/300x200/{hex_code}/{hex_code}.png", caption=f"🎨 **Color:** #{hex_code}\nRGB: ({r}, {g}, {b})")
    except: bot.reply_to(message, "Invalid hex code.")

@bot.message_handler(commands=['time'])
def current_time(message):
    bot.reply_to(message, f"🕒 Server Time: **{datetime.now().strftime('%H:%M:%S')}**", parse_mode="Markdown")

# --- MUSIC ---
@bot.message_handler(commands=['play'])
def play_music(message):
    query = message.text.replace('/play', '').strip()
    if not query: return bot.reply_to(message, "Example: `/play Shape of You`", parse_mode="Markdown")
    msg = bot.reply_to(message, f"🔍 Searching for: **{query}**...", parse_mode="Markdown")
    ydl_opts = {'format': 'bestaudio/best', 'outtmpl': 'song.%(ext)s', 'noplaylist': True, 'ignoreerrors': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"scsearch3:{query}", download=False)
            if not info or 'entries' not in info: raise Exception("No results.")
            downloaded = False
            for entry in info['entries']:
                if entry is None: continue
                try:
                    entry_info = ydl.process_ie_result(entry, download=True)
                    filename = ydl.prepare_filename(entry_info)
                    with open(filename, 'rb') as audio:
                        bot.send_audio(message.chat.id, audio, title=entry_info['title'], performer=entry_info.get('uploader', 'SoundCloud'))
                    os.remove(filename)
                    bot.delete_message(message.chat.id, msg.message_id)
                    downloaded = True
                    break
                except Exception: continue
            if not downloaded: bot.edit_message_text("❌ Results were DRM-protected.", message.chat.id, msg.message_id)
    except Exception as e: bot.edit_message_text(f"❌ Error: {str(e)[:100]}", message.chat.id, msg.message_id)

# --- GAMES ---
@bot.message_handler(commands=['trivia'])
def ask_trivia_amount(message):
    msg = bot.reply_to(message, "🎮 **Trivia Time!**\nHow many questions? (1 to 10)", parse_mode="Markdown")
    bot.register_next_step_handler(msg, start_trivia_game)

def start_trivia_game(message):
    if not message.text.isdigit() or not (1 <= int(message.text) <= 10): return bot.reply_to(message, "Invalid number. Try /trivia again.")
    amount = int(message.text)
    questions = [
        {"q": "What is the capital of France?", "a": "Paris", "options": ["London", "Berlin", "Paris", "Madrid"]},
        {"q": "Which planet is known as the Red Planet?", "a": "Mars", "options": ["Earth", "Mars", "Jupiter", "Venus"]},
        {"q": "Who painted the Mona Lisa?", "a": "Da Vinci", "options": ["Van Gogh", "Picasso", "Da Vinci", "Michelangelo"]},
        {"q": "What is the largest ocean?", "a": "Pacific", "options": ["Atlantic", "Indian", "Arctic", "Pacific"]},
        {"q": "What year did World War II end?", "a": "1945", "options": ["1918", "1939", "1945", "1950"]},
        {"q": "What is the chemical symbol for gold?", "a": "Au", "options": ["Ag", "Au", "Fe", "Cu"]}
    ]
    random.shuffle(questions)
    user_id = message.from_user.id
    trivia_state[user_id] = {"questions": questions[:amount], "current": 0, "score": 0}
    send_trivia_question(message.chat.id, user_id)

def send_trivia_question(chat_id, user_id):
    state = trivia_state.get(user_id)
    if not state or state["current"] >= len(state["questions"]):
        score = state["score"] if state else 0
        total = len(state["questions"]) if state else 0
        user_balances[user_id] = user_balances.get(user_id, 1000) + (score * 50)
        bot.send_message(chat_id, f"🏁 **Game Over!**\nScore: {score}/{total}.\nEarned: ${score * 50}!\nCheck /balance", parse_mode="Markdown")
        if user_id in trivia_state: del trivia_state[user_id]
        return
    q = state["questions"][state["current"]]
    markup = InlineKeyboardMarkup()
    for option in q["options"]: markup.add(InlineKeyboardButton(option, callback_data=f"ans_{option}"))
    bot.send_message(chat_id, f"❓ **Q{state['current'] + 1}/{len(state['questions'])}:**\n\n{q['q']}", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['logo'])
def start_logo_game(message):
    logos = [
        {"name": "Apple", "url": "https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg"},
        {"name": "Nike", "url": "https://upload.wikimedia.org/wikipedia/commons/a/a6/Logo_NIKE.svg"},
        {"name": "McDonald's", "url": "https://upload.wikimedia.org/wikipedia/commons/3/36/McDonald%27s_Golden_Arches.svg"},
        {"name": "Twitter", "url": "https://upload.wikimedia.org/wikipedia/commons/6/6f/Logo_of_Twitter.svg"},
        {"name": "Coca-Cola", "url": "https://upload.wikimedia.org/wikipedia/commons/c/ce/Coca-Cola_logo.svg"}
    ]
    correct = random.choice(logos)
    wrong_choices = random.sample([l["name"] for l in logos if l["name"] != correct["name"]], 3)
    options = wrong_choices + [correct["name"]]
    random.shuffle(options)
    markup = InlineKeyboardMarkup()
    for opt in options: markup.add(InlineKeyboardButton(opt, callback_data=f"logo_{opt}_{correct['name']}"))
    bot.send_photo(message.chat.id, correct["url"], caption="🖼️ **Guess the Logo!**", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['roll'])
def roll_dice(message): bot.reply_to(message, f"🎲 You rolled a **{random.randint(1, 6)}**!", parse_mode="Markdown")

@bot.message_handler(commands=['flip'])
def flip_coin(message): bot.reply_to(message, f"🪙 **{random.choice(['Heads', 'Tails'])}**!", parse_mode="Markdown")

@bot.message_handler(commands=['8ball'])
def magic_8ball(message):
    if len(message.text) < 7: return bot.reply_to(message, "Ask a question! /8ball Will I be rich?")
    bot.reply_to(message, f"🎱 {random.choice(['Yes.', 'No.', 'Maybe.', 'Definitely.', 'Doubtful.', 'Ask later.'])}")

# --- BASIC & FUN ---
@bot.message_handler(commands=['ping'])
def send_ping(message): bot.reply_to(message, "🏓 Pong!")

@bot.message_handler(commands=['id'])
def send_id(message): bot.reply_to(message, f"ID: `{message.from_user.id}`", parse_mode="Markdown")

@bot.message_handler(commands=['balance'])
def check_balance(message):
    uid = message.from_user.id
    if uid not in user_balances: user_balances[uid] = 1000
    bot.reply_to(message, f"💰 Balance: **${user_balances[uid]}**", parse_mode="Markdown")

@bot.message_handler(commands=['joke'])
def get_joke(message):
    try: bot.reply_to(message, f"😂 {requests.get('https://v2.jokeapi.dev/joke/Any?type=single').json()['joke']}")
    except: bot.reply_to(message, "Failed to get joke.")

@bot.message_handler(commands=['meme'])
def get_meme(message):
    try:
        res = requests.get('https://meme-api.com/gimme').json()
        bot.send_photo(message.chat.id, res['url'], caption=f"😂 **{res['title']}**\nr/{res['subreddit']}", parse_mode="Markdown")
    except: bot.reply_to(message, "Failed to get meme.")

@bot.message_handler(commands=['cat'])
def get_cat(message):
    try: bot.send_photo(message.chat.id, requests.get('https://api.thecatapi.com/v1/images/search').json()[0]['url'], caption="🐱 Meow!")
    except: bot.reply_to(message, "Cat API failed.")

@bot.message_handler(commands=['dog'])
def get_dog(message):
    try: bot.send_photo(message.chat.id, requests.get('https://dog.ceo/api/breeds/image/random').json()['message'], caption="🐶 Woof!")
    except: bot.reply_to(message, "Dog API failed.")

@bot.message_handler(commands=['quote'])
def get_quote(message):
    try:
        res = requests.get('https://api.quotable.io/random').json()
        bot.reply_to(message, f"💬 *{res['content']}*\n— {res['author']}", parse_mode="Markdown")
    except: bot.reply_to(message, "Quote API failed.")

@bot.message_handler(commands=['fact'])
def get_fact(message):
    try: bot.reply_to(message, f"🧠 {requests.get('https://uselessfacts.jsph.pl/api/v2/facts/random').json()['text']}")
    except: bot.reply_to(message, "Fact API failed.")

@bot.message_handler(commands=['password'])
def generate_password(message):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    bot.reply_to(message, f"🔐 `{''.join(random.choice(chars) for _ in range(16))}`", parse_mode="Markdown")

@bot.message_handler(commands=['slap'])
def slap_user(message):
    if not message.reply_to_message: return bot.reply_to(message, "Reply to someone to slap them!")
    bot.reply_to(message, f"👋 {message.from_user.first_name} slapped {message.reply_to_message.from_user.first_name} with a trout!")

@bot.message_handler(commands=['hug'])
def hug_user(message):
    if not message.reply_to_message: return bot.reply_to(message, "Reply to someone to hug them!")
    bot.reply_to(message, f"🤗 {message.from_user.first_name} hugged {message.reply_to_message.from_user.first_name}!")

@bot.message_handler(commands=['bug'])
def bug_command(message):
    if not message.reply_to_message: return bot.reply_to(message, "Reply to someone with /bug to prank them!")
    target = message.reply_to_message.from_user.first_name
    bot.reply_to(message, f"⚠️ Bug Sequence on {target}...")
    for msg in [f"🐛 ERROR IN {target.upper()}!", "📡 virus.exe 50%", "💥 HACKED!", "😂 Just kidding."]:
        bot.send_message(message.chat.id, msg)
        time.sleep(1.5)

# --- BUTTON HANDLERS ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    if call.data.startswith("ans_"):
        chosen = call.data.replace("ans_", "")
        state = trivia_state.get(user_id)
        if state:
            q = state["questions"][state["current"]]
            if chosen == q["a"]:
                state["score"] += 1
                bot.answer_callback_query(call.id, "✅ Correct! +$50")
            else: bot.answer_callback_query(call.id, f"❌ Wrong! Answer: {q['a']}", show_alert=True)
            state["current"] += 1
            bot.delete_message(call.message.chat.id, call.message.message_id)
            send_trivia_question(call.message.chat.id, user_id)
        return
    if call.data.startswith("logo_"):
        _, chosen, correct = call.data.split("_")
        if chosen == correct:
            user_balances[user_id] = user_balances.get(user_id, 1000) + 20
            bot.answer_callback_query(call.id, "✅ Correct! You win $20!")
            bot.edit_message_caption("✅ **Correct!** You won $20!", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, f"❌ Wrong! It was {correct}.", show_alert=True)
            bot.edit_message_caption(f"❌ **Wrong!** It was {correct}.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        return
    if call.data == "cmd_trivia": ask_trivia_amount(call.message)
    elif call.data == "cmd_logo": start_logo_game(call.message)
    elif call.data == "cmd_balance": check_balance(call.message)
    elif call.data == "cmd_play": bot.answer_callback_query(call.id, "Type /play <song name> to use this!", show_alert=True)

print("Bot is running...")
bot.infinity_polling()
