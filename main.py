import os, telebot, yt_dlp, time, sys, requests, json, tempfile
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
    """محاولة جلب البيانات عبر API وسيط (أقوى من المكتبات العادية)"""
    try:
        # المحرك الأول: خدمة vkrdown
        res = requests.get(f"https://api.vkrdown.com/instainfo/?url={url}", timeout=10).json()
        if res.get('success') and res.get('data'):
            return res['data']
    except:
        try:
            # المحرك الثاني (احتياطي): خدمة ddl-api
            res = requests.get(f"https://api.douyin.wtf/api?url={url}", timeout=10).json()
            if res.get('url'): return res
        except: return None
    return None

# --- 3. إعدادات البوت والتحقق ---
API_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)
user_status = {}

def get_welcome_markup(step=1):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url="https://snapchat.com/t/wxsuV6qD"))
    markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data=f"verify_{step}"))
    return markup

# --- 4. المعالجة الرئيسية ---

def handle_insta(url, chat_id):
    """معالجة الإنستغرام بنظام المحركات المتعددة"""
    data = get_insta_media(url)
    
    if data:
        media_group = []
        # إذا كانت البيانات قائمة (صور متعددة)
        if isinstance(data, list):
            for item in data:
                u = item.get('url')
                if item.get('type') == 'video': media_group.append(types.InputMediaVideo(u))
                else: media_group.append(types.InputMediaPhoto(u))
        
        # إرسال الوسائط
        if len(media_group) > 1:
            bot.send_media_group(chat_id, media_group[:10])
        elif len(media_group) == 1:
            if isinstance(media_group[0], types.InputMediaVideo): bot.send_video(chat_id, media_group[0].media)
            else: bot.send_photo(chat_id, media_group[0].media)
        else:
            # محاولة أخيرة عبر yt-dlp إذا فشل الـ API
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                bot.send_video(chat_id, info['url'])
    else:
        bot.send_message(chat_id, "❌ عذراً، لم نتمكن من جلب هذا المنشور. قد يكون الحساب خاصاً.")

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "<b>أهلاً بك 👋🏼 يرجى المتابعة للتفعيل:</b>", 
                     reply_markup=get_welcome_markup(1), parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('verify'))
def verify_handler(call):
    uid = call.message.chat.id
    if call.data == "verify_1":
        bot.send_message(uid, "<b>نعتذر لم يتم التحقق ❌</b>\nحاول مجدداً بعد المتابعة.", 
                         reply_markup=get_welcome_markup(2), parse_mode='HTML')
    else:
        user_status[uid] = "verified"
        bot.send_message(uid, "<b>تم التفعيل بنجاح ✅ أرسل الرابط الآن</b>", parse_mode='HTML')

@bot.message_handler(func=lambda m: True)
def handle_all(m):
    if user_status.get(m.chat.id) != "verified": return start(m)
    url = m.text.strip()
    prog = bot.reply_to(m, "<b>جاري التحميل... ⏳</b>", parse_mode='HTML')
    
    try:
        if "instagram.com" in url:
            handle_insta(url, m.chat.id)
        elif any(d in url for d in ["tiktok.com", "x.com", "snapchat.com"]):
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                bot.send_video(m.chat.id, info['url'])
        bot.delete_message(m.chat.id, prog.message_id)
    except:
        bot.edit_message_text("❌ فشل التحميل، تأكد من الرابط.", m.chat.id, prog.message_id)

if __name__ == "__main__":
    Thread(target=run).start()
    bot.remove_webhook()
    bot.infinity_polling(timeout=60)
