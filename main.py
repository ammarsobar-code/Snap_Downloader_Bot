import os, telebot, yt_dlp, time, sys, requests, json, tempfile, re
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. إعدادات السيرفر ---
app = Flask('')
@app.route('/')
def home(): return "Bot Multi-Engine is Online", 200

def run():
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

# --- 2. محركات البحث الاحترافية للإنستغرام ---
def get_insta_media(url):
    try:
        res = requests.get(f"https://api.vkrdown.com/instainfo/?url={url}", timeout=10).json()
        if res.get('success') and res.get('data'):
            return res['data']
    except:
        try:
            res = requests.get(f"https://api.douyin.wtf/api?url={url}", timeout=10).json()
            if res.get('url'): return res
        except: return None
    return None

# --- 3. إعدادات البوت والتحقق ---
API_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)
user_status = {}

WELCOME_TEXT = (
    "<b>أهلاً بك 👋🏼 في بوت التحميل الشامل 🚀</b>\n\n"
    "<b>يخدمك البوت في تحميل كل من:</b>\n"
    "👻 • صور ومقاطع القصص العامة في سناب شات\n"
    "🎵 • صور ومقاطع الحسابات العامة في تيك توك\n"
    "📸 • مقاطع فيديو الحسابات العامة والريلز في انستقرام\n"
    "📱 • مقاطع فيديو الحسابات العامة في منصة إكس\n\n"
    "⚠️ <b>لتفعيل البوت:</b> يرجى متابعة حسابي في سناب شات أولاً ثم الضغط على زر التفعيل بالأسفل 👇🏼"
)

ERROR_TEXT = (
    "<b>عذراً، لم نتمكن من تحميل هذا الرابط ❌</b>\n\n"
    "قد يكون الحساب خاص أو الرابط يحتوي على محتوى حساس ⚠️ أو حجمه كبير جداً 📁، وتفادياً لثقل البوت تم رفض التحميل."
)

def get_welcome_markup(step=1):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url="https://snapchat.com/t/wxsuV6qD"))
    markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data=f"verify_{step}"))
    return markup

# --- 4. المعالجة الرئيسية ---
def handle_insta(url, chat_id):
    data = get_insta_media(url)
    if data:
        media_group = []
        if isinstance(data, list):
            for item in data:
                u = item.get('url')
                if not u: continue
                if item.get('type') == 'video': media_group.append(types.InputMediaVideo(u))
                else: media_group.append(types.InputMediaPhoto(u))
        
        if len(media_group) > 1:
            bot.send_media_group(chat_id, media_group[:10])
        elif len(media_group) == 1:
            if isinstance(media_group[0], types.InputMediaVideo): bot.send_video(chat_id, media_group[0].media)
            else: bot.send_photo(chat_id, media_group[0].media)
        else:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                bot.send_video(chat_id, info['url'])
    else:
        bot.send_message(chat_id, ERROR_TEXT, parse_mode='HTML')

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, WELCOME_TEXT, reply_markup=get_welcome_markup(1), parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('verify'))
def verify_handler(call):
    uid = call.message.chat.id
    if call.data == "verify_1":
        bot.send_message(uid, "<b>نعتذر منك، لم يتم التحقق من المتابعة ❌👻</b>\nيرجى التأكد من المتابعة ثم الضغط على زر التفعيل مجدداً.", 
                         reply_markup=get_welcome_markup(2), parse_mode='HTML')
    else:
        user_status[uid] = "verified"
        bot.send_message(uid, "<b>تم تفعيل البوت بنجاح ✅🚀</b>\nيمكنك الآن إرسال أي رابط للتحميل مباشرة.", parse_mode='HTML')

@bot.message_handler(func=lambda m: True)
def handle_all(m):
    uid = m.chat.id
    if user_status.get(uid) != "verified": return start(m)
    
    url = m.text.strip()
    
    # التحقق: إذا لم يكن النص رابطاً يبدأ بـ http
    if not re.match(r'^https?://', url):
        # ملصق "تنبيه" (يمكنك تغيير الـ ID بملصقك الخاص)
        bot.send_sticker(uid, "CAACAgIAAxkBAAEL6ZlmB_3_S1s_Sample_ID") 
        bot.send_message(uid, "<b>عذراً، يرجى إرسال رابط صحيح من المنصات المدعومة فقط 🔗⚠️</b>", parse_mode='HTML')
        return

    prog = bot.reply_to(m, "<b>جاري التحميل... ⏳</b>", parse_mode='HTML')
    
    try:
        if "instagram.com" in url:
            handle_insta(url, uid)
        elif any(d in url for d in ["tiktok.com", "x.com", "twitter.com", "snapchat.com"]):
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                bot.send_video(uid, info['url'])
        else:
            bot.edit_message_text("<b>عذراً، هذا الرابط غير مدعوم حالياً ❌</b>", uid, prog.message_id, parse_mode='HTML')
            return

        bot.delete_message(uid, prog.message_id)
    except:
        bot.edit_message_text(ERROR_TEXT, uid, prog.message_id, parse_mode='HTML')

if __name__ == "__main__":
    Thread(target=run).start()
    bot.remove_webhook()
    bot.infinity_polling(timeout=60)
