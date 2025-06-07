import requests
import time
import os
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from keep_alive import keep_alive

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"

bot = Bot(token=TELEGRAM_TOKEN)
last_prediction = None
history = []
last_period = None

def fetch_results():
    try:
        res = requests.get(API_URL, timeout=10)
        data = res.json()
        entries = data.get("data", {}).get("list", [])
        result_list = []
        for item in entries:
            period = item.get("issue")
            code = item.get("code", "").lower()
            if 'r' in code and 'g' in code:
                color = "violet"
            elif 'r' in code:
                color = "red"
            elif 'g' in code:
                color = "green"
            else:
                color = "unknown"
            result_list.append((period, color))
        return result_list
    except Exception as e:
        print("Fetch error:", e)
        return []

def predict_next_color(history):
    reds = history.count("red")
    greens = history.count("green")
    if history and history[-1] == "violet":
        return "red" if reds < greens else "green"
    return "green" if reds > greens else "red"

def start_command(update: Update, context: CallbackContext):
    context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    update.message.reply_text("🔄 Please wait... fetching latest prediction 🔍\nYou will receive the next prediction shortly.")

def status_command(update: Update, context: CallbackContext):
    status = (
        "📊 Prediction Status:\n"
        f"Last Period: {last_period}\n"
        f"Last Prediction: {last_prediction}\n"
        f"Recent History: {', '.join(history[:10])}"
    )
    update.message.reply_text(status)

def help_command(update: Update, context: CallbackContext):
    help_text = (
        "🤖 Available Commands:\n"
        "/start - Start the bot\n"
        "/status - View current prediction status\n"
        "/help - Show this help message"
    )
    update.message.reply_text(help_text)

def run_bot():
    global last_period, last_prediction, history

    keep_alive()
    print("✅ Bot is running and polling...")
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(CommandHandler("status", status_command))
    dp.add_handler(CommandHandler("help", help_command))

    updater.start_polling()

    while True:
        results = fetch_results()
        if not results:
            time.sleep(10)
            continue

        period, color = results[0]

        if period != last_period:
            history.insert(0, color)
            history = history[:20]
            prediction = predict_next_color(history)
            last_prediction = prediction

            message = (
                f"🎯 *Next Prediction:* `{prediction.upper()}`\n"
                f"🕓 *Period:* {int(period) + 1}\n"
                f"✅ *Last Result:* `{color.upper()}`\n"
                f"📊 *History:* {', '.join(history[:10])}"
            )

            try:
                print("Sending to Telegram:", message)
                bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')
            except Exception as e:
                print("Telegram error:", e)

            last_period = period

        time.sleep(10)

if __name__ == '__main__':
    run_bot()