import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread

# --- تنظیمات اولیه ---
TOKEN = "8983560084:AAHBzgRYHBnUGweunJiywhi7EpfDyL2QvMk" 
ADMIN_ID = 1867576697       
GROUP_CHAT_ID = "@linkdooni_dad"

bot = telebot.TeleBot(TOKEN)
app = Flask('')

# ذخیره اطلاعات کاربران
user_states = {}

# --- بخش Flask ---
@app.route('/')
def home(): return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- کیبوردها ---
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("🛠 ساخت بنر گپ", callback_data="make_banner"),
               types.InlineKeyboardButton("🖼 بنر آماده دارم", callback_data="ready_banner"))
    return markup

def get_admin_keyboard(user_id, mode):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ تایید", callback_data=f"approve_{user_id}_{mode}"),
               types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{user_id}_{mode}"))
    return markup

# --- تابع تولید متن بنر جذاب ---
def create_fancy_banner(name, desc, link):
    separator = "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
    banner = (
        f"{separator}\n"
        f"🌟 **لینکدونی رایگان پدر** 🌟\n"
        f"{separator}\n\n"
        f"🆔 **نام گپ:** `{name}`\n"
        f"📝 **توضیحات:** {desc}\n\n"
        f"🔗 **لینک ورود:**\n{link}\n\n"
        f"{separator}"
    )
    return banner

# --- مدیریت پیام‌ها ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_states[message.from_user.id] = {'step': 'idle', 'data': {}}
    welcome_text = (
        f"👋 سلام **{message.from_user.first_name}** عزیز!\n\n"
        f"🤖 به ربات ثبت لینک در **لینکدونی رایگان پدر** خوش اومدی. 🚀\n\n"
        f"🎯 برای معرفی گپ خودت، یکی از گزینه‌های زیر رو انتخاب کن:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    
    if call.data == "make_banner":
        bot.answer_callback_query(call.id)
        user_states[user_id] = {'step': 'make_name', 'data': {}}
        bot.edit_message_text("🛠 مرحله اول: لطفاً **اسم گپ** خودت رو بنویس: 👇", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    elif call.data == "ready_banner":
        bot.answer_callback_query(call.id)
        user_states[user_id] = {'step': 'ready_upload', 'data': {}}
        bot.edit_message_text("🖼 مرحله اول: لطفاً **عکس، لینک گپ و متن کوتاه** رو در یک پیام (با کپشن) بفرست: 👇", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    # --- بخش تایید ادمین (فقط برای ادمین) ---
    elif call.data.startswith("approve_"):
        # ساختار: approve_{user_id}_{mode}
        parts = call.data.split("_")
        target_user_id = int(parts[1])
        mode = parts[2]
        
        bot.answer_callback_query(call.id, "✅ تایید شد!")
        bot.edit_message_text("✅ درخواست با موفقیت تایید و در گروه منتشر شد! 🎉", call.message.chat.id)

        # حالا بنر رو در گروه منتشر می‌کنیم
        if mode == "make":
            u_data = user_states.get(target_user_id, {}).get('data', {})
            banner_text = create_fancy_banner(u_data.get('name'), u_data.get('desc'), u_data.get('link', 'درخواست ارسال نشده'))
            bot.send_photo(GROUP_CHAT_ID, u_data['photo_id'], caption=banner_text, parse_mode="Markdown")
        else:
            u_data = user_states.get(target_user_id, {}).get('data', {})
            banner_text = create_fancy_banner("گپ ارسالی کاربر", u_data.get('desc', ''), "لینک در کپشن")
            bot.send_photo(GROUP_CHAT_ID, u_data['photo_id'], caption=banner_text, parse_mode="Markdown")

        # اطلاع به کاربر
        try:
            bot.send_message(target_user_id, "🎊 تبریک! گپ شما تایید و در لینکدونی منتشر شد! ✨")
        except: pass

    elif call.data.startswith("reject_"):
        parts = call.data.split("_")
        target_user_id = int(parts[1])
        bot.answer_callback_query(call.id, "❌ رد شد!")
        bot.edit_message_text("❌ درخواست رد شد. 😕", call.message.chat.id)
        try:
            bot.send_message(target_user_id, "⚠️ متاسفانه درخواست شما رد شد. 🚫")
        except: pass

@bot.message_handler(content_types=['text', 'photo'])
def process_steps(message):
    user_id = message.from_user.id
    if user_id not in user_states or user_states[user_id]['step'] == 'idle':
        return

    state = user_states[user_id]['step']
    data = user_states[user_id]['data']

    # مسیر ساخت بنر
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
            # برای ساخت بنر، نیاز به لینک هم داریم (در اینجا از کاربر می‌خوایم بعد از عکس لینک رو بده یا در مرحله قبل)
            # جهت سادگی، فعلاً لینک رو در مرحله توضیحات می‌گیریم یا اینجا می‌پرسیم
            bot.send_message(user_id, "🔗 حالا لطفاً **لینک گپ** رو بفرست: 👇")
            user_states[user_id]['step'] = 'make_link'
        else:
            bot.send_message(user_id, "❌ لطفاً فقط عکس بفرست! 📸")

    elif state == 'make_link':
        data['link'] = message.text
        # ارسال به ادمین برای تایید نهایی
        send_to_admin(user_id, data, "make")
        user_states[user_id] = {'step': 'idle', 'data': {}}
        bot.send_message(user_id, "✅ اطلاعات دریافت شد! منتظر تایید ادمین باش... ⏳")

    # مسیر بنر آماده
    elif state == 'ready_upload':
        if message.content_type == 'photo':
            caption = message.caption if message.caption else ""
            if len(caption) > 3:
                # فرض می‌کنیم کاربر در کپشن: "لینک [space] توضیحات" فرستاده یا فقط لینک. 
                # برای سادگی، کل کپشن رو به عنوان توضیحات و لینک در نظر می‌گیریم یا جدا می‌کنیم.
                # در اینجا کل کپشن رو به عنوان محتوا می‌گیریم.
                data['photo_id'] = message.photo[-1].file_id
                data['desc'] = caption 
                data['link'] = "لینک در کپشن" # یا تلاش برای جدا کردن
                send_to_admin(user_id, data, "ready")
                user_states[user_id] = {'step': 'idle', 'data': {}}
                bot.send_message(user_id, "✅ اطلاعات دریافت شد! منتظر تایید ادمین باش... ⏳")
            else:
                bot.send_message(user_id, "❌ لطفاً عکس رو همراه با **لینک و متن** در کپشن بفرست! ✍️")

def send_to_admin(user_id, data, mode):
    admin_msg = f"🔔 **درخواست جدید ({mode})**\n\n"
    admin_msg += f"👤 از طرف: {user_id}\n"
    
    if mode == "make":
        admin_msg += f"🏷 نام: {data.get('name')}\n📝 توضیح: {data.get('desc')}\n🔗 لینک: {data.get('link')}"
        bot.send_photo(GROUP_CHAT_ID, data['photo_id'], caption=admin_msg, reply_markup=get_admin_keyboard(user_id, "make"), parse_mode="Markdown")
    else:
        admin_msg += f"📝 محتوا:\n{data.get('desc')}"
        bot.send_photo(GROUP_CHAT_ID, data['photo_id'], caption=admin_msg, reply_markup=get_admin_keyboard(user_id, "ready"), parse_mode="Markdown")

if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    bot.infinity_polling(skip_pending=True)
