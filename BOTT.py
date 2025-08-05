import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import logging
import sqlite3
from datetime import datetime
import random

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

# Emoji Decorations
EMOJI = {
    "welcome": "🌟✨💫",
    "money": "💰🪙💵",
    "success": "✅🎉🥳",
    "error": "❌⚠️😢",
    "referral": "👥📢🤝",
    "support": "🛎️💬🆘"
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
        has_joined_channel BOOLEAN DEFAULT FALSE
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

async def send_animated_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    messages = [
        f"{EMOJI['welcome']} <b>Welcome, {user.first_name}!</b> {EMOJI['welcome']}",
        "🌟 Your journey to earnings starts here! 🌟",
        "⚡ Powering up your account... ⚡",
        f"{EMOJI['money']} <i>Loading financial dashboard...</i> {EMOJI['money']}"
    ]
    
    for msg in messages:
        await update.message.reply_text(msg, parse_mode='HTML')
        await asyncio.sleep(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_animated_welcome(update, context)
    
    user = update.effective_user
    referral_code = context.args[0] if context.args else None
    
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    # Register user if new
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user.id,))
    if not cursor.fetchone():
        cursor.execute('''
        INSERT INTO users (user_id, username, first_name, last_name, referred_by)
        VALUES (?, ?, ?, ?, ?)
        ''', (user.id, user.username, user.first_name, user.last_name, referral_code))
        
        # Process referral if exists
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
    
    # Check channel membership
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
    
    # Show main menu
    await show_dashboard(update, context)

async def show_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance, referral_count FROM users WHERE user_id = ?", (user.id,))
    balance, ref_count = cursor.fetchone()
    conn.close()
    
    # Create beautiful dashboard
    dashboard = f"""
✨ <b>EARNING MASTER DASHBOARD</b> ✨

👤 <b>User:</b> {user.first_name} {user.last_name or ''}
🆔 <b>ID:</b> <code>{user.id}</code>
📅 <b>Joined:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}

{EMOJI['money']} <b>Balance:</b> <code>{balance} BDT</code>
{EMOJI['referral']} <b>Referrals:</b> <code>{ref_count}</code>

💎 <i>Earn more by referring friends!</i>
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

async def earn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    earning_options = [
        {"emoji": "📺", "title": "Watch Ads", "earn": "0.10-1.00 BDT"},
        {"emoji": "📝", "title": "Complete Surveys", "earn": "5-20 BDT"},
        {"emoji": "🎮", "title": "Play Games", "earn": "1-10 BDT"}
    ]
    
    keyboard = []
    for option in earning_options:
        keyboard.append([
            InlineKeyboardButton(
                f"{option['emoji']} {option['title']} (+{option['earn']})", 
                callback_data=f"earn_{option['title'].lower().replace(' ', '_')}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton(f"{EMOJI['money']} Back to Dashboard", callback_data="dashboard")])
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"<b>{EMOJI['money']} Earning Opportunities {EMOJI['money']}</b>\n\n"
             "Choose how you want to earn money:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

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
        [InlineKeyboardButton(f"{EMOJI['money']} Copy Link", callback_data="copy_link")]
    ]
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"<b>{EMOJI['referral']} Referral Program {EMOJI['referral']}</b>\n\n"
             f"🔗 Your referral link:\n<code>{referral_link}</code>\n\n"
             f"👥 Total referrals: <b>{ref_count}</b>\n"
             f"💰 Earn <b>10 BDT</b> for each successful referral!\n\n"
             "<i>Share your link with friends and earn together!</i>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(CommandHandler("earn", earn_command))
    application.add_handler(CommandHandler("refer", refer_command))
    
    application.run_polling()

if __name__ == "__main__":
    main()
