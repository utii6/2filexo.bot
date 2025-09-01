from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import telegram, json

TOKEN = "7955735266:AAGSqtTDWtCbnjYVZIScdKqIQkLFnEiZHJY"
CHANNEL = "@qd3qd"
WEBAPP_URL = "https://x-o-bot.onrender.com"

# التحقق من الاشتراك
async def is_subscribed(bot: telegram.Bot, user_id):
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["creator", "administrator", "member"]
    except:
        return False

# حفظ النتائج
def save_score(user_id, name, result):
    try:
        with open("scores.json", "r") as f:
            scores = json.load(f)
    except:
        scores = {}

    if user_id not in scores:
        scores[user_id] = {"name": name, "wins": 0, "losses": 0, "draws": 0}

    if result == "win":
        scores[user_id]["wins"] += 1
    elif result == "loss":
        scores[user_id]["losses"] += 1
    else:
        scores[user_id]["draws"] += 1

    with open("scores.json", "w") as f:
        json.dump(scores, f)

# رسالة الترحيب + زر اللعبة
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if await is_subscribed(context.bot, user_id):
        keyboard = [
            [InlineKeyboardButton("🎮 العب XO", web_app={"url": WEBAPP_URL})]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"أهلاً بك {update.message.from_user.first_name} 😂👋\n دز البوت لضلعك لو للبتيته مالتكXO!",
            reply_markup=reply_markup
        )
    else:
        keyboard = [
            [InlineKeyboardButton("مَـدار💎", url=f"https://t.me/+NeIEOgnefpk1MWIy")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "💁يالطيـب اشترك وارسل /start :.",
            reply_markup=reply_markup
        )

# استقبال بيانات اللعبة
async def handle_webapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.message.web_app_data.data  # "win", "loss", "draw"
    user = update.message.from_user
    save_score(user.id, user.first_name, data)
    await update.message.reply_text(f"😂📢 النتيجة تم تسجيلها: {data}")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp))

print("🤖 Bot running...")
app.run_polling()
