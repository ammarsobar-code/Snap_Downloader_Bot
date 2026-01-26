import os, telebot, yt_dlp, time, sys, subprocess, shutil, requests, json, tempfile
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. إعدادات السيرفر والبقاء حياً ---
app = Flask('')
@app.route('/')
def home(): return "Multi-Downloader Bot is Online 24/7"

def run():
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. وظائف التنظيف وإدارة الكوكيز ---
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

# --- 3. إعدادات البوت والقائمة ---
API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD"
bot = telebot.TeleBot(API_TOKEN)
user_status = {}

def get_welcome_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
    markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="verify_1"))
    return markup

# --- 4. محركات التحميل ---
def dl_tiktok(url):
    try: # محاولة TikWM
        res = requests.get(f"https://www.tikwm.com/api/?url={url}", timeout=10).json()
        if res.get('code') == 0: return res['data']
    except: return None

def dl_ytdlp(url, cookie_path=None, is_insta=False):
    opts = {'format': 'best', 'quiet': True, 'cachedir': False, 'nocheckcertificate': True}
    if cookie_path: opts['cookiefile'] = cookie_path
    if is_insta: opts['outtmpl'] = 'downloads/%(id)s.%(ext)s'
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=is_insta)
        return ydl.prepare_filename(info) if is_insta else info.get('url')

# --- 5. معالجة الرسائل والتحقق ---
@bot.message_handler(commands=['start'])
def start(m):
    text = "<b>أهلاً بك 👋🏼 في بوت التحميل الشامل (Snap, TikTok, Insta, X)</b>\n\n⚠️ يرجى المتابعة للتفعيل:"
    bot.send_message(m.chat.id, text, reply_markup=get_welcome_markup(), parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('verify'))
def verify(call):
    uid = call.message.chat.id
    if call.data == "verify_1":
        bot.send_message(uid, "<b>لم يتم التحقق ❌ يرجى المتابعة ثم الضغط على تفعيل</b>", reply_markup=get_welcome_markup(), parse_mode='HTML')
    else:
        user_status[uid] = "verified"
        bot.send_message(uid, "<b>تم التفعيل بنجاح ✅ أرسل أي رابط الآن</b>", parse_mode='HTML')

@bot.message_handler(func=lambda m: True)
def handle_all(m):
    uid = m.chat.id
    url = m.text.strip()
    if user_status.get(uid) != "verified":
        start(m); return

    prog = bot.reply_to(m, "<b>جاري المعالجة... ⏳</b>", parse_mode='HTML')
    try:
        # --- TikTok ---
        if "tiktok.com" in url or "douyin.com" in url:
            data = dl_tiktok(url)
            if data and data.get('images'):
                bot.send_media_group(uid, [types.InputMediaPhoto(i) for i in data['images'][:10]])
            elif data and data.get('play'):
                bot.send_video(uid, data['play'])
            else:
                bot.send_video(uid, dl_ytdlp(url))

        # --- Instagram ---
        elif "instagram.com" in url:
            c_path = prepare_cookies()
            f_path = dl_ytdlp(url, c_path, is_insta=True)
            with open(f_path, 'rb') as v: bot.send_video(uid, v)
            if os.path.exists(f_path): os.remove(f_path)
            if c_path and os.path.exists(c_path): os.remove(c_path)

        # --- X (Twitter) & Snap ---
        elif any(x in url for x in ["x.com", "twitter.com", "snapchat.com"]):
            bot.send_video(uid, dl_ytdlp(url))

        else:
            bot.edit_message_text("<b>الرابط غير مدعوم ❌</b>", uid, prog.message_id)
            return

        bot.delete_message(uid, prog.message_id)
    except Exception as e:
        bot.edit_message_text(f"<b>عذراً، حدث خطأ أثناء التحميل ❌</b>", uid, prog.message_id)
    finally:
        auto_clean()

# --- 6. التشغيل ---
if __name__ == "__main__":
    keep_alive()
    auto_clean()
    print("Multi-Bot is starting...")
    bot.infinity_polling(timeout=20)
