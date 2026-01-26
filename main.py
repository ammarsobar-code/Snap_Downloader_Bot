import os, telebot, yt_dlp, time, sys, subprocess, shutil, requests, json, tempfile
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. إعدادات السيرفر (Koyeb) ---
app = Flask('')

@app.route('/')
def home(): return "Multi-Bot is Live", 200

def run():
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

# --- 2. وظائف التنظيف والكوكيز ---
def auto_clean():
    try:
        subprocess.run([sys.executable, "-m", "yt_dlp", "--rm-cache-dir"], stderr=subprocess.DEVNULL)
        if os.path.exists("downloads"):
            shutil.rmtree("downloads", ignore_errors=True)
        os.makedirs("downloads", exist_ok=True)
    except: pass

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

# --- 3. إعدادات البوت ---
API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD"
bot = telebot.TeleBot(API_TOKEN)
user_status = {}

def get_welcome_markup(step=1):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
    callback_val = "verify_1" if step == 1 else "verify_2"
    markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data=callback_val))
    return markup

# --- 4. محركات التحميل المتطورة ---
def dl_tiktok(url):
    try:
        res = requests.get(f"https://www.tikwm.com/api/?url={url}", timeout=10).json()
        if res.get('code') == 0: return res['data']
    except: return None

def dl_insta_advanced(url, chat_id):
    c_path = prepare_cookies()
    ydl_opts = {
        'quiet': True, 'no_warnings': True, 'cachedir': False,
        'cookiefile': c_path, 'nocheckcertificate': True, 'extract_flat': False
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            # ألبومات (Carousel)
            if 'entries' in info:
                media = []
                for e in info['entries']:
                    if e.get('vcodec') != 'none': media.append(types.InputMediaVideo(e['url']))
                    else: media.append(types.InputMediaPhoto(e['url']))
                for i in range(0, len(media), 10):
                    bot.send_media_group(chat_id, media[i:i+10])
            # منشور مفرد
            else:
                if info.get('vcodec') != 'none' or info.get('video_ext') != 'none':
                    bot.send_video(chat_id, info['url'], caption="✅ تم تحميل الفيديو")
                else:
                    bot.send_photo(chat_id, info.get('url') or info.get('thumbnail'), caption="✅ تم تحميل الصورة")
    except:
        bot.send_message(chat_id, "❌ فشل التحميل. تأكد من أن الحساب عام (Public).")
    finally:
        if c_path and os.path.exists(c_path): os.remove(c_path)

def dl_generic(url):
    with yt_dlp.YoutubeDL({'format': 'best', 'quiet': True}) as ydl:
        return ydl.extract_info(url, download=False).get('url')

# --- 5. المعالجات ونظام التحقق ---
@bot.message_handler(commands=['start'])
def start(m):
    text = "<b>أهلاً بك 👋🏼 في بوت التحميل الشامل</b>\n\n⚠️ يرجى متابعة حساب السناب شات أولاً:"
    bot.send_message(m.chat.id, text, reply_markup=get_welcome_markup(1), parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('verify'))
def verify_handler(call):
    uid = call.message.chat.id
    if call.data == "verify_1":
        fail = "<b>نعتذر منك لم يتم التحقق ❌👻</b>\nيرجى المتابعة ثم الضغط على تفعيل مجدداً."
        bot.send_message(uid, fail, reply_markup=get_welcome_markup(2), parse_mode='HTML')
    elif call.data == "verify_2":
        user_status[uid] = "verified"
        bot.send_message(uid, "<b>تم التفعيل بنجاح ✅ أرسل الرابط الآن</b>", parse_mode='HTML')

@bot.message_handler(func=lambda m: True)
def handle_all(m):
    uid = m.chat.id
    url = m.text.strip()
    if user_status.get(uid) != "verified":
        start(m); return

    prog = bot.reply_to(m, "<b>جاري المعالجة... ⏳</b>", parse_mode='HTML')
    try:
        if "tiktok.com" in url or "douyin.com" in url:
            data = dl_tiktok(url)
            if data and data.get('images'):
                bot.send_media_group(uid, [types.InputMediaPhoto(i) for i in data['images'][:10]])
            elif data and data.get('play'): bot.send_video(uid, data['play'])
            else: bot.send_video(uid, dl_generic(url))
        elif "instagram.com" in url:
            dl_insta_advanced(url, uid)
        elif any(d in url for d in ["x.com", "twitter.com", "snapchat.com"]):
            bot.send_video(uid, dl_generic(url))
        else:
            bot.edit_message_text("<b>الرابط غير مدعوم ❌</b>", uid, prog.message_id)
            return
        bot.delete_message(uid, prog.message_id)
    except:
        bot.edit_message_text("<b>فشل التحميل ❌</b>", uid, prog.message_id)
    finally:
        auto_clean()

# --- 6. التشغيل النهائي ---
if __name__ == "__main__":
    auto_clean()
    Thread(target=run).start()
    try:
        bot.remove_webhook() # لمسح أي تضارب سابق
        print("Bot is Polling...")
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        print(f"Polling Error: {e}")
        time.sleep(5)
