import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread

# --- تنظیمات حیاتی ---
TOKEN = "8983560084:AAHBzgRYHBnUGweunJiywhi7EpfDyL2QvMk" 
ADMIN_ID = 1867576697       # درخواست‌ها فقط برای این آیدی می‌آید
GROUP_CHAT_ID = "@linkdooni_dad" # بنر نهایی در اینجا منتشر می‌شود

bot = telebot.TeleBot(TOKEN)

# ذخیره داده‌های موقت کاربران
user_data_store = {} # {user_id: {'name':..., 'desc':..., 'link':..., 'photo_id':...}}
user_steps = {}      # {user_id: 'step_name'}

app = Flask('')

@app.route('/')
def home(): return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- قالب‌بندی بنر (Template) ---
def generate_fancy_text(name, desc, link):
    sep = "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
    return (
        f"{sep}\n"
        f"🌟 **لینکدونی رایگان پدر** 🌟\n"
        f"{sep}\n\n"
        f"🆔 **نام گپ:** `{name}`\n"
        f"📝 **توضیحات:** {desc}\n\n"
        f"🔗 **لینک ورود:**\n{link}\n\n"
        f"{sep}"
    )

# --- کیبوردها ---
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("🛠 ساخت بنر گپ", callback_data="start_make"),
               types.InlineKeyboardButton("🖼 بنر آماده دارم", callback_data="start_ready"))
    return markup

def get_admin_keyboard(target_user_id, mode):
    markup = types.InlineKeyboardMarkup()
    # ساخت دکمه‌ها با فرمت مشخص برای پردازش دقیق
    markup.add(types.InlineKeyboardButton("✅ تایید", callback_data=f"adm_ok_{target_user_id}_{mode}"),
               types.InlineKeyboardButton("❌ رد", callback_data=f"adm_no_{target_user_id}_{mode}"))
    return markup

# --- مدیریت پیام‌ها و مراحل ---

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_steps[user_id] = 'idle'
    user_data_store[user_id] = {}
    welcome = f"👋 سلام **{message.from_user.first_name}** عزیز!\n\n🤖 برای ثبت گپ خودت یکی از گزینه‌های زیر رو انتخاب کن:"
    bot.send_message(user_id, welcome, reply_markup=get_main_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id

    # ۱. شروع ساخت بنر (گام به گام)
    if call.data == "start_make":
        bot.answer_callback_query(call.id)
        user_steps[user_id] = 'make_name'
        bot.edit_message_text("🛠 مرحله اول: لطفاً **اسم گپ** خودت رو بنویس: 👇", user_id, call.message.message_id, parse_mode="Markdown")

    elif call.data == "start_ready":
        bot.answer_callback_query(call.id)
        user_steps[user_id] = 'ready_upload'
        bot.edit_message_text("🖼 مرحله اول: لطفاً **عکس، لینک و متن** رو در قالب یک پیام (کپشن عکس) بفرست: 👇", user_id, call.message.message_id, parse_mode="Markdown")

    # ۲. مدیریت تایید/رد توسط ادمین (فقط ادمین می‌تواند این دکمه‌ها را بزند)
    elif call.data.startswith("adm_ok_"):
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ شما دسترسی ندارید!")
            return
        
        parts = call.data.split("_")
        target_uid = int(parts[2])
        mode = parts[3]
        
        bot.answer_callback_query(call.id, "✅ تایید شد!")
        bot.edit_message_text("✅ درخواست تایید و در گروه منتشر شد! 🎉", user_id, call.message.message_id)

        # انتشار بنر نهایی در گروه
        data = user_data_store.get(target_uid, {})
        if mode == "make":
            text = generate_fancy_text(data.get('name', 'بدون نام'), data.get('desc', '-'), data.get('link', '-'))
            bot.send_photo(GROUP_CHAT_ID, data.get('photo_id'), caption=text, parse_mode="Markdown")
        else:
            text = generate_fancy_text("گپ ارسالی کاربر", data.get('desc', '-'), "لینک در کپشن")
            bot.send_photo(GROUP_CHAT_ID, data.get('photo_id'), caption=text, parse_mode="Markdown")

        # خبر دادن به کاربر
        try:
            bot.send_message(target_uid, "🎊 تبریک! گپ شما تایید و در لینکدونی منتشر شد! ✨")
        except: pass

    elif call.data.startswith("adm_no_"):
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ شما دسترسی ندارید!")
            return
        
        parts = call.data.split("_")
        target_uid = int(parts[2])
        mode = parts[3]
        
        bot.answer_callback_query(call.id, "❌ رد شد!")
        bot.edit_message_text("❌ درخواست رد شد. 😕", user_id, call.message.message_id)
        try:
            bot.send_message(target_uid, "⚠️ متاسفانه درخواست شما رد شد. 🚫")
        except: pass

# --- دریافت پیام و حرکت در مراحل ---

@bot.message_handler(content_types=['text', 'photo'])
def process_all_messages(message):
    user_id = message.from_user.id
    if user_id not in user_steps or user_steps[user_id] == 'idle': return

    step = user_steps[user_id]
    if user_id not in user_data_store: user_data_store[user_id] = {}
    data = user_data_store[user_id]

    # مسیر ساخت بنر
    if step == 'make_name':
        data['name'] = message.text
        user_steps[user_id] = 'make_desc'
        bot.send_message(user_id, "📝 عالی! حالا **توضیحات کوتاه** گپ رو بفرست: 👇", parse_mode="Markdown")

    elif step == 'make_desc':
        data['desc'] = message.text
        user_steps[user_id] = 'make_photo'
        bot.send_message(user_id, "📸 حالا **عکس گپ** رو برام بفرست: 👇", parse_mode="Markdown")

    elif step == 'make_photo':
        if message.content_type == 'photo':
            data['photo_id'] = message.photo[-1].file_id
            user_steps[user_id] = 'make_link'
            bot.send_message(user_id, "🔗 حالا آخرین مرحله: **لینک گپ** رو بفرست: 👇", parse_mode="Markdown")
        else:
            bot.send_message(user_id, "❌ لطفاً فقط عکس بفرست! 📸")

    elif step == 'make_link':
        data['link'] = message.text
        # ارسال درخواست به ادمین (در چت خصوصی ادمین)
        send_to_admin_private(user_id, data, "make")
        user_steps[user_id] = 'idle'
        bot.send_message(user_id, "✅ اطلاعات دریافت شد! منتظر تایید ادمین باش... ⏳")

    # مسیر بنر آماده (عکس + کپشن)
    elif step == 'ready_upload':
        if message.content_type == 'photo':
            caption = message.caption if message.caption else ""
            if len(caption) > 3:
                data['photo_id'] = message.photo[-1].file_id
                data['desc'] = caption
                send_to_admin_private(user_id, data, "ready")
                user_steps[user_id] = 'idle'
                bot.send_message(user_id, "✅ اطلاعات دریافت شد! منتظر تایید ادمین باش... ⏳")
            else:
                bot.send_message(user_id, "❌ عکس رو با متن و لینک در کپشن بفرست! ✍️")

def send_to_admin_private(user_id, data, mode):
    """ارسال درخواست تایید به صورت خصوصی برای ادمین"""
    admin_msg = f"🔔 **درخواست جدید ({mode})**\n\n"
    admin_msg += f"👤 از طرف: {user_id}\n"
    
    if mode == "make":
        admin_msg += f"🏷 نام: {data.get('name')}\n📝 توضیح: {data.get('desc')}\n🔗 لینک: {data.get('link')}"
        bot.send_photo(ADMIN_ID, data.get('photo_id'), caption=admin_msg, reply_markup=get_admin_keyboard(user_id, "make"), parse_mode="Markdown")
    else:
        admin_msg += f"📝 محتوا (کپشن):\n{data.get('desc')}"
        bot.send_photo(ADMIN_ID, data.get('photo_id'), caption=admin_msg, reply_markup=get_admin_keyboard(user_id, "ready"), parse_mode="Markdown")

if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    bot.infinity_polling(skip_pending=True)
