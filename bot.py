import os
import sqlite3
import threading
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get("8842275295:AAE_zKGIGeWSiS2waVjWU9sCGGb0F_BVvxk")
ADMIN_GROUP_ID = int(os.environ.get("-1004376603252", 0))
ADMIN_ID = int(os.environ.get("6673230697", 0)) 

if not BOT_TOKEN:
    print("❌ Error: BOT_TOKEN ကို မတွေ့ရှိပါ။ Render Environment Variables တွင် ထည့်ပေးပါ။")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# --- WEB SERVER (Render အတွက်) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- DATABASE SETUP ---
conn = sqlite3.connect('candyhub.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (chat_id INTEGER PRIMARY KEY, name TEXT, email TEXT, password TEXT, coins INTEGER)''')
conn.commit()

# --- HELPERS ---
def get_user(chat_id):
    cursor.execute("SELECT * FROM users WHERE chat_id=?", (chat_id,))
    return cursor.fetchone()

# --- COMMAND SETTINGS ---
bot.set_my_commands([
    BotCommand("start", "🚀 စတင်ရန်"),
    BotCommand("me", "👤 Profile"),
    BotCommand("check2", "📸 ပုံတင်ရန်"),
    BotCommand("leaderboard", "🏆 Admin: Leaderboard"),
    BotCommand("active", "👥 Admin: Active Users"),
    BotCommand("see", "🔍 Admin: See Data"),
    BotCommand("change", "🔄 Admin: Edit Data"),
    BotCommand("broadcast", "📣 Admin: Broadcast"),
    BotCommand("error", "⚠️ တိုင်ကြားရန်"),
])

# --- USER COMMANDS ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user = get_user(message.chat.id)
    if user: bot.send_message(message.chat.id, f"👋 ပြန်လည်ကြိုဆိုပါတယ် {user[1]}! သင့် Coin: {user[4]}")
    else: bot.send_message(message.chat.id, "မင်္ဂလာပါ! အကောင့်ဖွင့်ရန် နာမည်ရိုက်ပေးပါ -")

@bot.message_handler(commands=['me'])
def profile(message):
    user = get_user(message.chat.id)
    if user: bot.send_message(message.chat.id, f"👤 Name: {user[1]}\n📧 Email: {user[2]}\n💰 Coins: {user[4]}")
    else: bot.send_message(message.chat.id, "အကောင့်မရှိပါ။ /start သုံးပါ။")

@bot.message_handler(commands=['check2'])
def check2(message):
    bot.send_message(message.chat.id, "📸 ပုံပို့ပေးပါ (Confirm ဖြစ်ရင် 1000 coin ရပါမည်)")
    bot.register_next_step_handler(message, lambda m: bot.send_photo(ADMIN_GROUP_ID, m.photo[-1].file_id, caption=f"User {m.chat.id} ပုံပို့သည်", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Reward 1000", callback_data=f"reward_{m.chat.id}"))) if m.photo else bot.send_message(m.chat.id, "ပုံသာ ပို့ပါ။"))

# --- ADMIN COMMANDS ---
@bot.message_handler(commands=['leaderboard'])
def leaderboard(message):
    if message.from_user.id != ADMIN_ID: return
    users = cursor.execute("SELECT name, coins FROM users ORDER BY coins DESC LIMIT 10").fetchall()
    text = "🏆 **Top 10 Users:**\n" + "\n".join([f"{i+1}. {u[0]} - {u[1]} Coins" for i, u in enumerate(users)])
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['active'])
def active_users(message):
    if message.from_user.id != ADMIN_ID: return
    count = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    bot.send_message(message.chat.id, f"👥 လက်ရှိ User စုစုပေါင်း: {count} ယောက်")

@bot.message_handler(commands=['see'])
def see_user(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        target_id = message.text.split()[1]
        user = get_user(target_id)
        if user: bot.send_message(message.chat.id, f"👤 User Data:\nID: {user[0]}\nName: {user[1]}\nEmail: {user[2]}\nCoins: {user[4]}")
        else: bot.send_message(message.chat.id, "❌ User မတွေ့ပါ။")
    except: bot.send_message(message.chat.id, "Usage: /see [user_id]")

@bot.message_handler(commands=['change'])
def change_admin(message):
    if message.from_user.id != ADMIN_ID: return
    bot.send_message(message.chat.id, "🛠 User ID ကို ရိုက်ပေးပါ:")
    bot.register_next_step_handler(message, lambda m: bot.send_message(m.chat.id, "Email အသစ်:") or bot.register_next_step_handler(m, lambda m2: bot.send_message(m2.chat.id, "Coin (+/-) :") or bot.register_next_step_handler(m2, lambda m3: update_user(m, m2, m3))))

def update_user(m_id, m_email, m_coin):
    try:
        cursor.execute("UPDATE users SET email=?, coins=coins+? WHERE chat_id=?", (m_email.text, int(m_coin.text), int(m_id.text)))
        conn.commit()
        bot.send_message(m_id.chat.id, "✅ အောင်မြင်သည်။")
    except: bot.send_message(m_id.chat.id, "❌ Error ဖြစ်သည်။")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "📣 ကြော်ငြာစာ ရိုက်ပေးပါ -")
        bot.register_next_step_handler(message, lambda m: [bot.send_message(u[0], f"📣 {m.text}") for u in cursor.execute("SELECT chat_id FROM users").fetchall()] and bot.send_message(message.chat.id, "✅ ပို့ပြီးပါပြီ။"))

# --- CALLBACK & RUN ---
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data.startswith("reward_"):
        uid = int(call.data.split("_")[1])
        cursor.execute("UPDATE users SET coins=coins+1000 WHERE chat_id=?", (uid,))
        conn.commit()
        bot.send_message(uid, "🎉 1000 Coins ရရှိပါပြီ!")
        bot.edit_message_caption(chat_id=ADMIN_GROUP_ID, message_id=call.message.message_id, caption="✅ Reward ပေးပြီး")

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot.infinity_polling()
                              
