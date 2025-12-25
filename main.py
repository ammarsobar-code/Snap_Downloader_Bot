import os, telebot, yt_dlp
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask ---
app = Flask('')
@app.route('/')
def home(): return "Snapchat Bot is Live!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. إعدادات البوت ---
API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 
bot = telebot.TeleBot(API_TOKEN)
user_status = {}

# --- 3. نظام التحقق والمتابعة ---
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
        bot.send_message(user_id, f"❌ لم يتم التحقق بعد، تأكد من المتابعة ثم اضغط تأكيد\nVerification failed:\n\n{SNAP_LINK}", reply_markup=markup)
    elif call.data == "check_final":
        user_status[user_id] = "verified"
        bot.send_message(user_id, "✅ تم تفعيل البوت بنجاح! أرسل الرابط الآن")

# --- 4. معالج تحميل سناب شات (باستخدام المحرك العملاق yt-dlp) ---
@bot.message_handler(func=lambda message: True)
def handle_snap(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    if "snapchat.com" in url:
        prog = bot.reply_to(message, "⏳ جاري التحميل... | Downloading...")
        
        # إعدادات المحرك ليكون سريعاً ولا يستهلك رام سيرفر Render
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'cachedir': False
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_url = info.get('url')
                
                if video_url:
                    bot.send_video(user_id, video_url, caption="✅ تم التحميل بنجاح | Downloaded")
                    bot.delete_message(user_id, prog.message_id)
                else:
                    bot.edit_message_text("❌ لم أتمكن من العثور على الفيديو، تأكد أن القصة عامة.", user_id, prog.message_id)
        except Exception:
            bot.edit_message_text("❌ خطأ: الرابط خاص أو غير مدعوم حالياً.", user_id, prog.message_id)
    else:
        bot.reply_to(message, "❌ يرجى إرسال رابط سناب شات صحيح.")

# --- 5. التشغيل وحل مشكلة Conflict ---
if __name__ == "__main__":
    keep_alive()
    # السطر السحري لحل مشكلة Conflict 409
    bot.remove_webhook() 
    print("Bot is starting...")
    bot.infinity_polling(skip_pending_updates=True)
