from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import sqlite3
import uuid
from dotenv import load_dotenv
import os
import logging

# লগিং কনফিগার
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# এনভায়রনমেন্ট লোড
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
REQUIRED_GROUP = "@EarningMasterbd24"

# মিনি অ্যাপ URL (টেলিগ্রাম ওয়েব অ্যাপ ফরম্যাটে)
def get_mini_app_url(ref_code: str):
    return f"https://your-mini-app-domain.com?ref={ref_code}"  # আপনার রিয়েল মিনি অ্যাপ URL দিয়ে প্রতিস্থাপন করুন

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    try:
        # গ্রুপ মেম্বারশিপ চেক
        member = await context.bot.get_chat_member(REQUIRED_GROUP, user.id)
        if member.status not in ["member", "administrator", "creator"]:
            await update.message.reply_text("⚠️ প্রথমে আমাদের গ্রুপে জয়েন করুন!")
            return

        # রেফারেল কোড জেনারেট/ফেচ
        conn = sqlite3.connect('referral.db')
        cursor = conn.cursor()
        cursor.execute('SELECT referral_code FROM users WHERE user_id=?', (user.id,))
        result = cursor.fetchone()
        
        ref_code = result[0] if result else str(uuid.uuid4())[:8]
        if not result:
            cursor.execute('INSERT INTO users (user_id, referral_code) VALUES (?, ?)', (user.id, ref_code))
            conn.commit()
        
        # মিনি অ্যাপ বাটন তৈরি
        keyboard = [
            [InlineKeyboardButton(
                text="🚀 মিনি অ্যাপ ওপেন করুন", 
                web_app=WebAppInfo(url=get_mini_app_url(ref_code))
            ]
        ]
        
        await update.message.reply_text(
            f"👋 হ্যালো {user.first_name}!\n"
            f"আপনার রেফারেল কোড: {ref_code}",
            reply_markup=InlineKeyboardMarkup(keyboard)
            
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ সিস্টেমে সমস্যা হয়েছে!")
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
