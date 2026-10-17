import os
import telebot
from flask import Flask
from threading import Thread

# دریافت متغیرهای محیطی
TOKEN = os.environ.get('BOT_TOKEN', '8983560084:AAHBzgRYHBnUGweunJiywhi7EpfDyL2QvMk')
GROUP_CHAT_ID = os.environ.get('GROUP_CHAT_ID', '@linkdooni_dad')
ADMIN_CHAT_ID = int(os.environ.get('ADMIN_CHAT_ID', '1867576697'))

bot = telebot.TeleBot(TOKEN)

# ساخت یک وب‌سرور کوچک برای راضی نگه داشتن رندر (Port Binding)
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# هندلر شروع و پیام‌ها
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام برهان عزیز! ربات لینکدونی با موفقیت روی فضای ابری روشن شد. 🚀")

@bot.message_handler(func=lambda message: True)
def handle_all(message):
    pass

if __name__ == "__main__":
    # اجرای وب‌سرور در یک ترد (Thread) جداگانه
    t = Thread(target=run_web)
    t.start()
    
    # اجرای ربات تلگرام
    print("Bot is polling...")
    bot.infinity_polling()
