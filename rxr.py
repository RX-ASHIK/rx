import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import sqlite3
import uuid
from dotenv import load_dotenv
import os

# লোড এনভায়রনমেন্ট ভেরিয়েবল
load_dotenv()

# কনফিগারেশন
BOT_TOKEN = os.getenv("7641873839:AAHt4JsRYUMQDHrrEHdOB-No3ZrtJQeDxXc")  # .env ফাইলে রাখুন
REQUIRED_GROUP = "@EarningMasterbd24"
MINI_APP_URL = "https://earningmaster244.blogspot.com/?m=1&ref={ref_code}"

# ডাটাবেস সেটআপ
def init_db():
    conn = sqlite3.connect('/opt/render/project/src/referral.db')  # Render-সাপোর্টেড পাথ
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            referral_code TEXT UNIQUE,
            referrals INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        await track_referral(update, context)
        return

    user = update.effective_user
    try:
        member = await context.bot.get_chat_member(REQUIRED_GROUP, user.id)
        if member.status not in ["member", "administrator", "creator"]:
            await update.message.reply_html(
                f"⚠️ <b>Access Denied!</b>\n\n"
                f"Please join {REQUIRED_GROUP} first."
            )
            return

        conn = sqlite3.connect('/opt/render/project/src/referral.db')
        cursor = conn.cursor()
        cursor.execute('SELECT referral_code FROM users WHERE user_id = ?', (user.id,))
        result = cursor.fetchone()

        ref_code = result[0] if result else str(uuid.uuid4())[:8]
        if not result:
            cursor.execute(
                'INSERT INTO users (user_id, username, referral_code) VALUES (?, ?, ?)',
                (user.id, user.username or "", ref_code)
            )
            conn.commit()

        keyboard = [
            [InlineKeyboardButton("✨ Open Mini App", url=MINI_APP_URL.format(ref_code=ref_code))],
            [InlineKeyboardButton("📊 My Referrals", callback_data="my_refs")]
        ]
        await update.message.reply_html(
            f"🎉 Welcome, {user.first_name}!\n\n"
            f"Your referral link:\n<code>https://t.me/{context.bot.username}?start={ref_code}</code>",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("❌ Bot error. Please try later.")
    finally:
        if 'conn' in locals():
            conn.close()

async def track_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ref_code = context.args[0] if context.args else None
    if ref_code:
        conn = sqlite3.connect('/opt/render/project/src/referral.db')
        try:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE users SET referrals = referrals + 1 WHERE referral_code = ?',
                (ref_code,)
            )
            conn.commit()
        finally:
            conn.close()
    await start(update, context)

async def show_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    conn = sqlite3.connect('/opt/render/project/src/referral.db')
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT referrals FROM users WHERE user_id = ?', (query.from_user.id,))
        result = cursor.fetchone()
        count = result[0] if result else 0
        await query.edit_message_text(f"📊 Total referrals: {count}")
    finally:
        conn.close()

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(show_referrals, pattern="^my_refs$"))
    app.run_polling()

if __name__ == "__main__":
    main()
