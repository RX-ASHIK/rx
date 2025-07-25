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
BOT_TOKEN = os.getenv("BOT_TOKEN")
REQUIRED_GROUP = "@EarningMasterbd24"
MINI_APP_URL = "https://earningmaster244.blogspot.com/?m=1&ref={ref_code}"  # সঠিক URL ফরম্যাট

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
    if context.args:  # রেফারেল লিংক দিয়ে এসেছে
        await track_referral(update, context)
        return

    user = update.effective_user
    try:
        # গ্রুপ মেম্বারশিপ চেক
        member = await context.bot.get_chat_member(REQUIRED_GROUP, user.id)
        if member.status not in ["member", "administrator", "creator"]:
            await update.message.reply_html(
                f"⚠️ <b>Access Denied!</b>\n\n"
                f"Join {REQUIRED_GROUP} first, then try /start again."
            )
            return

        # রেফারেল কোড জেনারেট বা ফেচ
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

        # সঠিক মিনি অ্যাপ URL তৈরি
        mini_app_url = f"https://t.me/{context.bot.username}/app?startapp={ref_code}"  # Telegram Web App লিংক
        blog_url = MINI_APP_URL.format(ref_code=ref_code)  # আপনার ব্লগ URL

        keyboard = [
            [InlineKeyboardButton("✨ Open Mini App", web_app=WebAppInfo(url=blog_url))],  # WebAppInfo ব্যবহার
            [InlineKeyboardButton("📊 My Referrals", callback_data="my_refs")]
        ]
        
        await update.message.reply_html(
            f"🎉 <b>Welcome, {user.first_name}!</b>\n\n"
            f"🔗 Your referral link:\n<code>https://t.me/{context.bot.username}?start={ref_code}</code>\n\n"
            "Click below to open the Mini App:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("❌ Bot error. Contact admin.")
    finally:
        if 'conn' in locals():
            conn.close()

# ... (বাকি কোড একই রেখে দিন track_referral এবং show_referrals ফাংশন)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(show_referrals, pattern="^my_refs$"))
    app.run_polling()

if __name__ == "__main__":
    main()
