import os
import telebot
from flask import Flask
from threading import Thread

# دریافت متغیرهای محیطی
TOKEN = os.environ.get('BOT_TOKEN', '*******')
GROUP_CHAT_ID = os.environ.get('GROUP_CHAT_ID', '@linkdooni_dad')

bot = telebot.TeleBot(TOKEN)

# راه‌اندازی وب‌سرور Flask برای پاسخ به پورت رندر
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام برهان عزیز! ربات لینکدونی با موفقیت روی فضای ابری روشن شد. 🚀")

@bot.message_handler(func=lambda message: True)
def handle_all(message):
    pass

if __name__ == "__main__":
    # اول وب‌سرور رو توی ترد جداگانه استارت می‌کنیم تا پورت رندر فوری باز بشه
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # بعد ربات تلگرام رو روشن می‌کنیم
    print("Bot is polling...")
    bot.infinity_polling(skip_pending=True)
