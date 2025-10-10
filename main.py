import os
import logging
import urllib.parse  # لاستخدامه في تشفير رابط المشاركة
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

# ------------------- إعدادات زر المشاركة -------------------
# !!! هام: استبدل "b2xobot" باسم المستخدم الفعلي لبوتك (بدون علامة @)
BOT_USERNAME_FOR_SHARE = "b2xobot"  
BOT_LINK_FOR_SHARE = f"https://t.me/{BOT_USERNAME_FOR_SHARE}"

# النص الترويجي الذي يظهر عند مشاركة الرابط (كما ظهر في صورك)
SHARE_TEXT_AR = "تعال نلعـب أكس أو والفائز اله نجووم 🩵⭐️.. ."

# تشفير النص لضمان عمله ضمن رابط URL
ENCODED_SHARE_TEXT = urllib.parse.quote_plus(SHARE_TEXT_AR)

# رابط المشاركة الفعلي الذي سيفتح قائمة اختيار الصديق في تليجرام
SHARE_URL = f"https://t.me/share/url?url={BOT_LINK_FOR_SHARE}&text={ENCODED_SHARE_TEXT}"
# ------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI + Telegram Application
fastapi_app = FastAPI()
application = Application.builder().token(TOKEN).build()


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
            [InlineKeyboardButton("✅ تحققت", callback_data="check_sub")]
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


# ----- الترحيب + إشعار المالك (تم تحديث لوحة المفاتيح هنا) -----
async def send_welcome(update, context, callback=False):
    user = update.effective_user
    user_id = user.id
    username = f"@{user.username}" if user.username else "لا يوجد"
    full_name = " ".join(filter(None, [user.first_name, user.last_name])) or "بدون اسم"

    # --- كود تسجيل المستخدمين ---
    users = set()
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                users = set(line.strip() for line in f if line.strip())
        except Exception as e:
            logger.error(f"قراءة users.txt فشلت: {e}")

    is_new = str(user_id) not in users

    if is_new:
        users.add(str(user_id))
        try:
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                for u in sorted(users):
                    f.write(u + "\n")
        except Exception as e:
            logger.error(f"كتابة users.txt فشلت: {e}")

        count = len(users)
        extra_number = 381
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
    # --- نهاية كود تسجيل المستخدمين ---


    # 1. لوحة المفاتيح المحدثة التي تحتوي على زر المشاركة
    keyboard = [
        [InlineKeyboardButton("🎮 العب وأربـح XO", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton("🔗 مشاركة لصاحبـك", url=SHARE_URL)] 
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if callback:
        await update.callback_query.edit_message_text(
            f"أهلاً {user.first_name or ''} 😂👋\nاضغط الزر للعب XO!",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            f"أهلاً {user.first_name or ''} 👋\nاضغط الزر للعب XO 😂!",
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
    await application.initialize()
    await application.bot.set_webhook(WEBHOOK_URL)
    logger.info(f"✅ Webhook set: {WEBHOOK_URL}")


@fastapi_app.get("/")
async def root():
    return {"status": "running"}
