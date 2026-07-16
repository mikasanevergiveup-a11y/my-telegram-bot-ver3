import os
import sqlite3
import threading
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from dotenv import load_dotenv

# .env ဖိုင်ကို စတင်ဖတ်ရှုခြင်း
load_dotenv()

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_GROUP_ID = int(os.environ.get("ADMIN_GROUP_ID", 0))
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

if not BOT_TOKEN:
    print("❌ ERROR: BOT_TOKEN ကို မတွေ့ရှိပါ။ .env ဖိုင်ကို စစ်ဆေးပါ။")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# --- WEB SERVER (Render အတွက်) ---
app = Flask(__name__)
@app.route('/')
def home():
    return "CandyHub Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- DATABASE ---
conn = sqlite3.connect('candyhub.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (chat_id INTEGER PRIMARY KEY, name TEXT, email TEXT, password TEXT, coins INTEGER)''')
conn.commit()

# --- COMMANDS MENU ---
bot.set_my_commands([
    BotCommand("start", "စတင်ရန်"),
    BotCommand("me", "Profile ကြည့်ရန်"),
    BotCommand("check2", "ပုံတင်ရန်"),
    BotCommand("sent", "စာပို့ရန်"),
    BotCommand("error", "တိုင်ကြားရန်"),
    BotCommand("game", "ဂိမ်းဆော့ရန်"),
    BotCommand("leaderboard", "Top 10"),
    BotCommand("active", "Total Users"),
    BotCommand("see", "See Data"),
    BotCommand("change", "Data ပြင်ရန်"),
    BotCommand("broadcast", "ကြော်ငြာရန်")
])

# --- USER COMMANDS ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user = cursor.execute("SELECT * FROM users WHERE chat_id=?", (message.chat.id,)).fetchone()
    if user:
        bot.send_message(message.chat.id, f"👋 ပြန်လည်ကြိုဆိုပါတယ် {user[1]}!")
    else:
        bot.send_message(message.chat.id, "မင်္ဂလာပါ! အကောင့်ဖွင့်ရန် သင့်နာမည်ကို ရိုက်ပေးပါ:")
        bot.register_next_step_handler(message, lambda m: cursor.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?, ?)", (m.chat.id, m.text, "None", "None", 0)) or conn.commit() or bot.send_message(m.chat.id, "✅ အကောင့်ဖွင့်ပြီးပါပြီ။"))

@bot.message_handler(commands=['me'])
def profile(message):
    user = cursor.execute("SELECT * FROM users WHERE chat_id=?", (message.chat.id,)).fetchone()
    if user: bot.send_message(message.chat.id, f"👤 Name: {user[1]}\n💰 Coins: {user[4]}")
    else: bot.send_message(message.chat.id, "❌ အကောင့်မရှိပါ။ /start ကိုနှိပ်ပါ။")

@bot.message_handler(commands=['check2'])
def check2(message):
    bot.send_message(message.chat.id, "📸 ပုံကို ပို့ပေးပါ:")
    bot.register_next_step_handler(message, lambda m: bot.send_photo(ADMIN_GROUP_ID, m.photo[-1].file_id, caption=f"User ID: {m.chat.id}") if m.photo else bot.reply_to(m, "ပုံသာ ပို့ပေးပါ"))

@bot.message_handler(commands=['sent'])
def sent_cmd(message):
    bot.send_message(message.chat.id, "💬 Admin ထံ ပို့လိုသော စာသားကို ရေးပေးပါ:")
    bot.register_next_step_handler(message, lambda m: bot.send_message(ADMIN_ID, f"📩 စာရောက်ရှိပါသည်:\n\n{m.text}"))

@bot.message_handler(commands=['error'])
def error_cmd(message):
    bot.send_message(message.chat.id, "⚠️ ပြဿနာကို ရေးပေးပါ:")
    bot.register_next_step_handler(message, lambda m: bot.send_message(ADMIN_ID, f"🚨 Error တိုင်ကြားချက်:\n{m.text}"))

@bot.message_handler(commands=['game'])
def game_cmd(message):
    bot.send_message(message.chat.id, "🎮 ဂိမ်းဆော့ရန် - @CandyHub8_bot")

# --- ADMIN COMMANDS ---
@bot.message_handler(commands=['leaderboard'])
def leaderboard(message):
    if message.from_user.id != ADMIN_ID: return
    users = cursor.execute("SELECT name, coins FROM users ORDER BY coins DESC LIMIT 10").fetchall()
    text = "\n".join([f"{i+1}. {u[0]} - {u[1]}" for i, u in enumerate(users)])
    bot.send_message(message.chat.id, f"🏆 Top 10:\n{text}")

@bot.message_handler(commands=['active'])
def active(message):
    if message.from_user.id != ADMIN_ID: return
    count = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    bot.send_message(message.chat.id, f"👥 User ပေါင်း: {count}")

@bot.message_handler(commands=['see'])
def see(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        user = cursor.execute("SELECT * FROM users WHERE chat_id=?", (message.text.split()[1],)).fetchone()
        bot.send_message(message.chat.id, str(user))
    except: bot.send_message(message.chat.id, "အသုံးပြုပုံ: /see [id]")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    bot.send_message(message.chat.id, "📣 ကြော်ငြာစာကို ရေးပေးပါ:")
    bot.register_next_step_handler(message, lambda m: [bot.send_message(u[0], m.text) for u in cursor.execute("SELECT chat_id FROM users").fetchall()])

# --- RUN ---
if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot.infinity_polling)
