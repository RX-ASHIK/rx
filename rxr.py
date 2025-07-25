from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
import os
import logging

# লগিং কনফিগার
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# এনভায়রনমেন্ট লোড
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# গ্রুপ লিস্ট (পরবর্তীতে একাধিক গ্রুপ অ্যাড করতে পারেন)
REQUIRED_GROUPS = ["@EarningMasterbd24"]  # বর্তমানে শুধু একটি গ্রুপ

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    try:
        # সব গ্রুপ চেক করা (বর্তমানে শুধু একটি গ্রুপ)
        for group in REQUIRED_GROUPS:
            member = await context.bot.get_chat_member(group, user.id)
            if member.status not in ["member", "administrator", "creator"]:
                await update.message.reply_html(
                    "🌟 <b>Welcome to Our Community!</b>\n\n"
                    "To use this bot, please join our official group:\n"
                    f"{group}\n\n"
                    "After joining, send /start again."
                )
                return

        # গ্রুপে থাকলে প্রফেশনাল ওয়েলকাম মেসেজ
        await update.message.reply_html(
            "🛎️ <b>Welcome Aboard!</b>\n\n"
            f"Hello <b>{user.first_name}</b>,\n\n"
            "Thank you for being part of our community. "
            "This bot is designed to provide you with exclusive services.\n\n"
            "Type /help to see available commands."
        )

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(
            "⚠️ We're experiencing technical difficulties. "
            "Please try again later."
        )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
