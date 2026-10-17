import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread

# --- تنظیمات اولیه ---
TOKEN = "8983560084:AAHBzgRYHBnUGweunJiywhi7EpfDyL2QvMk"  # <--- حتماً توکن خودت رو اینجا بذار
ADMIN_ID = 1867576697       # آیدی عددی خودت برای تایید لینک‌ها
GROUP_CHAT_ID = "@linkdooni_dad"

bot = telebot.TeleBot(TOKEN)

# ذخیره وضعیت کاربران (در حافظه موقت)
# ساختار: {user_id: {'step': 'state', 'data': {}}}
user_states = {}

# --- بخش Flask برای رندر ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- کیبوردها ---
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_make = types.InlineKeyboardButton("🛠 ساخت بنر گپ", callback_data="make_banner")
    btn_ready = types.InlineKeyboardButton("🖼 بنر آماده دارم", callback_data="ready_banner")
    markup.add(btn_make, btn_ready)
    return markup

def get_admin_keyboard(user_id, info_type):
    markup = types.InlineKeyboardMarkup()
    btn_approve = types.InlineKeyboardButton("✅ تایید", callback_data=f"approve_{user_id}_{info_type}")
    btn_reject = types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{user_id}_{info_type}")
    markup.add(btn_approve, btn_reject)
    return markup

# --- مدیریت دستورات ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_states[message.from_user.id] = {'step': 'idle', 'data': {}}
    welcome_text = (
        f"👋 سلام **{message.from_user.first_name}** عزیز!\n\n"
        f"🤖 به ربات ثبت لینک در **لینکدونی رایگان پدر** خوش اومدی. 🚀\n\n"
        f"🎯 برای ثبت و معرفی گپ خودت، لطفاً یکی از گزینه‌های زیر رو انتخاب کن:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    
    # شروع فرآیند ساخت بنر
    if call.data == "make_banner":
        bot.answer_callback_query(call.id)
        user_states[user_id] = {'step': 'make_name', 'data': {}}
        bot.edit_message_text("🛠 مرحله اول: لطفاً **اسم گپ** خودت رو بنویس: 👇", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        bot.send_message(call.message.chat.id, "📝")

    # شروع فرآیند بنر آماده
    elif call.data == "ready_banner":
        bot.answer_callback_query(call.id)
        user_states[user_id] = {'step': 'ready_upload', 'data': {}}
        bot.edit_message_text("🖼 مرحله اول: لطفاً **عکس، لینک گپ و متن کوتاه** رو در یک پیام برای من بفرست: 👇", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    # تایید ادمین (تایید کردن)
    elif call.data.startswith("approve_"):
        _, target_user_id, info_type = call.data.split("_")
        bot.answer_callback_query(call.id, "✅ تایید شد!")
        bot.edit_message_text("✅ این لینک با موفقیت تایید و در لینکدونی ثبت شد! 🎉", call.message.chat.id)
        # اطلاع به کاربر
        try:
            bot.send_message(target_user_id, "🎊 تبریک! گپ شما توسط ادمین تایید و در لینکدونی ثبت شد. موفق باشید! ✨")
        except: pass

    # رد کردن توسط ادمین
    elif call.data.startswith("reject_"):
        _, target_user_id, info_type = call.data.split("_")
        bot.answer_callback_query(call.id, "❌ رد شد!")
        bot.edit_message_text("❌ این درخواست رد شد. 😕", call.message.chat.id)
        # اطلاع به کاربر
        try:
            bot.send_message(target_user_id, "⚠️ متاسفانه درخواست ثبت لینک شما رد شد. دوباره تلاش کنید. 🚫")
        except: pass

# --- مدیریت دریافت پیام‌ها و مراحل (State Machine) ---

@bot.message_handler(content_types=['text', 'photo'])
def handle_messages(message):
    user_id = message.from_user.id
    
    # اگر کاربر در حال طی کردن مراحل نیست، کاری نکن
    if user_id not in user_states or user_states[user_id]['step'] == 'idle':
        return

    state = user_states[user_id]['step']
    data = user_states[user_id]['data']

    # --- مسیر ساخت بنر (Make Banner) ---
    if state == 'make_name':
        data['name'] = message.text
        user_states[user_id]['step'] = 'make_desc'
        bot.send_message(user_id, "📝 عالی! حالا **توضیحات کوتاه** گپ رو بفرست: 👇", parse_mode="Markdown")

    elif state == 'make_desc':
        data['desc'] = message.text
        user_states[user_id]['step'] = 'make_photo'
        bot.send_message(user_id, "📸 حالا **عکس گپ** رو برام بفرست: 👇", parse_mode="Markdown")

    elif state == 'make_photo':
        if message.content_type == 'photo':
            data['photo_id'] = message.photo[-1].file_id
            # پایان مراحل ساخت بنر - ارسال برای ادمین
            send_to_admin_review(user_id, data, "ساخت بنر")
            user_states[user_id] = {'step': 'idle', 'data': {}}
            bot.send_message(user_id, "✅ اطلاعاتت دریافت شد! منتظر تایید ادمین باش... ⏳")
        else:
            bot.send_message(user_id, "❌ لطفاً فقط **عکس** بفرست! 📸")

    # --- مسیر بنر آماده (Ready Banner) ---
    elif state == 'ready_upload':
        if message.content_type == 'photo':
            # فرض می‌کنیم کاربر عکس، متن و لینک رو با هم فرستاده (در یک پیام)
            # در تلگرام وقتی عکس + متن میاد، caption حاوی متن هست
            caption = message.caption if message.caption else ""
            if len(caption) > 3: # چک کردن اینکه متن خالی نباشه
                data['photo_id'] = message.photo[-1].file_id
                data['content'] = caption # متن و لینک در کپشن هست
                send_to_admin_review(user_id, data, "بنر آماده")
                user_states[user_id] = {'step': 'idle', 'data': {}}
                bot.send_message(user_id, "✅ اطلاعاتت دریافت شد! منتظر تایید ادمین باش... ⏳")
            else:
                bot.send_message(user_id, "❌ لطفاً عکس رو همراه با **لینک و متن** در کپشن بفرست! ✍️")
        else:
            bot.send_message(user_id, "❌ لطفاً فقط **عکس** (همراه با متن/لینک در کپشن) بفرست! 📸")

# --- تابع کمکی برای ارسال به ادمین ---
def send_to_admin_review(user_id, data, info_type):
    admin_msg = f"🔔 **درخواست جدید: {info_type}**\n\n"
    admin_msg += f"👤 از طرف: {user_id}\n"
    
    if info_type == "ساخت بنر":
        admin_msg += f"🏷 نام گپ: {data['name']}\n"
        admin_msg += f"📝 توضیحات: {data['desc']}\n"
        bot.send_photo(GROUP_CHAT_ID, data['photo_id'], caption=admin_msg, reply_markup=get_admin_keyboard(user_id, "make"), parse_mode="Markdown")
    
    else: # بنر آماده
        admin_msg += f"🔗 محتوا:\n{data['content']}\n"
        bot.send_photo(GROUP_CHAT_ID, data['photo_id'], caption=admin_msg, reply_markup=get_admin_keyboard(user_id, "ready"), parse_mode="Markdown")

# --- اجرا ---
if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    print("Bot is polling...")
    bot.infinity_polling(skip_pending=True)
