import os
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

# --------- الإعدادات ----------
TOKEN = "7955735266:AAGSqtTDWtCbnjYVZIScdKqIQkLFnEiZHJY"
ADMIN_ID = 5581457665
WEBAPP_URL = "https://x_o.bot.onrender.com"   # رابط لعبتك
USERS_FILE = "users.txt"
CHANNEL_USERNAME = "@qd3Qd"  # قناة الاشتراك الإجباري
# ------------------------------

# تطبيق FastAPI
fastapi_app = FastAPI()

# تطبيق بوت تيليجرام
telegram_app = Application.builder().token(TOKEN).build()


# فحص الاشتراك
async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False


# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return

    user_id = user.id
    username = f"@{user.username}" if user.username else "لا يوجد"
    full_name = " ".join(filter(None, [user.first_name, user.last_name])) or "بدون اسم"

    # تحقق من الاشتراك
    is_subscribed = await check_subscription(user_id, context)
    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton("📢مَـداار", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
            [InlineKeyboardButton("✅ تم الاشتراك يقلبي", callback_data="check_sub")]
        ]
        await update.message.reply_text(
            "🚨اشتـرك حبيبي وارسل /start:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # اقرأ المستخدمين
    users = set()
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = set(line.strip() for line in f if line.strip())

    is_new = str(user_id) not in users

    if is_new:
        users.add(str(user_id))
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            for u in sorted(users):
                f.write(u + "\n")

        count = len(users)
        admin_text = (
            "دخول نفـرر جديد لبوتك 😎\n"
            "-----------------------\n"
            f"• الاسم😂: {full_name}\n"
            f"• معرف💁: {username}\n"
            f"• الايدي🆔: {user_id}\n"
            "-----------------------\n"
            f"• عدد مشتركينك الابطال:😂 {count}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text)

    # زر اللعب
    keyboard = [[InlineKeyboardButton("🎮 العب وأربـح XO", web_app=WebAppInfo(url=WEBAPP_URL))]]
    await update.message.reply_text(
        f"أهلاً {user.first_name or ''} 😂👋\nاضغط الزر للعب XO!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# إضافة Handlers
telegram_app.add_handler(CommandHandler("start", start))


# Webhook endpoint
WEBHOOK_PATH = f"/webhook/{TOKEN}"


@fastapi_app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    update = Update.de_json(await request.json(), telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}


# تشغيل عند بدء السيرفر
@fastapi_app.on_event("startup")
async def on_startup():
    webhook_url = f"https://twofilexo-bot.onrender.com{WEBHOOK_PATH}"
    await telegram_app.bot.set_webhook(webhook_url)
    asyncio.create_task(telegram_app.start())
