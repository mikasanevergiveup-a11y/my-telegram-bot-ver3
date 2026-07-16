import telebot
from telebot import types
from flask import Flask, jsonify, render_template_string, request, redirect, url_for, session
import threading
import os
from datetime import datetime

# -----------------[ Secret Variables များ ဖတ်ခြင်း ]-----------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_GROUP_ID = int(os.environ.get("ADMIN_GROUP_ID", 0))

CHANNEL_1_ID = "@CandyHub_Ch"       
CHANNEL_2_ID = "@candyhubassissiant" 

CHANNEL_1_LINK = "https://t.me/CandyHub_Ch"
CHANNEL_2_LINK = "https://t.me/candyhubassissiant"

# Admin Web Panel အတွက် အချက်အလက်
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "CandyHubAdminPassword123!" 
# -----------------------------------------------------------

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')
app.secret_key = os.urandom(24)

# Database ယာယီသိမ်းဆည်းမည့်နေရာ
users_db = {} 
user_states = {}

# --- 🌐 WEBSITE TEMPLATES (HTML & CSS) ---

# ၁။ LOGIN WINDOW (Admin နှင့် User နှစ်ဦးလုံးအတွက်)
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CandyHub - Web Portal</title>
    <style>
        body { font-family: sans-serif; background: #f4f7f6; display: flex; justify-content: center; align-items: center; height: 100vh; margin:0;}
        .card { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); width: 320px; text-align: center;}
        input { width: 90%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        button { width: 90%; padding: 10px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;}
        .msg { color: red; font-size: 14px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🍬 CandyHub Login</h2>
        {% if msg %}<p class="msg">{{ msg }}</p>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="Gmail သို့မဟုတ် Admin Name" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">လော့ဂ်အင် ဝင်မည်</button>
        </form>
    </div>
</body>
</html>
"""

# ၂။ USER PROFILE DASHBOARD (အသုံးပြုသူများအတွက်)
USER_DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Profile - CandyHub</title>
    <style>
        body { font-family: sans-serif; background: #eef2f3; margin: 0; padding: 20px; display: flex; justify-content: center; }
        .profile-card { background: white; max-width: 450px; width: 100%; padding: 25px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.08); text-align: center; position: relative;}
        .avatar { width: 90px; height: 90px; background: #4CAF50; color: white; border-radius: 50%; display: inline-flex; justify-content: center; align-items: center; font-size: 32px; font-weight: bold; margin-bottom: 15px; text-transform: uppercase;}
        .info-group { text-align: left; background: #f9f9f9; padding: 15px; border-radius: 8px; margin: 12px 0; border-left: 5px solid #4CAF50;}
        .info-label { font-size: 12px; color: #777; text-transform: uppercase; font-weight: bold;}
        .info-value { font-size: 16px; color: #333; margin-top: 3px; font-weight: 500;}
        .coin-badge { background: #ff9800; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; display: inline-block; margin-bottom: 15px;}
        .logout-link { color: #f44336; text-decoration: none; font-weight: bold; font-size: 14px; display: inline-block; margin-top: 15px;}
    </style>
</head>
<body>
    <div class="profile-card">
        <div class="avatar">{{ user.name[0] }}</div>
        <h2>မင်္ဂလာပါ၊ {{ user.name }}</h2>
        <div class="coin-badge">💰 {{ user.coin }} Coins</div>
        
        <div class="info-group">
            <div class="info-label">အသုံးပြုသူ အမည် (TG Name)</div>
            <div class="info-value">{{ user.name }}</div>
        </div>
        <div class="info-group">
            <div class="info-label">Telegram User ID</div>
            <div class="info-value"><code>{{ user_id }}</code></div>
        </div>
        <div class="info-group">
            <div class="info-label">မှတ်ပုံတင်ထားသော Gmail</div>
            <div class="info-value">{{ user.email }}</div>
        </div>
        <div class="info-group">
            <div class="info-label">စကားဝှက် (Password)</div>
            <div class="info-value"><code>{{ user.password }}</code></div>
        </div>
        
        <a href="/logout" class="logout-link">❌ အကောင့်မှ ထွက်မည်</a>
    </div>
</body>
</html>
"""

# ၃။ ADMIN DASHBOARD (ပိုင်ရှင်/မန်နေဂျာများအတွက်)
ADMIN_DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard</title>
    <style>
        body { font-family: sans-serif; background: #f4f7f6; margin: 20px; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .stats { display: flex; gap: 20px; margin-bottom: 20px; }
        .stat-box { flex: 1; padding: 20px; background: #e8f5e9; border-radius: 5px; text-align: center; font-size: 18px; font-weight: bold;}
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #4CAF50; color: white; }
        .btn-del { background: #f44336; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; }
        .btn-edit { background: #008CBA; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; }
        input[type="number"] { width: 60px; padding: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🍬 CandyHub Admin/Owner Dashboard</h2>
        <a href="/logout" style="float: right; color: red; font-weight: bold;">Logout</a>
        
        <div class="stats">
            <div class="stat-box">စုစုပေါင်း User: {{ total_users }} ယောက်</div>
            <div class="stat-box" style="background: #e3f2fd;">Active User: {{ active_users }} ယောက်</div>
        </div>

        <h3>Active Users စာရင်း (ယနေ့အတွင်း Bot သုံးထားသူများ)</h3>
        <ul>
            {% for act in active_list %}
                <li><strong>{{ act.name }}</strong> (Gmail: {{ act.email }})</li>
            {% else %}
                <li>လတ်တလော Active ဖြစ်သူမရှိသေးပါ</li>
            {% endfor %}
        </ul>

        <h3>အသုံးပြုသူများအားလုံး စီမံခန့်ခွဲရန်ဇယား</h3>
        <table>
            <thead>
                <tr>
                    <th>User ID</th>
                    <th>Name</th>
                    <th>Gmail</th>
                    <th>Password</th>
                    <th>Coins (ပြင်ရန်)</th>
                    <th>လုပ်ဆောင်ချက်</th>
                </tr>
            </thead>
            <tbody>
                {% for uid, user in users.items() %}
                <tr>
                    <td>{{ uid }}</td>
                    <td>{{ user.name }}</td>
                    <td>{{ user.email }}</td>
                    <td><code>{{ user.password }}</code></td>
                    <td>
                        <form method="POST" action="/update_coin/{{ uid }}" style="display:inline;">
                            <input type="number" name="coin" value="{{ user.coin }}">
                            <button type="submit" class="btn-edit">Update</button>
                        </form>
                    </td>
                    <td>
                        <a href="/delete_user/{{ uid }}"><button class="btn-del" onclick="return confirm('ဤအကောင့်အား ဖျက်ပစ်ရန် သေချာပါသလား?')">Delete</button></a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

# --- 🌐 WEBSITE ROUTING LOGIC ---

@app.route('/', methods=['GET', 'POST'])
def login():
    msg = ""
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        
        # Admin လော့ဂ်အင် စစ်ဆေးခြင်း
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['role'] = 'admin'
            return redirect(url_for('admin_dashboard'))
            
        # User လော့ဂ်အင် စစ်ဆေးခြင်း (Gmail နှင့် Password ကို စစ်သည်)
        user_found = None
        user_id_found = None
        for uid, data in users_db.items():
            if data.get('email') == username and data.get('password') == password:
                user_found = data
                user_id_found = uid
                break
                
        if user_found:
            session['role'] = 'user'
            session['user_id'] = user_id_found
            return redirect(url_for('user_dashboard'))
        else:
            msg = "Gmail သို့မဟုတ် Password မှားယွင်းနေပါသည်။"
            
    return render_template_string(LOGIN_TEMPLATE, msg=msg)

@app.route('/my-profile')
def user_dashboard():
    if session.get('role') != 'user' or 'user_id' not in session:
        return redirect(url_for('login'))
    
    uid = session['user_id']
    if uid not in users_db:
        session.clear()
        return redirect(url_for('login'))
        
    return render_template_string(USER_DASHBOARD_TEMPLATE, user=users_db[uid], user_id=uid)

@app.route('/admin-panel')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    total_users = len(users_db)
    active_list = []
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    for uid, data in users_db.items():
        if data.get('last_active') == current_date:
            active_list.append(data)
            
    active_users = len(active_list)
    return render_template_string(ADMIN_DASHBOARD_TEMPLATE, users=users_db, total_users=total_users, active_users=active_users, active_list=active_list)

@app.route('/update_coin/<int:user_id>', methods=['POST'])
def update_coin(user_id):
    if session.get('role') == 'admin' and user_id in users_db:
        users_db[user_id]['coin'] = int(request.form['coin'])
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if session.get('role') == 'admin' and user_id in users_db:
        del users_db[user_id]
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)


# --- 🤖 TELEGRAM BOT FUNCTIONS ---

def update_active_status(user_id):
    if user_id in users_db:
        users_db[user_id]['last_active'] = datetime.now().strftime("%Y-%m-%d")

def check_channel_joined(user_id):
    try:
        member1 = bot.get_chat_member(CHANNEL_1_ID, user_id)
        member2 = bot.get_chat_member(CHANNEL_2_ID, user_id)
        return member1.status in ['member', 'administrator', 'creator'] and member2.status in ['member', 'administrator', 'creator']
    except:
        return False

# /start Command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("ခလုတ် 1 (CandyHub_Ch)", url=CHANNEL_1_LINK))
    markup.add(types.InlineKeyboardButton("ခလုတ် 2 (candyhubassissiant)", url=CHANNEL_2_LINK))
    markup.add(types.InlineKeyboardButton("🔄 Check Button (စစ်ဆေးမည်)", callback_data="check_join"))
    
    bot.send_message(message.chat.id, "မင်္ဂလာပါရှင့်။\nBot ကိုအသုံးပြုရန် အောက်က channel လေးတွေ join ပေးပါနော်\n(Join မှ bot သုံးရမှာဖြစ်ပါတယ်)", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def callback_check_join(call):
    user_id = call.from_user.id
    if check_channel_joined(user_id):
        bot.answer_callback_query(call.id, "အတည်ပြုချက် အောင်မြင်ပါသည်!")
        
        if user_id not in users_db:
            users_db[user_id] = {
                'name': call.from_user.first_name,
                'email': 'မထည့်ရသေးပါ',
                'password': 'မထည့်ရသေးပါ',
                'coin': 0,
                'last_active': datetime.now().strftime("%Y-%m-%d")
            }
        
        bot.send_message(call.message.chat.id, "✅ အတည်ပြုကြောင်းစာ- Channel Join တာ အောင်မြင်ပါပြီရှင့်။\n\n/profile - အကောင့်အချက်အလက်ကြည့်ရန်\n/check1 - Task စစ်ဆေးရန်\n/checkads - Ads စစ်ဆေးရန်")
    else:
        bot.answer_callback_query(call.id, "❌ Channel များအားလုံးကို မဝင်ရသေးပါ!", show_alert=True)

# /profile Command
@bot.message_handler(commands=['profile'])
def show_profile(message):
    user_id = message.from_user.id
    update_active_status(user_id)
    
    if user_id not in users_db:
        bot.reply_to(message, "⚠️ ကျေးဇူးပြု၍ /start ကို အရင်နှိပ်ပြီး စာရင်းသွင်းပါ။")
        return
        
    u = users_db[user_id]
    profile_text = (
        "👤 **လူကြီးမင်း၏ Profile အချက်အလက်များ**\n\n"
        f"📝 TG Name: {u['name']}\n"
        f"🆔 User ID: `{user_id}`\n"
        f"📧 Gmail: {u['email']}\n"
        f"🔑 Password: `{u['password']}`\n"
        f"💰 လက်ကျန် Coin: {u['coin']} Coins"
    )
    bot.send_message(message.chat.id, profile_text, parse_mode="Markdown")

# /check1 Command
@bot.message_handler(commands=['check1'])
def start_check1(message):
    user_id = message.from_user.id
    update_active_status(user_id)
    
    if not check_channel_joined(user_id):
        bot.reply_to(message, "⚠️ Channel အရင် Join ပါ။")
        return
        
    bot.reply_to(message, "📧 [Task 1] ကျေးဇူးပြု၍ လူကြီးမင်း၏ Email နှင့် Password ကို (ဥပမာ- example@gmail.com / pass123) ပုံစံဖြင့် ရိုက်ထည့်ပေးပါ။")
    user_states[user_id] = {'step': 'WAITING_TASK_INFO', 'type': 'check1'}

# /checkads Command
@bot.message_handler(commands=['checkads'])
def start_checkads(message):
    user_id = message.from_user.id
    update_active_status(user_id)
    
    if not check_channel_joined(user_id):
        bot.reply_to(message, "⚠️ Channel အရင် Join ပါ။")
        return
        
    bot.reply_to(message, "📸 [Ads Task] ကျေးဇူးပြု၍ Ads ကြည့်ရှုထားသည့် သက်သေခံဓာတ်ပုံ (Photo) ကို ပို့ပေးပါရန်။")
    user_states[user_id] = {'step': 'WAITING_ADS_PHOTO', 'type': 'checkads'}

# စာသားလက်ခံခြင်း (Email/Password ရိုက်ချက်)
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('step') == 'WAITING_TASK_INFO')
def get_task_info(message):
    user_id = message.from_user.id
    text = message.text
    
    if "/" in text:
        parts = text.split("/")
        users_db[user_id]['email'] = parts[0].strip()
        users_db[user_id]['password'] = parts[1].strip()
    else:
        users_db[user_id]['email'] = text.strip()
        users_db[user_id]['password'] = "မသတ်မှတ်ရသေး"

    user_states[user_id]['step'] = 'WAITING_TASK_PHOTO'
    bot.reply_to(message, "📸 ကျေးဇူးပြု၍ သက်သေခံ ဓာတ်ပုံ (Photo) ကို ပို့ပေးပါရန်။")

# ဓာတ်ပုံလက်ခံခြင်း
@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    
    if state.get('step') == 'WAITING_TASK_PHOTO' and state.get('type') == 'check1':
        photo_id = message.photo[-1].file_id
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Confirm", callback_data=f"c1_confirm_{user_id}"),
                   types.InlineKeyboardButton("❌ Reject", callback_data=f"c1_reject_{user_id}"))
        
        msg_text = f"📩 **[Task 1] စစ်ဆေးရန် တောင်းဆိုချက်**\n\n👤 Name: {users_db[user_id]['name']}\n🆔 ID: `{user_id}`\n📧 Gmail: {users_db[user_id]['email']}\n🔑 Pass: `{users_db[user_id]['password']}`\n⏰ အချိန်: {time_str}"
        bot.send_photo(ADMIN_GROUP_ID, photo_id, caption=msg_text, reply_markup=markup, parse_mode="Markdown")
        bot.reply_to(message, "⏳ အချက်အလက်များကို Admin Group သို့ တင်ပြထားပါသည်။")
        user_states[user_id] = {}
        
    elif state.get('step') == 'WAITING_ADS_PHOTO' and state.get('type') == 'checkads':
        photo_id = message.photo[-1].file_id
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Confirm", callback_data=f"ads_confirm_{user_id}"),
                   types.InlineKeyboardButton("❌ Reject", callback_data=f"ads_reject_{user_id}"))
        
        msg_text = f"📺 **[Ads Task] စစ်ဆေးရန် တောင်းဆိုချက်**\n\n👤 Name: {users_db[user_id]['name']}\n🆔 User ID: `{user_id}`"
        bot.send_photo(ADMIN_GROUP_ID, photo_id, caption=msg_text, reply_markup=markup, parse_mode="Markdown")
        bot.reply_to(message, "⏳ Ads အချက်အလက်များကို Admin သို့ တင်ပြထားပါသည်။")
        user_states[user_id] = {}

# Admin ခလုတ်များ ကိုင်တွယ်ခြင်း
@bot.callback_query_handler(func=lambda call: call.data.startswith(("c1_", "ads_")))
def admin_actions(call):
    data = call.data.split("_")
    task_type = data[0] 
    action = data[1]    
    target_uid = int(data[2])
    
    if action == "confirm":
        if target_uid in users_db:
            users_db[target_uid]['coin'] += 10 
            
        bot.edit_message_caption(f"✅ အတည်ပြုပြီးပါပြီ (User ID: {target_uid})", chat_id=call.message.chat.id, message_id=call.message.message_id)
        
        if task_type == "c1":
            bot.send_message(target_uid, "🎉 candyhubမှ task ကိုစစ်ဆေးပြီးပါပြီ။")
        else:
            bot.send_message(target_uid, "🎉 candy(ads) မှ စစ်ဆေးပြီးပါပီ့။")
            
    elif action == "reject":
        bot.edit_message_caption(f"❌ Ngreenspalလိုက်ပါပြီ (User ID: {target_uid})", chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(target_uid, "❌ စိတ်မကောင်းပါဘူးရှင့်၊ လူကြီးမင်းပေးပို့သော သက်သေခံချက် မပြည့်စုံသဖြင့် ငြင်းပယ်ခံရပါသည်။")

if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    print("CandyHub System is Live...")
    bot.infinity_polling()

