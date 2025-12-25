import os, telebot, requests
from telebot import types
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Snap Live"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 
bot = telebot.TeleBot(API_TOKEN)
user_status = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_status[user_id] = "step_1"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ تمت المتابعة | Done", callback_data="check_1"))
    bot.send_message(user_id, f"⚠️ يرجى متابعة حسابي أولاً:\nPlease follow first:\n\n{SNAP_LINK}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.message.chat.id
    if call.data == "check_1":
        user_status[user_id] = "step_2"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ تأكيد | Confirm", callback_data="check_final"))
        bot.send_message(user_id, f"❌ تأكد من المتابعة ثم اضغط تأكيد\nFollow then confirm:\n\n{SNAP_LINK}", reply_markup=markup)
    elif call.data == "check_final":
        user_status[user_id] = "verified"
        bot.send_message(user_id, "✅ تم التفعيل! أرسل الرابط الآن")

@bot.message_handler(func=lambda message: True)
def handle_snap(message):
    if user_status.get(message.chat.id) != "verified":
        send_welcome(message)
        return
    
    url = message.text.strip()
    if "snapchat.com" in url:
        prog = bot.reply_to(message, "⏳ جاري التحميل... | Downloading...")
        try:
            # استخدام محرك بحث TikWM المباشر للسناب (أكثر استقراراً)
            res = requests.get(f"https://www.tikwm.com/api/extra/snapchat?url={url}").json()
            if res.get('code') == 0:
                bot.send_video(message.chat.id, res['data']['url'], caption="✅ Done")
                bot.delete_message(message.chat.id, prog.message_id)
            else:
                bot.edit_message_text("❌ الرابط غير مدعوم أو خاص", message.chat.id, prog.message_id)
        except:
            bot.edit_message_text("❌ خطأ مؤقت، حاول لاحقاً", message.chat.id, prog.message_id)

keep_alive()
bot.infinity_polling()
