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

# (نفس دالات التحقق السابقة هنا لضمان التطابق)

@bot.message_handler(func=lambda message: True)
def handle_snap(message):
    if user_status.get(message.chat.id) != "verified":
        return
    
    url = message.text.strip()
    if "snapchat.com" in url:
        prog = bot.reply_to(message, "⏳ جاري التحميل...")
        try:
            # استخدام API مباشر يتجنب حظر IP السيرفرات
            res = requests.post("https://scdownloader.net/download", data={"url": url}).text
            # ملاحظة: سنستخدم الـ API الاحتياطي في حال فشل الكشط المباشر
            api_url = f"https://api.tikwm.com/api/extra/snapchat?url={url}"
            data = requests.get(api_url).json()
            if data['code'] == 0:
                bot.send_video(message.chat.id, data['data']['url'])
                bot.delete_message(message.chat.id, prog.message_id)
            else:
                bot.edit_message_text("❌ عذراً، لم نتمكن من الوصول للسنابة.", message.chat.id, prog.message_id)
        except:
            bot.edit_message_text("❌ خطأ تقني متكرر.", message.chat.id, prog.message_id)

keep_alive()
bot.infinity_polling()
