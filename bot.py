import os
from fastapi import FastAPI, Request
from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
)
from telegram.ext import (
    Application, CommandHandler, ContextTypes
)
import asyncio

# ------ عدّل هذه القيم ----------
TOKEN = "7955735266:AAGSqtTDWtCbnjYVZIScdKqIQkLFnEiZHJY"
ADMIN_ID = 5581457665                       # آي دي المالك
WEBAPP_URL = "https://x_o.bot.onrender.com"   # رابط لعبتك على Render
CHANNEL_USERNAME = "@qd3QD"           # قناة الاشتراك الإجباري
USERS_FILE = "users.txt"
WEBHOOK_PATH = f"/webhook/{TOKEN}"
# --------------------------------

app = FastAPI()
telegram_app = Application.builder().token(TOKEN).build()


# ======= دالة الاشتراك الإجباري =======
async def check_subscription(user_id, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
    except Exception as e:
        print("خطأ فحص الاشتراك:", e)
    return False


# ======= دالة /start =======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return

    user_id = user.id
    username = f"@{user.username}" if user.username else "لا يوجد"
    full_name = " ".join(filter(None, [user.first_name, user.last_name])) or "بدون اسم"

    # --- تحقق من الاشتراك
    is_subscribed = await check_subscription(user_id, context)
    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton("📢مَـداار ", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
            [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub")]
        ]
        await update.message.reply_text(
            "🚨اشتـرك حبيبي وارسل /start 🎮",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # --- قراءة المستخدمين
    users = set()
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = set(line.strip() for line in f if line.strip())

    is_new = str(user_id) not in users

    # --- إذا جديد -> سجل وأرسل إشعار للمالك
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

    # --- زر اللعبة
    keyboard = [
        [InlineKeyboardButton("🎮  العب وفوز XO", web_app=WebAppInfo(url=WEBAPP_URL))]
    ]
    await update.message.reply_text(
        f"أهلاً {user.first_name or ''} 😂👋\nاضغط الزر للعب XO!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ======= هندلر تحقق من الاشتراك =======
from telegram.ext import CallbackQueryHandler
async def check_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    is_subscribed = await check_subscription(query.from_user.id, context)
    if is_subscribed:
        await start(update, context)
    else:
        await query.edit_message_text("🚨يلا حبيبي اشترك وارسل /start 📢")


telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CallbackQueryHandler(check_sub, pattern="check_sub"))


# ======= FastAPI Webhook =======
@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    asyncio.create_task(telegram_app.process_update(update))
    return {"ok": True}


@app.on_event("startup")
async def startup_event():
    webhook_url = f"https://twofilexo-bot.onrender.com{WEBHOOK_PATH}"
    await telegram_app.bot.set_webhook(webhook_url)
    print("🚀 Webhook set:", webhook_url)
