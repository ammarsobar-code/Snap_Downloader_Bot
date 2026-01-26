import os, telebot, yt_dlp, time, sys, subprocess, shutil, requests, json, tempfile
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. إعدادات السيرفر ---
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

# --- 4. محرك التحميل المطور ---
def dl_tiktok(url):
    try:
        res = requests.get(f"https://www.tikwm.com/api/?url={url}", timeout=10).json()
        if res.get('code') == 0: return res['data']
    except: return None

def dl_insta_advanced(url, chat_id, prog_id):
    c_path = prepare_cookies()
    ydl_opts = {
        'quiet': True,
        'cachedir': False,
        'cookiefile': c_path,
        'nocheckcertificate': True
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        # إذا كان المنشور يحتوي على صور/فيديوهات متعددة (Carousel)
        if 'entries' in info:
            media_group = []
            for entry in info['entries']:
                if entry.get('vcodec') != 'none':
                    media_group.append(types.InputMediaVideo(entry['url']))
                else:
                    media_group.append(types.InputMediaPhoto(entry['url']))
            bot.send_media_group(chat_id, media_group[:10]) # بحد أقصى 10
        
        # إذا كان رابط واحد (فيديو أو صورة)
        else:
            if info.get('vcodec') != 'none':
                bot.send_video(chat_id, info['url'], caption="✅ تم التحميل بنجاح")
            else:
                bot.send_photo(chat_id, info['url'], caption="✅ تم التحميل بنجاح")
    
    if c_path and os.path.exists(c_path): os.remove(c_path)

def dl_ytdlp_generic(url):
    opts = {'format': 'best', 'quiet': True, 'cachedir': False}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get('url')

# --- 5. نظام التحقق والردود ---
@bot.message_handler(commands=['start'])
def start(m):
    text = "<b>أهلاً بك 👋🏼 في بوت التحميل الشامل</b>\n\n⚠️ يرجى متابعة حساب السناب شات أولاً لتفعيل البوت:"
    bot.send_message(m.chat.id, text, reply_markup=get_welcome_markup(step=1), parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('verify'))
def verify_handler(call):
    uid = call.message.chat.id
    
    if call.data == "verify_1":
        # إرسال رسالة فشل جديدة بدلاً من تعديل السابقة
        fail_text = "<b>نعتذر منك لم يتم التحقق من المتابعة ❌👻</b>\nالرجاء التأكد من المتابعة ثم الضغط على زر التفعيل بالأسفل مجدداً."
        bot.send_message(uid, fail_text, reply_markup=get_welcome_markup(step=2), parse_mode='HTML')
        
    elif call.data == "verify_2":
        user_status[uid] = "verified"
        success_text = "<b>تم تفعيل البوت بنجاح ✅\nالآن أرسل أي رابط (Snap, TikTok, Insta, X)</b>"
        bot.send_message(uid, success_text, parse_mode='HTML')

@bot.message_handler(func=lambda m: True)
def handle_all_links(m):
    uid = m.chat.id
    url = m.text.strip()
    
    if user_status.get(uid) != "verified":
        start(m); return

    prog = bot.reply_to(m, "<b>جاري المعالجة... ⏳</b>", parse_mode='HTML')
    try:
        if
