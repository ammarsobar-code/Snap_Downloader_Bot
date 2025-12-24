import os
import telebot
from telebot import types
import requests
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask لمنع النوم ---
app = Flask('')
@app.route('/')
def home(): return "Snapchat Bot is Live!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. إعدادات البوت (يجب أن تكون قبل استخدام @bot) ---
API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 
bot = telebot.TeleBot(API_TOKEN)
user_status = {}

# --- 3. نظام التحقق ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_status[user_id] = "step_1"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ تمت المتابعة | Done", callback_data="check_1"))
    
    msg = f"⚠️ يرجى متابعة حسابي أولاً لتفعيل البوت:\nPlease follow my account first:\n\n{SNAP_LINK}"
    bot.send_message(user_id, msg, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.message.chat.id
    if call.data == "check_1":
        user_status[user_id] = "step_2"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ تأكيد | Confirm", callback_data="check_final"))
        bot.send_message(user_id, f"❌ لم يتم التحقق بعد، تأكد من المتابعة ثم اضغط تأكيد\nVerification failed, make sure to follow then confirm:\n\n{SNAP_LINK}", reply_markup=markup)
        bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)
    
    elif call.data == "check_final":
        user_status[user_id] = "verified"
        bot.send_message(user_id, "✅ تم تفعيل البوت بنجاح! أرسل الرابط الآن\nBot activated successfully! Send the link now")
        bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)

# --- 4. معالج تحميل سناب شات المحدث ---
@bot.message_handler(func=lambda message: True)
def handle_snap(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    if "snapchat.com" in url:
        prog = bot.reply_to(message, "⏳ جاري التحميل... | Downloading...")
        try:
            # استخدام API مستقر للسناب
            api_url = f"https://api.tikwm.com/api/extra/snapchat?url={url}"
            res = requests.get(api_url).json()
            
            if res.get('code') == 0 and res.get('data'):
                video_url = res['data'].get('url')
                bot.send_video(user_id, video_url, caption="✅ تم التحميل بنجاح | Downloaded Successfully")
                bot.delete_message(user_id, prog.message_id)
            else:
                bot.edit_message_text("❌ تأكد أن القصة عامة (Public)\nMake sure the story is public", user_id, prog.message_id)
        except Exception as e:
            bot.edit_message_text("❌ عذراً، الخدمة مشغولة حالياً\nService busy, try again later", user_id, prog.message_id)
    else:
        bot.reply_to(message, "❌ يرجى إرسال رابط سناب شات صحيح\nPlease send a valid Snapchat link")

# --- 5. التشغيل ---
if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
