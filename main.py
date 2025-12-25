import os, telebot, yt_dlp, time
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask للحفاظ على نشاط البوت ---
app = Flask('')
@app.route('/')
def home(): return "Snapchat Downloader Live"
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

# --- 3. نظام التحقق والمتابعة المطور (Bold + HTML) ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    welcome_text = (
        "<b>اهلا بك 👋🏼</b>\n"
        "شكرا لاستخدامك بوت تحميل السنابات 👻\n"
        "<b>⚠️ أولاً سيجب عليك متابعة حسابي في سناب شات لتشغيل البوت</b>\n\n"
        "<b>Welcome 👋🏼</b>\n"
        "Thank you for using Snapchat Downloader Bot 👻\n"
        "<b>⚠️ First, you'll need to follow my Snapchat account to activate the bot</b>"
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
        fail_msg = (
            "<b>نعتذر منك لم يتم التحقق من متابعتك لحساب سناب شات ❌👻</b>\n"
            "الرجاء الضغط على متابعة الحساب وسيتم توجيهك لسناب شات وبعد المتابعة اضغط على زر <b>تفعيل البوت 🔓</b>\n\n"
            "<b>We apologize, but your Snapchat account follow request has not been verified. ❌👻</b>\n"
            "Please click Follow Account and you will be redirected to Snapchat. After following, click the <b>Activate</b> button. 🔓"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
        markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="snap_step_2"))
        bot.send_message(user_id, fail_msg, reply_markup=markup, parse_mode='HTML')
        
    elif call.data == "snap_step_2":
        user_status[user_id] = "verified"
        success_text = (
            "<b>تم تفعيل البوت بنجاح ✅</b>\n"
            "<b>الرجاء ارسال الرابط 🔗</b>\n\n"
            "<b>The bot has been successfully activated ✅</b>\n"
            "<b>Please send the link 🔗</b>"
        )
        bot.send_message(user_id, success_text, parse_mode='HTML')

# --- 4. معالج تحميل سناب شات المطور ---
@bot.message_handler(func=lambda message: True)
def handle_snap(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    if "snapchat.com" in url:
        loading_text = "<b>جاري التحميل ... ⏳\nLoading... ⏳</b>"
        prog = bot.reply_to(message, loading_text, parse_mode='HTML')
        
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
                    bot.send_video(user_id, video_url)
                    
                    done_text = "<b>تم التحميل ✅\nDone ✅</b>"
                    bot.send_message(user_id, done_text, parse_mode='HTML')
                    bot.delete_message(user_id, prog.message_id)
                else:
                    raise Exception()
        except Exception:
            error_tech = (
                "<b>نعتذر منك نواجه الان مشكله تقنية وسيتم معالجتها في أقرب وقت ❌</b>\n\n"
                "<b>We apologize, we are currently experiencing a technical issue and it will be resolved as soon as possible ❌</b>"
            )
            bot.edit_message_text(error_tech, user_id, prog.message_id, parse_mode='HTML')
    else:
        wrong_link = (
            "<b>الرجاء ارسال رابط الصحيح ❌</b>\n"
            "<b>Please send the correct link ❌</b>"
        )
        bot.reply_to(message, wrong_link, parse_mode='HTML')

# --- 5. التشغيل الآمن ---
if __name__ == "__main__":
    keep_alive()
    try:
        bot.remove_webhook()
    except:
        pass
    time.sleep(1)
    print("Snap Bot is starting...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
