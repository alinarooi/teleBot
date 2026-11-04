import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatMemberStatus
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "PUT_YOUR_TOKEN_HERE")

# آیدی عددی خودت (ادمین) - از @userinfobot بگیر
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

# آیدی کانال ذخیره‌ی ویدیوها (خصوصی، ربات ادمین باشه) مثل -1001234567890
STORAGE_CHANNEL = int(os.environ.get("STORAGE_CHANNEL", "0"))

# کانال‌هایی که کاربر باید عضو باشه (ربات باید توشون ادمین باشه)
REQUIRED_CHANNELS = ["@eshgh_baza2", "@eshgh_baza3", "@eshgh_baza1"]

# اگه True باشه کاربر نمی‌تونه ویدیو رو فوروارد/ذخیره کنه
PROTECT_CONTENT = False

OK_STATUSES = {
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.OWNER,
}


async def get_missing_channels(bot, user_id: int) -> list[str]:
    missing = []
    for ch in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(ch, user_id)
            if member.status not in OK_STATUSES:
                missing.append(ch)
        except Exception:
            missing.append(ch)
    return missing


def join_keyboard(channels: list[str], payload: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"عضویت در {ch}", url=f"https://t.me/{ch.lstrip('@')}")]
        for ch in channels
    ]
    rows.append([InlineKeyboardButton("✅ عضو شدم", callback_data=f"check:{payload}")])
    return InlineKeyboardMarkup(rows)


async def deliver(bot, chat_id: int, payload: str):
    try:
        await bot.copy_message(
            chat_id=chat_id,
            from_chat_id=STORAGE_CHANNEL,
            message_id=int(payload),
            protect_content=PROTECT_CONTENT,
        )
    except Exception:
        await bot.send_message(chat_id, "❌ این ویدیو پیدا نشد یا حذف شده.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("سلام! برای دریافت ویدیو روی لینک زیر ویدیوها کلیک کن.")
        return

    payload = context.args[0]
    if not payload.isdigit():
        await update.message.reply_text("لینک نامعتبره.")
        return

    missing = await get_missing_channels(context.bot, update.effective_user.id)
    if missing:
        await update.message.reply_text(
            "برای دریافت ویدیو باید در کانال‌های زیر عضو باشی:",
            reply_markup=join_keyboard(missing, payload),
        )
        return

    await deliver(context.bot, update.effective_chat.id, payload)


async def on_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    payload = q.data.split(":", 1)[1]
    missing = await get_missing_channels(context.bot, q.from_user.id)
    if missing:
        await q.answer("هنوز در همه‌ی کانال‌ها عضو نیستی!", show_alert=True)
        return
    await q.answer("عضویتت تأیید شد ✅")
    await deliver(context.bot, q.message.chat_id, payload)


async def admin_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ادمین ویدیو رو به ربات می‌فرسته، ربات توی کانال ذخیره می‌کنه و لینک می‌ده."""
    msg = await context.bot.copy_message(
        chat_id=STORAGE_CHANNEL,
        from_chat_id=update.effective_chat.id,
        message_id=update.message.message_id,
    )
    link = f"https://t.me/{context.bot.username}?start={msg.message_id}"
    await update.message.reply_text(f"✅ ذخیره شد.\nلینک ویدیو:\n{link}")


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_check, pattern=r"^check:\d+$"))
    app.add_handler(
        MessageHandler(
            filters.User(ADMIN_ID) & (filters.VIDEO | filters.Document.VIDEO),
            admin_upload,
        )
    )
    app.run_polling()


if __name__ == "__main__":
    main()
