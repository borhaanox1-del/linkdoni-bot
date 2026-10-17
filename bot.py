import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread

# --- تنظیمات اولیه ---
TOKEN = "8983560084:AAHBzgRYHBnUGweunJiywhi7EpfDyL2QvMk"  # <--- حتماً توکن خودت رو اینجا بذار
GROUP_CHAT_ID = os.environ.get('GROUP_CHAT_ID', '@linkdooni_dad')

bot = telebot.TeleBot(TOKEN)

# --- بخش Flask برای رندر ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- منطق ربات (Logic) ---

# دکمه‌های اصلی در شروع کار
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_make = types.InlineKeyboardButton("🛠 ساخت بنر", callback_data="make_banner")
    btn_ready = types.InlineKeyboardButton("🖼 بنر آماده دارم", callback_data="ready_banner")
    markup.add(btn_make, btn_ready)
    return markup

# دستور استارت
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        f"سلام {message.from_user.first_name} عزیز!\n\n"
        "به ربات ثبت لینک تو لینکدونی خوش اومدی. برای ثبت کانال یا گروهت از گزینه‌های زیر استفاده کن:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_keyboard())

# مدیریت کلیک روی دکمه‌ها (Callback Query)
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "make_banner":
        bot.answer_callback_query(call.id)
        bot.edit_message_text("شما گزینه 'ساخت بنر' را انتخاب کردید. در مراحل بعدی از شما اطلاعات خواسته می‌شود.", 
                              call.message.chat.id, call.message.message_id)
        # در مراحل بعد، اینجا شروع می‌کنیم به گرفتن اسم کانال
        bot.send_message(call.message.chat.id, "لطفاً ابتدا **اسم کانال یا گروه** خود را بنویسید:")
        
    elif call.data == "ready_banner":
        bot.answer_callback_query(call.id)
        bot.edit_message_text("شما گزینه 'بنر آماده دارم' را انتخاب کردید.", 
                              call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "لطفاً لینک (کانال/گروه) خود را به همراه عکس و متن کوتاه در یک پیام ارسال کنید:")

# اجرای همزمان Flask و Bot
if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    print("Bot is polling...")
    bot.infinity_polling(skip_pending=True)
