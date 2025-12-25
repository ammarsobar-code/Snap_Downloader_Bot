import os, telebot, yt_dlp
from telebot import types
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Snapchat Engine Active"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run).start()

API_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)
user_status = {}

@bot.message_handler(func=lambda m: "snapchat.com" in m.text)
def handle_snap(message):
    url = message.text.strip()
    prog = bot.reply_to(message, "⏳ جاري استخراج الفيديو... | Extracting...")
    
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info['url']
            bot.send_video(message.chat.id, video_url, caption="✅ تم التحميل | Done")
            bot.delete_message(message.chat.id, prog.message_id)
    except Exception:
        bot.edit_message_text("❌ عذراً، هذا الرابط خاص أو غير مدعوم حالياً.", message.chat.id, prog.message_id)

keep_alive()
bot.infinity_polling(timeout=10, long_polling_timeout=5)
