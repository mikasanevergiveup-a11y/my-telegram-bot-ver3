```python
import os
import sqlite3
import threading
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand

# ==========================================
# ၁။ CONFIGURATION & TOKENS
# ==========================================
BOT_TOKEN = os.environ.get("8842275295:AAE_zKGIGeWSiS2waVjWU9sCGGb0F_BVvxk")

# Token မရှိရင် Render မှာ Error သေချာပေါ်အောင် စစ်ဆေးခြင်း
if not BOT_TOKEN:
    print("❌ ERROR: BOT_TOKEN ကို မတွေ့ရှိပါ။ Render Environment Variables ကို သေချာစစ်ဆေးပါ။")
    exit(1)

# ID များကို Integer အဖြစ် ပြောင်းခြင်း (မရှိရင် 0 အဖြစ်ထားမည်)
try:
    ADMIN_GROUP_ID = int(os.environ.get("-1004376603252", 0))
    ADMIN_ID = int(os.environ.get("6673230697", 0))
except ValueError:
    print("❌ ERROR: ADMIN_GROUP_ID သို့မဟုတ် ADMIN_ID သည် ဂဏန်းဖြစ်ရပါမည်။")
    ADMIN_GROUP_ID = 0
    ADMIN_ID = 0

bot = telebot.TeleBot(BOT_TOKEN)

# ==========================================
# ၂။ WEB SERVER (Render မအိပ်သွားစေရန်)
# ==========================================
app = Flask(__name__)
@app.route('/')
def home():
    return "CandyHub Bot is running successfully!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ==========================================
# ၃။ DATABASE SETUP
# ==========================================
conn = sqlite3.connect('candyhub.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (chat_id INTEGER PRIMARY KEY, name TEXT, email TEXT, password TEXT, coins INTEGER)''')
conn.commit()

# ==========================================
# ၄။ HELPER FUNCTIONS
# ==========================================
REQUIRED_CHANNELS = ["@CandyHub_Ch", "@candyhubassissiant", "@CandyHub_Chat"]

def is_user_joined(user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception as e:
            # Bot က Channel မှာ Admin မဟုတ်ရင် error တက်နိုင်သည်
            return False
    return True

def get_user(chat_id):
    cursor.execute("SELECT * FROM users WHERE chat_id=?", (chat_id,))
    return cursor.fetchone()

# ==========================================
# ၅။ BOT COMMANDS MENU SETUP
# ==========================================
bot.set_my_commands([
    BotCommand("start", "🚀 Bot ကို စတင်ရန်"),
    BotCommand("me", "👤 မိမိ Profile ကိုကြည့်ရန်"),
    BotCommand("check2", "📸 ပုံတင်ပြီး Coin ရယူရန်"),
    BotCommand("sent", "💬 Admin များထံ စာပို့ရန်"),
    BotCommand("error", "⚠️ Coin ပြဿနာ တိုင်ကြားရန်"),
    BotCommand("game", "🎮 ဂိမ်းဆော့ရန်"),
    BotCommand("leaderboard", "🏆 Top 10 Users (Admin)"),
    BotCommand("active", "👥 Total Users (Admin)"),
    BotCommand("see", "🔍 User Data ကြည့်ရန် (Admin)"),
    BotCommand("change", "🔄 Data ပြင်ရန် (Admin)"),
    BotCommand("broadcast", "📣 ကြော်ငြာရန် (Admin)"),
    BotCommand("cancel", "❌ လုပ်ဆောင်ဆဲကို ဖျက်သိမ်းရန်")
])

# ==========================================
# ၆။ CANCEL COMMAND
# ==========================================
@bot.message_handler(commands=['cancel'])
def cancel_cmd(message):
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    bot.send_message(message.chat.id, "❌ လုပ်ဆောင်ချက်ကို ဖျက်သိမ်းလိုက်ပါပြီ။")

# ==========================================
# ၇။ ADMIN COMMANDS (Admin သီးသန့်)
# ==========================================
@bot.message_handler(commands=['leaderboard'])
def leaderboard(message):
    if message.from_user.id != ADMIN_ID: return
    users = cursor.execute("SELECT name, coins FROM users ORDER BY coins DESC LIMIT 10").fetchall()
    text = "🏆 **Top 10 Users:**\n\n"
    for i, u in enumerate(users):
        text += f"{i+1}. {u[0]} - 💰 {u[1]} Coins\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['active'])
def active_users(message):
    if message.from_user.id != ADMIN_ID: return
    count = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    bot.send_message(message.chat.id, f"👥 လက်ရှိ Bot အသုံးပြုသူ စုစုပေါင်း: {count} ယောက်")

@bot.message_handler(commands=['see'])
def see_user(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        target_id = int(message.text.split()[1])
        user = get_user(target_id)
        if user:
            bot.send_message(message.chat.id, f"👤 **User Data**\n\n🆔 ID: {user[0]}\n👤 Name: {user[1]}\n📧 Email: {user[2]}\n🔐 Pass: {user[3]}\n💰 Coins: {user[4]}")
        else:
            bot.send_message(message.chat.id, "❌ ထို ID ဖြင့် User မတွေ့ပါ။")
    except:
        bot.send_message(message.chat.id, "⚠️ အသုံးပြုပုံ: /see [user_id]")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    bot.send_message(message.chat.id, "📣 ကြော်ငြာလိုသော စာသားကို ရိုက်ပေးပါ:")
    bot.register_next_step_handler(message, process_broadcast)

def process_broadcast(message):
    if message.text == '/cancel': return cancel_cmd(message)
    users = cursor.execute("SELECT chat_id FROM users").fetchall()
    success = 0
    for u in users:
        try:
            bot.send_message(u[0], f"📣 **Announcement**\n\n{message.text}")
            success += 1
        except:
            pass
    bot.send_message(message.chat.id, f"✅ ကြော်ငြာစာကို User ပေါင်း {success} ယောက်ထံ အောင်မြင်စွာ ပို့ပြီးပါပြီ။")

@bot.message_handler(commands=['change'])
def change_admin(message):
    if message.from_user.id != ADMIN_ID: return
    bot.send_message(message.chat.id, "🛠 **Admin Edit Mode:**\nပြောင်းလဲလိုသော User ၏ ID ကို ရိုက်ထည့်ပါ:")
    bot.register_next_step_handler(message, change_get_id)

def change_get_id(message):
    if message.text == '/cancel': return cancel_cmd(message)
    user_id = message.text
    bot.send_message(message.chat.id, "📧 အီးမေးလ်အသစ်ကို ရိုက်ထည့်ပါ (မပြောင်းလိုပါက '-' ဟုရိုက်ပါ):")
    bot.register_next_step_handler(message, change_get_email, user_id)

def change_get_email(message, user_id):
    if message.text == '/cancel': return cancel_cmd(message)
    email = message.text
    bot.send_message(message.chat.id, "💰 Coin ပမာဏကို ရိုက်ထည့်ပါ (ဥပမာ: -1 သို့မဟုတ် +2):")
    bot.register_next_step_handler(message, change_finish, user_id, email)

def change_finish(message, user_id, email):
    if message.text == '/cancel': return cancel_cmd(message)
    try:
        coin_adj = int(message.text)
        if email != '-':
            cursor.execute("UPDATE users SET email=?, coins=coins+? WHERE chat_id=?", (email, coin_adj, int(user_id)))
        else:
            cursor.execute("UPDATE users SET coins=coins+? WHERE chat_id=?", (coin_adj, int(user_id)))
        conn.commit()
        bot.send_message(message.chat.id, f"✅ အောင်မြင်စွာ ပြင်ဆင်ပြီးပါပြီ!\nID: {user_id}\nCoin တိုး/လျှော့: {coin_adj}")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Error ဖြစ်သွားသည်။ (ဂဏန်းများ မှန်ကန်စွာ ထည့်သွင်းရန် သေချာစစ်ဆေးပါ)")

# ==========================================
# ၈။ USER COMMANDS (အသုံးပြုသူများအတွက်)
# ==========================================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    chat_id = message.chat.id
    # Force Join Check
    if not is_user_joined(chat_id):
        join_text = (
            f"မင်္ဂလာပါ {message.from_user.first_name} 🙏\n\n"
            "ဤ Bot ကိုအသုံးပြုရန် အောက်ပါ Group နှင့် Channel များ join ပေးပါနော်။\n\n"
            "🔗 https://t.me/CandyHub_Ch\n"
            "🔗 https://t.me/candyhubassissiant\n"
            "🔗 https://t.me/CandyHub_Chat\n\n"
            "👉 Join ပြီးပါက /start ကို ပြန်နှိပ်ပါ။"
        )
        bot.send_message(chat_id, join_text, disable_web_page_preview=True)
        return

    # Check if user exists in DB
    user = get_user(chat_id)
    if user:
        bot.send_message(chat_id, f"👋 ပြန်လည်ကြိုဆိုပါတယ် {user[1]}!\n💰 သင့်လက်ရှိ Coin ပမာဏ: {user[4]}")
    else:
        bot.send_message(chat_id, "မင်္ဂလာပါ! အကောင့်သစ်ဖွင့်ရန် သင့် **နာမည်** ကို ရိုက်ပေးပါ -")
        bot.register_next_step_handler(message, reg_name)

def reg_name(message):
    if message.text == '/cancel': return cancel_cmd(message)
    name = message.text
    bot.send_message(message.chat.id, "📧 သင့် **Email** ကို ရိုက်ပေးပါ -")
    bot.register_next_step_handler(message, reg_email, name)

def reg_email(message, name):
    if message.text == '/cancel': return cancel_cmd(message)
    email = message.text
    bot.send_message(message.chat.id, "🔐 **Password** တစ်ခု သတ်မှတ်ပေးပါ -")
    bot.register_next_step_handler(message, reg_pass, name, email)

def reg_pass(message, name, email):
    if message.text == '/cancel': return cancel_cmd(message)
    password = message.text
    try:
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (message.chat.id, name, email, password, 0))
        conn.commit()
        bot.send_message(message.chat.id, "✅ အကောင့်အောင်မြင်စွာ ဖွင့်လှစ်ပြီးပါပြီ! သင့်အချက်အလက်များကို /me တွင် ကြည့်ရှုနိုင်ပါသည်။")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ အကောင့်ဖွင့်ရာတွင် အမှားအယွင်းရှိခဲ့သည်။ ထပ်မံကြိုးစားပါ။")

@bot.message_handler(commands=['me'])
def profile(message):
    user = get_user(message.chat.id)
    if user:
        text = f"👤 **Profile Information**\n\n🆔 ID: `{user[0]}`\n👤 Name: {user[1]}\n📧 Email: {user[2]}\n💰 Coins: {user[4]}"
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "❌ အကောင့်မရှိသေးပါ။ ကျေးဇူးပြု၍ /start ကိုနှိပ်ပါ။")

@bot.message_handler(commands=['game'])
def game_cmd(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Play Game 🎮", url="https://t.me/CandyHub8_bot"))
    bot.send_message(message.chat.id, "🎮 CandyHub Game ဆော့ကစားရန် အောက်ပါခလုတ်ကို နှိပ်ပါ သို့မဟုတ် @CandyHub8_bot သို့ သွားပါရန်။", reply_markup=markup)

@bot.message_handler(commands=['check2'])
def check2(message):
    bot.send_message(message.chat.id, "📸 Verification အတွက် သင့်ပုံကို ပို့ပေးပါ -")
    bot.register_next_step_handler(message, check2_photo)

def check2_photo(message):
    if message.text == '/cancel': return cancel_cmd(message)
    if message.photo:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Confirm & Reward 1000", callback_data=f"reward_{message.chat.id}"))
        bot.send_photo(
            ADMIN_GROUP_ID, 
            message.photo[-1].file_id, 
            caption=f"📩 **Check2 Photo Upload**\n\n👤 User Name: {message.from_user.first_name}\n🆔 User ID: {message.chat.id}", 
            reply_markup=markup
        )
        bot.send_message(message.chat.id, "⏳ ပုံကို Admin ထံ ပို့ဆောင်ပြီးပါပြီ။ အတည်ပြုချက် စောင့်ဆိုင်းပေးပါ...")
    else:
        bot.send_message(message.chat.id, "⚠️ ကျေးဇူးပြု၍ ပုံ (Photo) သီးသန့် ပို့ပေးပါဗျာ။ /check2 ကို ပြန်နှိပ်ပါ။")

@bot.message_handler(commands=['sent'])
def sent_cmd(message):
    bot.send_message(message.chat.id, "💬 Admin များထံ ပို့လိုသော စာသား သို့မဟုတ် သတင်းစကားကို ရိုက်ပို့ပေးပါ -")
    bot.register_next_step_handler(message, send_to_admin)

def send_to_admin(message):
    if message.text == '/cancel': return cancel_cmd(message)
    bot.send_message(
        ADMIN_GROUP_ID, 
        f"📩 **Direct Message from User**\n\n👤 Name: {message.from_user.first_name}\n🆔 ID: {message.chat.id}\n💬 Message:\n{message.text}"
    )
    bot.send_message(message.chat.id, "✅ သင့်မက်ဆေ့ခ်ျကို Admin အဖွဲ့ထံသို့ အောင်မြင်စွာ ပို့ဆောင်ပြီးပါပြီ။")

@bot.message_handler(commands=['error'])
def error_cmd(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ Coin မဝင်ခြင်း", callback_data=f"err_no_coin_{message.chat.id}"))
    markup.add(InlineKeyboardButton("➖ Coin နှုတ်သွားခြင်း", callback_data=f"err_lost_coin_{message.chat.id}"))
    bot.send_message(message.chat.id, "⚠️ **ပြဿနာ တိုင်ကြားလိုသည့် အကြောင်းအရင်းကို ရွေးချယ်ပါ -**", reply_markup=markup)

# ==========================================
# ၉။ BUTTON CALLBACK HANDLER
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    # Check2 Reward Button
    if call.data.startswith("reward_"):
        user_id = int(call.data.split("_")[1])
        try:
            cursor.execute("UPDATE users SET coins=coins+1000 WHERE chat_id=?", (user_id,))
            conn.commit()
            bot.send_message(user_id, "🎉 ဂုဏ်ယူပါတယ်! Admin မှ သင့်ပုံကို အတည်ပြုပြီး 1000 Coins ပေးလိုက်ပါပြီ။")
            bot.edit_message_caption(chat_id=ADMIN_GROUP_ID, message_id=call.message.message_id, caption=call.message.caption + "\n\n🟢 **[Status: 1000 Coin ပေးပြီးပါပြီ]**")
            bot.answer_callback_query(call.id, "Reward ပေးပြီးပါပြီ ✅")
        except Exception as e:
            bot.answer_callback_query(call.id, "Error: User ကို Database တွင် မတွေ့ပါ။", show_alert=True)
            
    # Error Report Buttons
    elif call.data.startswith("err_"):
        data_parts = call.data.split("_")
        user_id = data_parts[-1]
        error_type = "Coin မဝင်ခြင်း" if "no_coin" in call.data else "Coin နှုတ်သွားခြင်း"
        
        bot.send_message(
            ADMIN_GROUP_ID, 
            f"🚨 **Error Report**\n\n👤 User Name: {call.from_user.first_name}\n🆔 User ID: {user_id}\n⚠️ ပြဿနာ: {error_type}"
        )
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"✅ သင့်ပြဿနာ ({error_type}) ကို Admin ထံ တိုင်ကြားပြီးပါပြီ။")
        bot.answer_callback_query(call.id, "Admin ထံ ပို့လိုက်ပါပြီ။")

# ==========================================
# ၁၀။ RUN BOT
# ==========================================
if __name__ == "__main__":
    print("🤖 CandyHub Bot is starting...")
    # Flask Web Server ကို Thread ဖြင့် run မည်
    threading.Thread(target=run_web, daemon=True).start()
    # Bot အလုပ်လုပ်မည်
    bot.infinity_polling()

```
    
