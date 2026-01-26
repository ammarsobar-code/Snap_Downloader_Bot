import os
import telebot
import yt_dlp
import time
import sys
import subprocess
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask للحفاظ على نشاط البوت وتوافق المنصة ---
app = Flask('')

@app.route('/')
def home():
    return "Snapchat Downloader is Running 24/7"

def run():
    # تعديل المنفذ ليتوافق مع إعدادات Koyeb (8000)
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. وظيفة التنظيف العميق ---
def reset_server_environment():
    """تنظيف شامل للمساحة والعمليات العالقة"""
    try:
        # مسح كاش yt-dlp
        subprocess.run([sys.executable, "-m", "yt_dlp", "--rm-cache-dir"], stderr=subprocess.DEVNULL)
    except:
        pass

    if os.name != 'nt':
        try:
            # قتل أي عمليات معلقة لـ yt-dlp
            subprocess.run(["pkill", "-9", "-f", "yt-dlp"], stderr=subprocess.DEVNULL)
        except:
            pass
    print("🧹 System Cleaned & Ready")

# --- 3. إعدادات البوت ---
# سيقوم البوت بسحب التوكن من Environment Variables في Koyeb
API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 
bot = telebot.TeleBot(API_TOKEN)
user_status = {}

# --- نظام التحقق والمتابعة ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    welcome_text = (
        "<b>اهلا بك 👋🏼</b>\n"
        "شكرا لاستخدامك بوت تحميل السنابات 👻\n"
        "<b>⚠️ أولاً سيجب عليك متابعة حسابي في سناب شات لتشغيل البوت</b>"
    )
    
    markup = types.InlineKeyboardMarkup()
    btn_follow = types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK)
    btn_confirm = types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="snap_step_1")
    markup.add(btn_follow)
    markup.add(btn_confirm)
    
    bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: True)
def handle_verification(call):
    user_id = call.message.chat.id
    
    if call.data == "snap_step_1":
        fail_msg = "<b>نعتذر منك لم يتم التحقق من المتابعة ❌</b>"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
        markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="snap_step_2"))
        bot.send_message(user_id, fail_msg, reply_markup=markup, parse_mode='HTML')
        
    elif call.data == "snap_step_2":
        user_status[user_id] = "verified"
        success_text = "<b>تم تفعيل البوت بنجاح ✅ أرسل الرابط الآن</b>"
        bot.send_message(user_id, success_text, parse_mode='HTML')

# --- 4. معالج تحميل سناب شات ---
@bot.message_handler(func=lambda message: True)
def handle_snap(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    if "snapchat.com" in url:
        prog = bot.reply_to(message, "<b>جاري التحميل ... ⏳</b>", parse_mode='HTML')
        
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'cachedir': False,
            'nocheckcertificate': True
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_url = info.get('url')
                
                if video_url:
                    bot.send_video(user_id, video_url)
                    bot.delete_message(user_id, prog.message_id)
                else:
                    raise Exception()
        except Exception:
            bot.edit_message_text("<b>عذراً، حدث خطأ فني ❌</b>", user_id, prog.message_id, parse_mode='HTML')
        finally:
            reset_server_environment()
    else:
        bot.reply_to(message, "<b>الرجاء ارسال رابط صحيح ❌</b>", parse_mode='HTML')

# --- 5. التشغيل النهائي ---
if __name__ == "__main__":
    keep_alive()
    print("Snap Bot is starting...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
