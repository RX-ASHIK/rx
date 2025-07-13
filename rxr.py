# ফাইল: rx_bot.py

import os
from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from pymongo import MongoClient
import requests
from datetime import datetime
import pytz

# ========== CONFIGURATION ==========
BOT_TOKEN = "7964248140:7941077439:AAEUf4Crt9Ca6N-N8N_tOB30jsHln5LxZWg"
API_ID = 27220846
API_HASH = "ade7381d9e0ee7b824d1970b692b8ee9"
MONGO_URL = "mongodb+srv://mdashekurislam8:KNiF0a1miKLkV4qy@rx.x3nlhsv.mongodb.net/?retryWrites=true&w=majority&appName=Rx"
ADMIN_ID = 5989402185
JOIN_CHANNELS = ["-1002120314355", "-1002315991867"]

# ===== MongoDB Connect =====
client_mongo = MongoClient(MONGO_URL)
db = client_mongo["rx_earning"]
users = db["users"]
withdraws = db["withdraws"]

# ===== Pyrogram Client =====
app = Client("rx_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# ========== HELPER FUNCTIONS ==========
async def has_joined_required_channels(client, user_id):
    for channel in JOIN_CHANNELS:
        try:
            member = await client.get_chat_member(channel, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def add_user(user_id, referred_by=None):
    if not users.find_one({"_id": user_id}):
        users.insert_one({"_id": user_id, "balance": 0, "referred_by": referred_by, "refs": 0})

def get_user(user_id):
    return users.find_one({"_id": user_id})

def update_balance(user_id, amount):
    users.update_one({"_id": user_id}, {"$inc": {"balance": amount}})

def add_referral(user_id):
    users.update_one({"_id": user_id}, {"$inc": {"refs": 1}})

def shorten_link(ref_link):
    try:
        r = requests.get(f"https://tinyurl.com/api-create.php?url={ref_link}")
        return r.text
    except:
        return ref_link

def is_real_user(user):
    return not getattr(user, "is_bot", True) and (user.username or user.first_name)

# ========== START COMMAND ==========
@app.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    user_id = message.from_user.id
    args = message.text.split()
    referred_by = int(args[1]) if len(args) > 1 else None

    if not await has_joined_required_channels(client, user_id):
        await message.reply("🚫 আপনি এখনও সকল চ্যানেলে জয়েন করেননি!\nদয়া করে জয়েন করে আবার /start দিন।")
        return

    add_user(user_id, referred_by)

    if referred_by and referred_by != user_id:
        referred_user = await client.get_users(user_id)
        if not is_real_user(referred_user):
            await message.reply("❌ বট বা ফেক অ্যাকাউন্ট দিয়ে রেফার করা যাবে না।")
            return
        ref_user = get_user(referred_by)
        if ref_user:
            update_balance(referred_by, 3)
            add_referral(referred_by)

    long_link = f"https://t.me/{(await client.get_me()).username}?start={user_id}"
    short_link = shorten_link(long_link)

    await message.reply(
        f"""
👋 স্বাগতম RX ERNING বটে!

🎁 প্রতি রেফার = ৩ টাকা
💰 ব্যালেন্স চেক ➜ /balance
🏦 উত্তোলন করতে ➜ /withdraw
🔗 রেফার লিংক: {short_link}
        """
    )

# ========== BALANCE ==========
@app.on_message(filters.command("balance"))
async def balance_handler(client, message: Message):
    user = get_user(message.from_user.id)
    if not user:
        await message.reply("❌ অ্যাকাউন্ট খুঁজে পাওয়া যায়নি। /start দিন।")
        return
    await message.reply(f"💰 ব্যালেন্স: {user['balance']} টাকা\n👥 রেফার করেছেন: {user['refs']} জন")

# ========== REFER ==========
@app.on_message(filters.command("refer"))
async def refer_handler(client, message: Message):
    user_id = message.from_user.id
    long_link = f"https://t.me/{(await client.get_me()).username}?start={user_id}"
    short_link = shorten_link(long_link)
    await message.reply(f"📲 আপনার রেফার লিংক:\n{short_link}")

# ========== WITHDRAW ==========
temp_data = {}

@app.on_message(filters.command("withdraw"))
async def withdraw_start(client, message: Message):
    user_id = message.from_user.id
    temp_data[user_id] = {}
    markup = ReplyKeyboardMarkup([["bKash", "Nagad"]], one_time_keyboard=True, resize_keyboard=True)
    await message.reply("📱 কোন মাধ্যমে টাকা উত্তোলন করতে চান?", reply_markup=markup)

@app.on_message(filters.text & filters.private)
async def withdraw_steps(client, message: Message):
    user_id = message.from_user.id
    if user_id not in temp_data:
        return

    step = temp_data[user_id]
    user = get_user(user_id)
    if not user:
        await message.reply("❌ অ্যাকাউন্ট খুঁজে পাওয়া যায়নি। /start দিন।")
        del temp_data[user_id]
        return

    if "method" not in step:
        method = message.text.strip()
        if method not in ["bKash", "Nagad"]:
            await message.reply("❌ শুধু bKash বা Nagad নির্বাচন করুন।")
            return
        temp_data[user_id]["method"] = method
        await message.reply("📞 আপনার নাম্বার দিন:", reply_markup=ReplyKeyboardRemove())

    elif "number" not in step:
        number = message.text.strip()
        temp_data[user_id]["number"] = number
        amount = user["balance"]
        if amount < 50:
            await message.reply("❌ উত্তোলনের জন্য ন্যূনতম ৫০ টাকা থাকতে হবে।")
            del temp_data[user_id]
            return
        withdraws.insert_one({
            "user_id": user_id,
            "method": step["method"],
            "number": number,
            "status": "pending",
            "amount": amount,
        })
        await client.send_message(ADMIN_ID, f"🔔 নতুন উইথড্র:\n\n👤 {user_id}\n📦 {step['method']}\n📱 {number}\n💰 {amount} টাকা")
        await message.reply("✅ আপনার অনুরোধ গ্রহণ করা হয়েছে। ২৪ ঘণ্টার মধ্যে পেমেন্ট করা হবে।")
        del temp_data[user_id]

# ========== APPROVE WITHDRAW ==========
@app.on_message(filters.command("approve") & filters.user(ADMIN_ID))
async def approve_withdraw(client, message: Message):
    try:
        _, uid = message.text.split()
        uid = int(uid)
        withdraw_data = withdraws.find_one({"user_id": uid, "status": "pending"})
        if not withdraw_data:
            await message.reply("❌ কোনো pending উইথড্র খুঁজে পাওয়া যায়নি।")
            return
        withdraws.update_one({"user_id": uid, "status": "pending"}, {"$set": {"status": "completed"}})
        users.update_one({"_id": uid}, {"$set": {"balance": 0}})
        await message.reply(f"✅ ইউজার `{uid}` এর উইথড্র Approve করা হয়েছে।")
        await client.send_message(uid, "✅ আপনার উইথড্র অনুরোধ সফলভাবে এপ্রুভ করা হয়েছে।")
    except:
        await message.reply("❌ কমান্ড ভুল। /approve USERID")

# ========== VIEW WITHDRAW ==========
@app.on_message(filters.command("withdraws") & filters.user(ADMIN_ID))
async def view_withdraws(client, message: Message):
    pending = list(withdraws.find({"status": "pending"}))
    if not pending:
        await message.reply("✅ কোনো pending উইথড্র নেই।")
        return
    msg_text = "🧾 Pending Withdraw Requests:\n\n"
    for w in pending:
        msg_text += (
            f"👤 ইউজার: `{w['user_id']}`\n"
            f"📱 নাম্বার: `{w['number']}`\n"
            f"💰 পরিমাণ: `{w['amount']} টাকা`\n"
            f"📦 মাধ্যম: `{w['method']}`\n\n"
        )
    await message.reply(msg_text)

# ========== WITHDRAW HISTORY ==========
@app.on_message(filters.command("myhistory"))
async def my_history(client, message: Message):
    user_id = message.from_user.id
    my_withdraws = list(withdraws.find({"user_id": user_id}))
    if not my_withdraws:
        await message.reply("ℹ️ কোনো উইথড্র ইতিহাস পাওয়া যায়নি।")
        return
    text = "📜 আপনার উইথড্র ইতিহাস:\n\n"
    for w in my_withdraws:
        text += (
            f"📦 মাধ্যম: {w['method']}\n"
            f"📱 নাম্বার: {w['number']}\n"
            f"💰 টাকা: {w['amount']}\n"
            f"⏳ স্ট্যাটাস: {w['status'].capitalize()}\n\n"
        )
    await message.reply(text)

# ========== MANUAL BALANCE (Admin) ==========
@app.on_message(filters.command("addbal") & filters.user(ADMIN_ID))
async def add_balance_cmd(client, message: Message):
    try:
        _, uid, amount = message.text.split()
        update_balance(int(uid), int(amount))
        await message.reply(f"✅ ইউজার `{uid}` এর ব্যালেন্সে {amount} টাকা যোগ হয়েছে।")
    except:
        await message.reply("❌ কমান্ড ভুল। /addbal 123456 10")

@app.on_message(filters.command("removebal") & filters.user(ADMIN_ID))
async def remove_balance_cmd(client, message: Message):
    try:
        _, uid, amount = message.text.split()
        update_balance(int(uid), -int(amount))
        await message.reply(f"✅ ইউজার `{uid}` এর ব্যালেন্স থেকে {amount} টাকা কাটা হয়েছে।")
    except:
        await message.reply("❌ কমান্ড ভুল। /removebal 123456 10")

# ========== Recharge Command ==========
@app.on_message(filters.command("recharge"))
async def recharge_info(client, message: Message):
    await message.reply(
        "📲 আপনি সরাসরি রিচার্জ করতে চাইলে আমাদের Admin এর সাথে যোগাযোগ করুন:\n\n"
        "👤 @ashik8f"
    )

# ========== NAMAZ TIME ==========
@app.on_message(filters.command("namaz"))
async def namaz_time(client, message: Message):
    try:
        response = requests.get("http://api.aladhan.com/v1/timingsByCity?city=Dhaka&country=Bangladesh&method=2")
        data = response.json()["data"]["timings"]
        now = datetime.now(pytz.timezone("Asia/Dhaka")).strftime("%I:%M %p, %d %B %Y")
        text = f"🕌 আজকের নামাজের সময় (ঢাকা):\n🗓️ {now}\n\n"
        text += f"📿 Fajr: {data['Fajr']}\n🌄 Sunrise: {data['Sunrise']}\n🕛 Dhuhr: {data['Dhuhr']}\n🌇 Asr: {data['Asr']}\n🌅 Maghrib: {data['Maghrib']}\n🌙 Isha: {data['Isha']}"
        await message.reply(text)
    except:
        await message.reply("❌ নামাজের সময় আনতে সমস্যা হয়েছে।")

# ========== BOT START ==========
print("✅ RX ERNING Bot চালু হচ্ছে...")
app.run()
