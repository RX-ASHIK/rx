from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv
import os
import logging

# লগিং কনফিগার
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# কনফিগারেশন
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
REQUIRED_GROUPS = ["@EarningMasterbd24"]
ADMIN_USERNAME = "@EarningMaster_help"  # এডমিন ইউজারনেম

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    try:
        # গ্রুপ মেম্বারশিপ চেক
        for group in REQUIRED_GROUPS:
            member = await context.bot.get_chat_member(group, user.id)
            if member.status not in ["member", "administrator", "creator"]:
                await update.message.reply_html(
                    "🔒 <b>অ্যাক্সেস সীমিত!</b>\n\n"
                    "📌 বট ব্যবহার করতে আমাদের গ্রুপে জয়েন করুন:\n"
                    f"➤ {group}\n\n"
                    "✅ জয়েন করে আবার /start টাইপ করুন"
                )
                return

        # মেইন মেনু বাটন
        keyboard = [
            [InlineKeyboardButton("🆘 সাহায্য", callback_data="help")],
            [InlineKeyboardButton("📢 অফিসিয়াল গ্রুপ", url=f"https://t.me/{group[1:]}")]
        ]
        
        await update.message.reply_html(
            f"✨ <b>স্বাগতম, {user.first_name}!</b>\n\n"
            "💼 আমাদের প্রফেশনাল সার্ভিসে আপনাকে স্বাগতম\n\n"
            "🛠️ সাহায্যের জন্য নিচের বাটন ট্যাপ করুন",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("⚠️ সিস্টেমে সমস্যা হচ্ছে। পরে চেষ্টা করুন")

async def help_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # এডমিন কন্টাক্ট ইনফো সহ হেল্প মেসেজ
    help_text = (
        "🆘 <b>সাহায্য কেন্দ্র</b>\n\n"
        "আপনি যদি কোনো সমস্যায় পড়েন:\n\n"
        f"📩 সরাসরি এডমিনের সাথে যোগাযোগ করুন: {ADMIN_USERNAME}\n\n"
        "📌 সাধারণ সমস্যার সমাধান:\n"
        "• বট রেসপন্স দিচ্ছে না? /start ট্রাই করুন\n"
        "• গ্রুপে জয়েন সমস্যা? লিংক আবার চেক করুন\n"
        "• অন্য কোনো সমস্যা? নিচে এডমিন কন্টাক্ট দিন"
    )
    
    await query.edit_message_text(
        text=help_text,
        parse_mode="HTML"
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # কমান্ড হ্যান্ডলার
    app.add_handler(CommandHandler("start", start))
    
    # কলব্যাক হ্যান্ডলার
    app.add_handler(CallbackQueryHandler(help_button, pattern="^help$"))
    
    logger.info("বট সক্রিয় হয়েছে...")
    app.run_polling()

if __name__ == "__main__":
    main()
