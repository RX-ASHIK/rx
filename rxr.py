import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import sqlite3
import uuid
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv("7641873839:AAHt4JsRYUMQDHrrEHdOB-No3ZrtJQeDxXc")  # টোকেন .env ফাইলে রাখুন
REQUIRED_GROUP = "@EarningMasterbd24"
MINI_APP_URL = "https://earningmaster244.blogspot.com/?m=1&ref={ref_code}"  # Fixed URL format

# Database Setup
def init_db():
    conn = None
    try:
        conn = sqlite3.connect('referral.db')
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
    except Exception as e:
        logging.error(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

init_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:  # রেফারেল লিংক দিয়ে এসেছে
        await track_referral(update, context)
        return

    user = update.effective_user
    try:
        # Check group membership
        member = await context.bot.get_chat_member(REQUIRED_GROUP, user.id)
        if member.status not in ["member", "administrator", "creator"]:
            await update.message.reply_html(
                f"⚠️ <b>Access Denied!</b>\n\n"
                f"Join {REQUIRED_GROUP} first, then try /start again."
            )
            return

        # Generate or get referral code
        conn = sqlite3.connect('referral.db')
        cursor = conn.cursor()
        cursor.execute('SELECT referral_code FROM users WHERE user_id = ?', (user.id,))
        result = cursor.fetchone()

        if not result:
            ref_code = str(uuid.uuid4())[:8]  # Unique 8-char code
            cursor.execute(
                'INSERT INTO users (user_id, username, referral_code) VALUES (?, ?, ?)',
                (user.id, user.username or "", ref_code)
            )
            conn.commit()
        else:
            ref_code = result[0]

        # Send welcome message
        keyboard = [
            [InlineKeyboardButton("✨ Open Mini App", url=MINI_APP_URL.format(ref_code=ref_code))],
            [InlineKeyboardButton("📊 My Referrals", callback_data="my_refs")]
        ]
        await update.message.reply_html(
            f"🎉 <b>Welcome, {user.first_name}!</b>\n\n"
            f"🔗 Your referral link:\n<code>https://t.me/{context.bot.username}?start={ref_code}</code>\n\n"
            "Earn rewards by sharing this link!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("❌ Bot error. Contact admin.")
    finally:
        if 'conn' in locals():
            conn.close()

async def track_referral(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    ref_code = context.args[0] if context.args else None

    if ref_code:
        conn = None
        try:
            conn = sqlite3.connect('referral.db')
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE users SET referrals = referrals + 1 WHERE referral_code = ?',
                (ref_code,)
            )
            conn.commit()
            await update.message.reply_text(f"✅ Referral from {user.first_name} recorded!")
        except Exception as e:
            logging.error(f"Referral tracking error: {e}")
        finally:
            if conn:
                conn.close()

    await start(update, context)  # Show normal start menu after tracking

async def show_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    conn = None
    try:
        conn = sqlite3.connect('referral.db')
        cursor = conn.cursor()
        cursor.execute('SELECT referrals FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()

        if result:
            await query.edit_message_text(f"📊 Your total referrals: {result[0]}")
        else:
            await query.edit_message_text("You don't have any referrals yet!")
    except Exception as e:
        logging.error(f"Error showing referrals: {e}")
        await query.edit_message_text("❌ Failed to load referrals.")
    finally:
        if conn:
            conn.close()

def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(show_referrals, pattern="^my_refs$"))
    
    # Error handler
    app.add_error_handler(lambda update, context: logging.error(context.error))
    
    app.run_polling()

if __name__ == "__main__":
    main()
