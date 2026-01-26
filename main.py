import os, telebot, yt_dlp, time, sys, subprocess, shutil, requests, json, tempfile
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. إعدادات السيرفر ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online with Fallback System", 200

def run():
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

# --- 2. إدارة الكوكيز ---
def prepare_cookies():
    path = "cookies.json"
    if not os.path.exists(path): return None
    try:
        with open(path, 'r') as f: cookies_data = json.load(f)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
        with open(tmp.name, 'w') as f:
            f.write("# Netscape HTTP Cookie File\n")
            for c in cookies_data:
                domain = c.get('domain', '')
                flag = "TRUE" if domain.startswith('.') else "FALSE"
                secure = "TRUE" if c.get('secure', False) else "FALSE"
                expiry = int(c.get('expirationDate', 0))
                f.write(f"{domain}\t{flag}\t{c.get('path', '/')}\t{secure}\t{expiry}\t{c.get('name','')}\t{c.get('value','')}\n")
        return tmp.name
    except: return None

# --- 3. المحرك الاحتياطي (Fallback API) ---
def insta_fallback(url):
    """محرك احتياطي لجلب البيانات إذا فشلت المكتبة الأساسية"""
    try:
        # نستخدم خدمة خارجية كمحرك بديل
        api_url = f"https://api.vkrdown.com/instainfo/?url={url}"
        res = requests.get(api_url, timeout=10).json()
        return res.get('data', [])
    except:
        return None

# --- 4. محرك إنستجرام الأساسي المطور ---
def dl_insta(url, chat_id):
    c_path = prepare_cookies()
    ydl_opts = {
        'quiet': True, 'cookiefile': c_path, 'nocheckcertificate': True,
        'extract_flat': False, 'skip_download': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                media = []
                for e in info['entries']:
                    u = e.get('url')
                    if not u: continue
                    media.append(types.InputMediaVideo(u) if e.get('vcodec') != 'none' else types.InputMediaPhoto(u))
                bot.send_media_group(chat_id, media[:10])
            else:
                u = info.get('url') or info.get('thumbnail')
                if info.get('vcodec') != 'none': bot.send_video(chat_id, u)
                else: bot.send_photo(chat_id, u)
    except Exception as e:
        # --- تفعيل نظام الطوارئ هنا ---
        print(f"yt-dlp failed, switching to fallback... Error: {e}")
        data = insta_fallback(url)
        if data:
            media = []
            for item in data:
                u = item.get('url')
                if item.get('type') == 'video': media.append(types.InputMediaVideo(u))
                else: media.append(types.InputMediaPhoto(u))
            
            if len(media) > 1: bot.send_media_group(chat_id, media[:10])
            elif len(media) == 1:
                if isinstance(media[0], types.InputMediaVideo): bot.send_video(chat_id, media[0].media)
                else: bot.send_photo(chat_id, media[0].media)
            else: bot.send_message(chat_id, "❌ لم نتمكن من جلب الوسائط حتى عبر المحرك الاحتياطي.")
        else:
            bot.send_message(chat_id, "❌ عذراً، هذا الرابط غير متاح حالياً (قد يكون الحساب خاصاً).")
    finally:
        if c_path and os.path.exists(c_path): os.remove(c_path)

# --- 5. إعدادات البوت والتحقق ---
API_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)
user_status = {}

@bot.message_handler(commands=['start'])
def start(m):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url="https://snapchat.com/t/wxsuV6qD"))
    markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="verify_1"))
    bot.send_message(m.chat.id, "<b>أهلاً بك 👋🏼 يرجى المتابعة للتفعيل:</b>", reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('verify'))
def verify_handler(call):
    if call.data == "verify_1":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url="https://snapchat.com/t/wxsuV6qD"))
        markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="verify_2"))
        bot.send_message(call.message.chat.id, "<b>نعتذر لم يتم التحقق ❌</b>", reply_markup=markup, parse_mode='HTML')
    else:
        user_status[call.message.chat.id] = "verified"
        bot.send_message(call.message.chat.id, "<b>تم التفعيل بنجاح ✅ أرسل الرابط الآن</b>", parse_mode='HTML')

@bot.message_handler(func=lambda m: True)
def handle_all(m):
    if user_status.get(m.chat.id) != "verified": return start(m)
    url = m.text.strip()
    prog = bot.reply_to(m, "<b>جاري العمل... ⏳</b>", parse_mode='HTML')
    try:
        if "instagram.com" in url: dl_insta(url, m.chat.id)
        else:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                bot.send_video(m.chat.id, ydl.extract_info(url, download=False)['url'])
        bot.delete_message(m.chat.id, prog.message_id)
    except: bot.edit_message_text("❌ فشل التحميل", m.chat.id, prog.message_id)

# --- 6. التشغيل ---
if __name__ == "__main__":
    Thread(target=run).start()
    bot.remove_webhook()
    bot.infinity_polling(timeout=60)
