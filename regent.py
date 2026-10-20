import os
import telebot
import yt_dlp
import random
import time
import requests
import string
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# Memory storage
user_balances = {}
trivia_state = {} 

# --- MAIN MENU ---
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
**Games:** /trivia, /logo, /roll, /flip, /8ball, /rps
**Utilities:** /font <text>, /password, /time, /userinfo, /id
**Media:** /play <song>, /meme, /cat, /dog
**Fun:** /joke, /quote, /fact, /slap, /hug, /bug
**Stickers:** Just send a sticker to the bot to save it for WhatsApp!
    """
    bot.reply_to(message, help_text, parse_mode="Markdown")

# --- STICKER SAVER (FOR WHATSAPP) ---
@bot.message_handler(content_types=['sticker'])
def handle_sticker(message):
    if message.chat.type != 'private':
        bot.reply_to(message, "Please send stickers to me in a private message to save them.")
        return
    
    msg = bot.reply_to(message, "⏳ Saving sticker...")
    try:
        # Get the file path from Telegram
        file_info = bot.get_file(message.sticker.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Save it temporarily
        file_name = "sticker.webp"
        with open(file_name, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        # Send it back as a document so WhatsApp can read it
        with open(file_name, 'rb') as f:
            bot.send_document(message.chat.id, f, caption="✅ **Sticker saved!**\nDownload this file and import it to WhatsApp as a sticker.", parse_mode="Markdown")
            
        os.remove(file_name) # Clean up
        bot.delete_message(message.chat.id, msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Failed to save sticker. Error: {str(e)[:100]}", message.chat.id, msg.message_id)

# --- FANCY FONT GENERATOR ---
@bot.message_handler(commands=['font'])
def generate_font(message):
    text = message.text.replace('/font', '').strip()
    if not text:
        bot.reply_to(message, "Please provide text. Example:\n`/font Hello World`", parse_mode="Markdown")
        return

    # Character maps for different styles
    normal = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    
    bold_lower = "𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳"
    bold_upper = "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙"
    bold_nums = "𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗"
    
    italic_lower = "𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻"
    italic_upper = "𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡"
    
    cursive_lower = "𝒶𝒷𝒸𝒹ℯ𝒻ℊ𝒽𝒾𝒿𝓀𝓁𝓂𝓃ℴ𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏"
    cursive_upper = "𝒜ℬ𝒞𝒟ℰℱ𝒢ℋℐ𝒥𝒦ℒℳ𝒩𝒪𝒫𝒬ℛ𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵"
    
    mono_lower = "𝚊𝚋𝚌𝚍𝚎𝚏𝚐𝚑𝚒𝚓𝚔𝚕𝚖𝚗𝚘𝚙𝚚𝚛𝚜𝚝𝚞𝚟𝚠𝚡𝚢𝚣"
    mono_upper = "𝙰𝙱𝙲𝙳𝙴𝙵𝙶𝙷𝙸𝙹𝙺𝙻𝙼𝙽𝙾𝙿𝚀𝚁𝚂𝚃𝚄𝚅𝚆𝚇𝚈𝚉"
    mono_nums = "𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿"

    # Functions to translate text
    def translate(txt, low, up, nums=None):
        res = ""
        for char in txt:
            if char.islower() and char in normal: res += low[normal.index(char)]
            elif char.isupper() and char in normal: res += up[normal.index(char) - 26]
            elif char.isdigit() and nums: res += nums[int(char)]
            else: res += char
        return res

    bold_text = translate(text, bold_lower, bold_upper, bold_nums)
    italic_text = translate(text, italic_lower, italic_upper)
    cursive_text = translate(text, cursive_lower, cursive_upper)
    mono_text = translate(text, mono_lower, mono_upper, mono_nums)

    output = f"✨ **Your Fancy Text:**\n\n**Bold:**\n`{bold_text}`\n\n**Italic:**\n`{italic_text}`\n\n**Cursive:**\n`{cursive_text}`\n\n**Monospace:**\n`{mono_text}`"
    bot.reply_to(message, output, parse_mode="Markdown")

# --- MUSIC ---
@bot.message_handler(commands=['play'])
def play_music(message):
    query = message.text.replace('/play', '').strip()
    if not query:
        bot.reply_to(message, "Please provide a song name. Example:\n`/play Shape of You`", parse_mode="Markdown")
        return
    
    msg = bot.reply_to(message, f"🔍 Searching for: **{query}**...", parse_mode="Markdown")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'song.%(ext)s',
        'noplaylist': True,
        'ignoreerrors': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"scsearch3:{query}", download=False)
            if not info or 'entries' not in info: raise Exception("No results found.")

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
                except Exception:
                    continue
            if not downloaded:
                bot.edit_message_text("❌ Top results were DRM-protected or unavailable.", message.chat.id, msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)[:100]}", message.chat.id, msg.message_id)

# --- TRIVIA GAME ---
@bot.message_handler(commands=['trivia'])
def ask_trivia_amount(message):
    msg = bot.reply_to(message, "🎮 **Trivia Time!**\nHow many questions do you want to play? (Send a number between 1 and 10)", parse_mode="Markdown")
    bot.register_next_step_handler(msg, start_trivia_game)

def start_trivia_game(message):
    if not message.text.isdigit() or int(message.text) < 1 or int(message.text) > 10:
        bot.reply_to(message, "Please send a valid number between 1 and 10. Try /trivia again.")
        return
    
    amount = int(message.text)
    questions = [
        {"q": "What is the capital of France?", "a": "Paris", "options": ["London", "Berlin", "Paris", "Madrid"]},
        {"q": "Which planet is known as the Red Planet?", "a": "Mars", "options": ["Earth", "Mars", "Jupiter", "Venus"]},
        {"q": "Who painted the Mona Lisa?", "a": "Da Vinci", "options": ["Van Gogh", "Picasso", "Da Vinci", "Michelangelo"]},
        {"q": "What is the largest ocean?", "a": "Pacific", "options": ["Atlantic", "Indian", "Arctic", "Pacific"]},
        {"q": "What year did World War II end?", "a": "1945", "options": ["1918", "1939", "1945", "1950"]},
        {"q": "What is the chemical symbol for gold?", "a": "Au", "options": ["Ag", "Au", "Fe", "Cu"]},
        {"q": "Who wrote Romeo and Juliet?", "a": "Shakespeare", "options": ["Dickens", "Shakespeare", "Hemingway", "Tolkien"]}
    ]
    random.shuffle(questions)
    selected_qs = questions[:amount]
    
    user_id = message.from_user.id
    trivia_state[user_id] = {"questions": selected_qs, "current": 0, "score": 0}
    
    send_trivia_question(message.chat.id, user_id)

def send_trivia_question(chat_id, user_id):
    state = trivia_state.get(user_id)
    if not state or state["current"] >= len(state["questions"]):
        score = state["score"] if state else 0
        total = len(state["questions"]) if state else 0
        user_balances[user_id] = user_balances.get(user_id, 1000) + (score * 50)
        bot.send_message(chat_id, f"🏁 **Game Over!**\nYou scored {score}/{total}.\nYou earned ${score * 50}!\nCheck /balance", parse_mode="Markdown")
        if user_id in trivia_state: del trivia_state[user_id]
        return

    q = state["questions"][state["current"]]
    markup = InlineKeyboardMarkup()
    for option in q["options"]:
        markup.add(InlineKeyboardButton(option, callback_data=f"ans_{option}"))
    
    bot.send_message(chat_id, f"❓ **Question {state['current'] + 1}/{len(state['questions'])}:**\n\n{q['q']}", reply_markup=markup, parse_mode="Markdown")

# --- LOGO GAME ---
@bot.message_handler(commands=['logo'])
def start_logo_game(message):
    logos = [
        {"name": "Apple", "url": "https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg"},
        {"name": "Nike", "url": "https://upload.wikimedia.org/wikipedia/commons/a/a6/Logo_NIKE.svg"},
        {"name": "McDonald's", "url": "https://upload.wikimedia.org/wikipedia/commons/3/36/McDonald%27s_Golden_Arches.svg"},
        {"name": "Twitter", "url": "https://upload.wikimedia.org/wikipedia/commons/6/6f/Logo_of_Twitter.svg"},
        {"name": "Coca-Cola", "url": "https://upload.wikimedia.org/wikipedia/commons/c/ce/Coca-Cola_logo.svg"},
        {"name": "Adidas", "url": "https://upload.wikimedia.org/wikipedia/commons/2/20/Adidas_Logo.svg"},
        {"name": "Target", "url": "https://upload.wikimedia.org/wikipedia/commons/9/9a/Target_logo.svg"}
    ]
    
    correct = random.choice(logos)
    wrong_choices = random.sample([l["name"] for l in logos if l["name"] != correct["name"]], 3)
    
    options = wrong_choices + [correct["name"]]
    random.shuffle(options)
    
    markup = InlineKeyboardMarkup()
    for opt in options:
        markup.add(InlineKeyboardButton(opt, callback_data=f"logo_{opt}_{correct['name']}"))
    
    bot.send_photo(message.chat.id, correct["url"], caption="🖼️ **Guess the Logo!**\nWhich company does this belong to?", reply_markup=markup, parse_mode="Markdown")

# --- BASIC COMMANDS ---
@bot.message_handler(commands=['ping'])
def send_ping(message): bot.reply_to(message, "🏓 Pong! I'm alive.")

@bot.message_handler(commands=['id'])
def send_id(message): bot.reply_to(message, f"Your Telegram ID: `{message.from_user.id}`", parse_mode="Markdown")

@bot.message_handler(commands=['userinfo'])
def user_info(message):
    user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    bot.reply_to(message, f"👤 **User Info:**\nName: {user.first_name}\nID: `{user.id}`\nUsername: @{user.username if user.username else 'None'}", parse_mode="Markdown")

@bot.message_handler(commands=['time'])
def current_time(message):
    from datetime import datetime
    bot.reply_to(message, f"🕒 Server Time: **{datetime.now().strftime('%H:%M:%S')}**", parse_mode="Markdown")

@bot.message_handler(commands=['balance'])
def check_balance(message):
    uid = message.from_user.id
    if uid not in user_balances: user_balances[uid] = 1000
    bot.reply_to(message, f"💰 Your balance is: **${user_balances[uid]}**", parse_mode="Markdown")

# --- FUN API COMMANDS ---
@bot.message_handler(commands=['joke'])
def get_joke(message):
    try: bot.reply_to(message, f"😂 {requests.get('https://v2.jokeapi.dev/joke/Any?type=single').json()['joke']}")
    except: bot.reply_to(message, "Could not fetch a joke.")

@bot.message_handler(commands=['meme'])
def get_meme(message):
    try:
        res = requests.get('https://meme-api.com/gimme').json()
        bot.send_photo(message.chat.id, res['url'], caption=f"😂 **{res['title']}**\nr/{res['subreddit']}", parse_mode="Markdown")
    except: bot.reply_to(message, "Could not fetch a meme.")

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

@bot.message_handler(commands=['roll'])
def roll_dice(message): bot.reply_to(message, f"🎲 You rolled a **{random.randint(1, 6)}**!", parse_mode="Markdown")

@bot.message_handler(commands=['flip'])
def flip_coin(message): bot.reply_to(message, f"🪙 **{random.choice(['Heads', 'Tails'])}**!", parse_mode="Markdown")

@bot.message_handler(commands=['8ball'])
def magic_8ball(message):
    if len(message.text) < 7: return bot.reply_to(message, "Ask a question! /8ball Will I be rich?")
    res = ["Yes.", "No.", "Maybe.", "Definitely.", "Doubtful.", "Ask later."]
    bot.reply_to(message, f"🎱 {random.choice(res)}")

@bot.message_handler(commands=['password'])
def generate_password(message):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    bot.reply_to(message, f"🔐 `{''.join(random.choice(chars) for _ in range(16))}`", parse_mode="Markdown")

# --- ACTION COMMANDS ---
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
    time.sleep(1)
    for msg in [f"🐛 ERROR IN {target.upper()}!", "📡 virus.exe 50%", "💥 HACKED!", "😂 Just kidding."]:
        bot.send_message(message.chat.id, msg)
        time.sleep(1.5)

# --- BUTTON HANDLERS ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    
    # TRIVIA BUTTONS
    if call.data.startswith("ans_"):
        chosen = call.data.replace("ans_", "")
        state = trivia_state.get(user_id)
        if state:
            q = state["questions"][state["current"]]
            if chosen == q["a"]:
                state["score"] += 1
                bot.answer_callback_query(call.id, "✅ Correct! +$50")
            else:
                bot.answer_callback_query(call.id, f"❌ Wrong! Answer: {q['a']}", show_alert=True)
            
            state["current"] += 1
            bot.delete_message(call.message.chat.id, call.message.message_id)
            send_trivia_question(call.message.chat.id, user_id)
        return

    # LOGO BUTTONS
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

    # MAIN MENU BUTTONS
    if call.data == "cmd_trivia": ask_trivia_amount(call.message)
    elif call.data == "cmd_logo": start_logo_game(call.message)
    elif call.data == "cmd_balance": check_balance(call.message)
    elif call.data == "cmd_play": bot.answer_callback_query(call.id, "Type /play <song name> to use this!", show_alert=True)
    else: bot.answer_callback_query(call.id, "Under construction!")

print("Bot is running...")
bot.infinity_polling()
