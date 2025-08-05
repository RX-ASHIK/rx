import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import logging
import sqlite3
from datetime import datetime, time
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = "7641873839:AAHt4JsRYUMQDHrrEHdOB-No3ZrtJQeDxXc"
CHANNEL_USERNAME = "@EarningMasterbd24"
SUPPORT_USERNAME = "@EarningMaster_help"
ADMIN_ID = "5989402185"
TIMEZONE = pytz.timezone("Asia/Dhaka")  # Bangladesh timezone

# Emoji Decorations
EMOJI = {
    "welcome": "🌟✨💫",
    "money": "💰🪙💵",
    "success": "✅🎉🥳",
    "error": "❌⚠️😢",
    "referral": "👥📢🤝",
    "support": "🛎️💬🆘",
    "notification": "🔔📢👀",
    "reset": "🔄⏰🎯"
}

# Database setup
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        balance REAL DEFAULT 0,
        referral_count INTEGER DEFAULT 0,
        referred_by INTEGER,
        join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        has_joined_channel BOOLEAN DEFAULT FALSE,
        ads_watched_today INTEGER DEFAULT 0,
        last_reset_date TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        type TEXT,
        status TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    ''')
    
    conn.commit()
    conn.close()

init_db()

# Scheduler setup
scheduler = AsyncIOScheduler(timezone=TIMEZONE)

async def reset_daily_tasks():
    """Reset all users' daily tasks at 10 AM"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    today = datetime.now(TIMEZONE).strftime('%Y-%m-%d')
    
    cursor.execute("""
    UPDATE users 
    SET ads_watched_today = 0,
        last_reset_date = ?
    WHERE last_reset_date IS NULL OR last_reset_date != ?
    """, (today, today))
    
    conn.commit()
    
    # Get all active users
    cursor.execute("SELECT user_id FROM users WHERE has_joined_channel = TRUE")
    users = cursor.fetchall()
    conn.close()
    
    # Send notification to all users
    for user in users:
        try:
            await send_reset_notification(user[0])
        except Exception as e:
            logger.error(f"Error sending reset notification to {user[0]}: {e}")

async def send_reset_notification(user_id: int):
    """Send beautiful reset notification to a user"""
    message = (
        f"{EMOJI['notification']} <b>Good Morning! Daily Reset Complete</b> {EMOJI['notification']}\n\n"
        f"{EMOJI['reset']} <i>Your daily tasks have been refreshed!</i> {EMOJI['reset']}\n\n"
        "🎯 <b>New Opportunities Available:</b>\n"
        "▫️ Watch ads (50 available)\n"
        "▫️ Complete surveys\n"
        "▫️ Play games\n\n"
        "💰 <b>Start earning now!</b>"
    )
    
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI['money']} Start Earning", callback_data="earn")]
    ]
    
    from telegram import Bot
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(
        chat_id=user_id,
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def check_channel_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            conn = sqlite3.connect('bot_data.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET has_joined_channel = TRUE WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            return True
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    referral_code = context.args[0] if context.args else None
    
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user.id,))
    user_data = cursor.fetchone()
    
    if not user_data:
        cursor.execute('''
        INSERT INTO users (user_id, username, first_name, last_name, referred_by)
        VALUES (?, ?, ?, ?, ?)
        ''', (user.id, user.username, user.first_name, user.last_name, referral_code))
        
        if referral_code:
            try:
                referrer_id = int(referral_code.split('_')[1])
                cursor.execute("UPDATE users SET referral_count = referral_count + 1, balance = balance + 10 WHERE user_id = ?", (referrer_id,))
                cursor.execute('''
                INSERT INTO transactions (user_id, amount, type, status)
                VALUES (?, ?, ?, ?)
                ''', (referrer_id, 10, 'referral', 'completed'))
            except:
                pass
    
    conn.commit()
    
    is_member = await check_channel_membership(update, context)
    
    if not is_member:
        keyboard = [
            [InlineKeyboardButton(f"{EMOJI['success']} Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton(f"{EMOJI['success']} Verify Join", callback_data="check_join")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"<b>{EMOJI['error']} Channel Membership Required {EMOJI['error']}</b>\n\n"
            f"To access all features, please join our official channel:\n"
            f"{CHANNEL_USERNAME}\n\n"
            "After joining, click the button below:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return
    
    await show_dashboard(update, context)

async def show_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance, referral_count, ads_watched_today FROM users WHERE user_id = ?", (user.id,))
    balance, ref_count, ads_watched = cursor.fetchone()
    conn.close()
    
    dashboard = f"""
✨ <b>EARNING MASTER DASHBOARD</b> ✨

👤 <b>User:</b> {user.first_name} {user.last_name or ''}
🆔 <b>ID:</b> <code>{user.id}</code>
📅 <b>Today:</b> {datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M')}

{EMOJI['money']} <b>Balance:</b> <code>{balance} BDT</code>
{EMOJI['referral']} <b>Referrals:</b> <code>{ref_count}</code>
📊 <b>Ads Watched Today:</b> <code>{ads_watched}/50</code>

💎 <i>Daily reset at 10 AM (GMT+6)</i>
"""
    
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI['money']} Earn Money", callback_data="earn")],
        [InlineKeyboardButton(f"{EMOJI['referral']} Refer Friends", callback_data="refer")],
        [InlineKeyboardButton(f"{EMOJI['support']} Support", url=f"https://t.me/{SUPPORT_USERNAME[1:]}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=dashboard,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "check_join":
        is_member = await check_channel_membership(update, context)
        
        if is_member:
            await query.edit_message_text(
                f"{EMOJI['success']} <b>Verification Successful!</b> {EMOJI['success']}\n\n"
                "You now have full access to all features!",
                parse_mode='HTML'
            )
            await show_dashboard(update, context)
        else:
            await query.answer(f"{EMOJI['error']} You haven't joined the channel yet!", show_alert=True)
    
    elif query.data == "earn":
        await earn_command(update, context)
    
    elif query.data == "refer":
        await refer_command(update, context)
    
    elif query.data == "dashboard":
        await show_dashboard(update, context)

async def earn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT ads_watched_today FROM users WHERE user_id = ?", (user.id,))
    ads_watched = cursor.fetchone()[0]
    conn.close()
    
    earning_options = [
        {"emoji": "📺", "title": "Watch Ads", "earn": "0.10-1.00 BDT", "left": f"{50 - ads_watched} left today"},
        {"emoji": "📝", "title": "Complete Surveys", "earn": "5-20 BDT", "left": "Unlimited"},
        {"emoji": "🎮", "title": "Play Games", "earn": "1-10 BDT", "left": "10 left today"}
    ]
    
    keyboard = []
    for option in earning_options:
        keyboard.append([
            InlineKeyboardButton(
                f"{option['emoji']} {option['title']} (+{option['earn']}) - {option['left']}", 
                callback_data=f"earn_{option['title'].lower().replace(' ', '_')}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton(f"{EMOJI['money']} Back to Dashboard", callback_data="dashboard")])
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"<b>{EMOJI['money']} Earning Opportunities {EMOJI['money']}</b>\n\n"
             "💰 <i>Choose how you want to earn money:</i>\n\n"
             f"⏰ <b>Daily reset at 10 AM (GMT+6)</b>\n"
             f"🔄 <i>Next reset in: {time_until_reset()}</i>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

def time_until_reset():
    now = datetime.now(TIMEZONE)
    reset_time = time(10, 0)  # 10 AM
    
    if now.time() < reset_time:
        target = datetime.combine(now.date(), reset_time)
    else:
        target = datetime.combine(now.date() + timedelta(days=1), reset_time)
    
    delta = target - now
    hours, remainder = divmod(delta.seconds, 3600)
    minutes = remainder // 60
    return f"{hours}h {minutes}m"

async def refer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT referral_count FROM users WHERE user_id = ?", (user.id,))
    ref_count = cursor.fetchone()[0]
    conn.close()
    
    referral_link = f"https://t.me/{context.bot.username}?start=ref_{user.id}"
    
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI['referral']} Share Link", url=f"https://t.me/share/url?url={referral_link}&text=Join%20Earning%20Master%20to%20earn%20money!")],
        [InlineKeyboardButton(f"{EMOJI['money']} Copy Link", callback_data="copy_link")],
        [InlineKeyboardButton(f"{EMOJI['money']} Back to Dashboard", callback_data="dashboard")]
    ]
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"<b>{EMOJI['referral']} Referral Program {EMOJI['referral']}</b>\n\n"
             f"🔗 <b>Your referral link:</b>\n<code>{referral_link}</code>\n\n"
             f"👥 <b>Total referrals:</b> <code>{ref_count}</code>\n"
             f"💰 <b>Earn 10 BDT</b> for each successful referral!\n\n"
             "<i>Share your link with friends and earn together!</i>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add daily reset job
    scheduler.add_job(
        reset_daily_tasks,
        trigger='cron',
        hour=10,  # 10 AM
        minute=0,
        timezone=TIMEZONE
    )
    scheduler.start()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(CommandHandler("earn", earn_command))
    application.add_handler(CommandHandler("refer", refer_command))
    application.add_handler(CommandHandler("dashboard", show_dashboard))
    
    application.run_polling()

if __name__ == "__main__":
    main()
