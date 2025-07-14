from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# আপনার বট শুরু
@Client.on_message(filters.command("start"))
async def start(client, message: Message):
    user = message.from_user
    name = user.first_name

    await message.reply_text(
        f"👋 হ্যালো {name}!\n\n"
        "🔥 এটি হলো *Earning Master* টেলিগ্রাম মিনি অ্যাপ। আপনি রেফার, বিজ্ঞাপন দেখা, "
        "ব্যালেন্স চেক ও উইথড্র করতে পারবেন।\n\n"
        "👇 নিচের বাটনে ক্লিক করে মিনি অ্যাপ চালু করুন:",
        reply_markup=InlineKeyboardMarkup(
            [[
                InlineKeyboardButton(
                    text="🚀 মিনি অ্যাপ খুলুন",
                    web_app={"url": "https://r2rbdbot.blogspot.com/?m=1"}
                )
            ]]
        ),
        parse_mode="markdown"
    )
