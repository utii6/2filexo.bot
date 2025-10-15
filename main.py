import os
import logging
from fastapi import FastAPI, Request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import Forbidden

# ------------------- إعدادات البوت -------------------
TOKEN = "7955735266:AAFBGu_RXstAQ-X9uhTzLKF6YfKc53nl8I8"
ADMIN_ID = 5581457665
WEBAPP_URL = "https://x-o-bot.onrender.com"
USERS_FILE = "users.txt"
CHANNEL_USERNAME = "Qd3Qd"
CHANNEL_LINK = "https://t.me/qd3qd"
PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"https://twofilexo-bot.onrender.com{WEBHOOK_PATH}"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

fastapi_app = FastAPI()
application = Application.builder().token(TOKEN).build()

# مجموعة المستخدمين المسجلين
registered_users = set()

# ----- دالة التحقق من الاشتراك -----
async def check_subscription(user_id, context):
    try:
        member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        if member.status in ["left", "kicked"]:
            return False
    except Forbidden:
        return False
    except Exception as e:
        logger.error(f"خطأ في التحقق من الاشتراك: {e}")
        return False
    return True


# ----- رسالة البداية -----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return

    user_id = user.id
    is_subscribed = await check_subscription(user_id, context)

    if not is_subscribed:
        buttons = [
            [InlineKeyboardButton(f"📢 مَـدار @{CHANNEL_USERNAME}", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ أشتركـت", callback_data="check_sub")]
        ]
        await update.message.reply_text(
            "⚠️ ، اشتـرك حبيبي وأرسل /start:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    await send_welcome(update, context)


# ----- التحقق بعد الضغط -----
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "check_sub":
        user_id = query.from_user.id
        is_subscribed = await check_subscription(user_id, context)
        if is_subscribed:
            await send_welcome(update, context, callback=True)
        else:
            await query.edit_message_text("❌  .اشتـرك حبيبي اشتـرك.")


# ----- الترحيب + إشعار المالك -----
async def send_welcome(update, context, callback=False):
    global registered_users

    user = update.effective_user
    user_id = user.id
    username = f"@{user.username}" if user.username else "لا يوجد"
    full_name = " ".join(filter(None, [user.first_name, user.last_name])) or "بدون اسم"

    # تحقق من المستخدم الجديد
    if str(user_id) not in registered_users:
        registered_users.add(str(user_id))
        try:
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                for u in sorted(registered_users):
                    f.write(u + "\n")
        except Exception as e:
            logger.error(f"كتابة users.txt فشلت: {e}")

        count = len(registered_users)
        extra_number = 23980
        admin_text = (
            "دخول نفـرر جديد لبوتك 😎\n"
            "-----------------------\n"
            f"• الاسم😂: {full_name}\n"
            f"• معرف💁: {username}\n"
            f"• الايدي🆔: {user_id}\n"
            "-----------------------\n"
            f"• عدد مشتركينك الابطال:😂 {extra_number + count}"
        )
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text)
        except Exception as e:
            logger.error(f"فشل إرسال إشعار للمالك: {e}")

    # لوحة المفاتيح
    keyboard = [
        [InlineKeyboardButton("🎮 العب وأربـح XO", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton("📤 العـب مع صاحبـك", url="https://t.me/share/url?url=@b2xobot")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if callback:
        await update.callback_query.edit_message_text(
            f"أهلاً {user.first_name or ''} 👋\nاضغط الزر للعب XO!",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            f"أهلاً {user.first_name or ''} 👋\nاضغط الزر للعب XO!",
            reply_markup=reply_markup
        )


# ----- Handlers -----
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_callback))


# ----- FastAPI Webhook -----
@fastapi_app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.initialize()
    await application.process_update(update)
    return {"ok": True}


@fastapi_app.on_event("startup")
async def on_startup():
    global registered_users
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            registered_users = set(line.strip() for line in f if line.strip())
    await application.initialize()
    await application.bot.set_webhook(WEBHOOK_URL)
    logger.info(f"✅ Webhook set: {WEBHOOK_URL}")
    logger.info(f"📂 تم تحميل {len(registered_users)} مستخدم من الملف")


@fastapi_app.get("/")
async def root():
    return {"status": "running"}
