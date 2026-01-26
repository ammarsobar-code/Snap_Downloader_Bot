import os, telebot, yt_dlp, time, sys, subprocess, shutil, requests, json, tempfile
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. إعدادات السيرفر والبقاء حياً على Koyeb ---
app = Flask('')
@app.route('/')
def home(): return "Multi-Downloader Bot is Online 24/7"

def run():
    # استخدام المنفذ 8000 كما في إعدادات Koyeb الخاصة بك
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. وظائف التنظيف وإدارة الكوكيز ---
def auto_clean():
    """تنظيف الذاكرة والكاش لضمان استقرار البوت"""
    try:
        subprocess.run([sys.executable, "-m", "yt_dlp", "--rm-cache-dir"], stderr=subprocess.DEVNULL)
        if os.path.exists("downloads"):
            shutil.rmtree("downloads", ignore_errors=True)
        os.makedirs("downloads", exist_ok=True)
    except: pass

def prepare_cookies():
    """تحويل ملف JSON إلى تنسيق Netscape الذي يفهمه yt-dlp"""
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

def get_welcome_markup(step=1):
    """إنشاء أزرار التحقق بناءً على المرحلة"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
    callback_val = "verify_1" if step == 1 else "verify_2"
    markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data=callback_val))
    return markup

# --- 4. محركات التحميل ---
def dl_tiktok(url):
    try:
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

# --- 5. معالجة الرسائل والتحقق (نظام الضغطتين) ---
@bot.message_handler(commands=['start'])
def start(m):
    text = "<b>أهلاً بك 👋🏼 في بوت التحميل الشامل</b>\n\n⚠️ يرجى متابعة حساب السناب شات أولاً لتفعيل البوت:"
    bot.send_message(m.chat.id, text, reply_markup=get_welcome_markup(step=1), parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('verify'))
def verify_handler(call):
    uid = call.message.chat.id
    
    if call.data == "verify_1":
        # المرحلة الأولى: إظهار رسالة الفشل وتغيير الزر لـ verify_2
        fail_text = "<b>نعتذر منك لم يتم التحقق من المتابعة ❌👻</b>\nالرجاء التأكد من المتابعة ثم الضغط على زر التفعيل مرة أخرى."
        bot.edit_message_text(fail_text, uid, call.message.message_id, 
                              reply_markup=get_welcome_markup(step=2), parse_mode='HTML')
        
    elif call.data == "verify_2":
        # المرحلة الثانية: التفعيل بنجاح
        user_status[uid] = "verified"
        success_text = "<b>تم تفعيل البوت بنجاح ✅\nالآن أرسل أي رابط (Snap, TikTok, Insta, X)</b>"
        bot.edit_message_text(success_text, uid, call.message.message_id, parse_mode='HTML')

@bot.message_handler(func=lambda m: True)
def handle_all_links(m):
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

        # --- X & Snap ---
        elif any(domain in url for domain in ["x.com", "twitter.com", "snapchat.com"]):
            video_url = dl_ytdlp(url)
            bot.send_video(uid, video_url)

        else:
            bot.edit_message_text("<b>الرابط غير مدعوم أو غير صحيح ❌</b>", uid, prog.message_id, parse_mode='HTML')
            return

        bot.delete_message(uid, prog.message_id)
    except Exception:
        bot.edit_message_text("<b>عذراً، حدث خطأ أثناء التحميل ❌</b>", uid, prog.message_id, parse_mode='HTML')
    finally:
        auto_clean()

# --- 6. التشغيل النهائي ---
if __name__ == "__main__":
    keep_alive()
    auto_clean()
    print("Multi-Bot is Online...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
