import os
import telebot
from telebot import types

# توکن و مشخصات شما
TOKEN = os.environ.get('BOT_TOKEN', '8983560084:AAHBzgRYHBnUGweunJiywhi7EpfDyL2QvMk')
GROUP_CHAT_ID = os.environ.get('GROUP_CHAT_ID', '@linkdooni_dad')
ADMIN_CHAT_ID = int(os.environ.get('ADMIN_CHAT_ID', '1867576697'))

bot = telebot.TeleBot(TOKEN)

user_data = {}
pending_posts = {}

class RegistrationState:
    NAME = 0
    DESC = 1
    LINK = 2

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("📌 ثبت کانال / گروه جدید")
    bot.reply_to(message, "سلام برهان عزیز! به ربات مدیریت لینکدونی خوش اومدی. برای ثبت کانال یا گروهت روی دکمه زیر بزن:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📌 ثبت کانال / گروه جدید")
def start_registration(message):
    bot.send_message(message.chat.id, "لطفاً نام کانال یا گروهت رو بفرست (مثلاً: آموزش پایتون):", reply_markup=types.ReplyKeyboardRemove())
    user_data[message.from_user.id] = {'step': RegistrationState.NAME}

@bot.message_handler(func=lambda msg: user_data.get(msg.from_user.id, {}).get('step') == RegistrationState.NAME)
def get_name(message):
    user_data[message.from_user.id]['name'] = message.text
    user_data[message.from_user.id]['step'] = RegistrationState.DESC
    bot.send_message(message.chat.id, "یک توضیحات کوتاه و جذاب (حداکثر ۱-۲ خط) درباره کانالت بفرست:")

@bot.message_handler(func=lambda msg: user_data.get(msg.from_user.id, {}).get('step') == RegistrationState.DESC)
def get_desc(message):
    user_data[message.from_user.id]['desc'] = message.text
    user_data[message.from_user.id]['step'] = RegistrationState.LINK
    bot.send_message(message.chat.id, "لینک دعوت کانال یا گروهت رو بفرست (مثلاً https://t.me/...):")

@bot.message_handler(func=lambda msg: user_data.get(msg.from_user.id, {}).get('step') == RegistrationState.LINK)
def get_link(message):
    user_id = message.from_user.id
    data = user_data[user_id]
    data['link'] = message.text
    data['username'] = message.from_user.username or 'ناشناس'
    
    preview_text = (
        f"🚨 **درخواست ثبت جدید (نیازمند تایید)**\n\n"
        f"🔗 نام کانال: {data['name']}\n"
        f"📝 توضیحات: {data['desc']}\n"
        f"🌐 لینک: {data['link']}\n"
        f"👤 ثبت‌کننده: @{data['username']} (ID: {user_id})"
    )
    
    pending_posts[user_id] = data
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ تایید و انتشار", callback_data=f"approve_{user_id}"),
        types.InlineKeyboardButton("❌ رد درخواست", callback_data=f"reject_{user_id}")
    )
    
    bot.send_message(ADMIN_CHAT_ID, preview_text, reply_markup=markup, parse_mode="Markdown")
    bot.send_message(chat_id=message.chat.id, text="⏳ اطلاعات شما با موفقیت ثبت شد و برای بررسی به ادمین ارسال گردید. پس از تایید در لینکدونی منتشر می‌شود.")
    
    user_data.pop(user_id, None)

@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_') or call.data.startswith('reject_'))
def handle_admin_decision(call):
    action, user_id_str = call.data.split('_')
    user_id = int(user_id_str)
    
    if action == 'approve':
        if user_id in pending_posts:
            data = pending_posts[user_id]
            
            post_text = (
                f"🔗 نام کانال: {data['name']}\n"
                f"📝 توضیحات: {data['desc']}\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"👤 ثبت‌کننده: @{data['username']}"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🚀 ورود به کانال", url=data['link']))
            
            bot.send_message(GROUP_CHAT_ID, post_text, reply_markup=markup)
            
            try:
                bot.send_message(user_id, "🎉 تبریک! کانال شما با موفقیت در لینکدونی منتشر شد.")
            except:
                pass
            
            bot.answer_callback_query(call.id, "✅ پست تایید و در گروه منتشر شد.")
            bot.edit_message_text(f"✅ **تایید شده و منتشر گردید.**\n\n{call.message.text}", ADMIN_CHAT_ID, call.message.message_id, parse_mode="Markdown")
            
            pending_posts.pop(user_id, None)
        else:
            bot.answer_callback_query(call.id, "⚠️ اطلاعات این پست منقضی شده یا قبلاً پردازش شده است.", show_alert=True)
            
    elif action == 'reject':
        if user_id in pending_posts:
            try:
                bot.send_message(user_id, "❌ متأسفانه درخواست شما برای ثبت در لینکدونی رد شد.")
            except:
                pass
            
            bot.answer_callback_query(call.id, "❌ درخواست رد شد.")
            bot.edit_message_text(f"❌ **رد شد.**\n\n{call.message.text}", ADMIN_CHAT_ID, call.message.message_id, parse_Mode="Markdown")
            
            pending_posts.pop(user_id, None)
        else:
            bot.answer_callback_query(call.id, "⚠️ این درخواست قبلاً پردازش شده است.", show_alert=True)

if __name__ == '__main__':
    print("Bot is running on cloud...")
    bot.infinity_polling()
