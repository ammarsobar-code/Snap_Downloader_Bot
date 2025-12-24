# --- معالج تحميل سناب شات المحدث ---
@bot.message_handler(func=lambda message: True)
def handle_snap(message):
    user_id = message.chat.id
    url = message.text.strip()

    if "snapchat.com" in url:
        prog = bot.reply_to(message, "⏳ جاري صيد السنابة... | Downloading...")
        try:
            # استخدام API مخصص للسناب
            res = requests.get(f"https://api.tikwm.com/api/extra/snapchat?url={url}").json()
            
            if res.get('code') == 0 and res.get('data'):
                video_url = res['data'].get('url')
                bot.send_video(user_id, video_url, caption="✅ تم التحميل | Done")
                bot.delete_message(user_id, prog.message_id)
            else:
                bot.edit_message_text("❌ تأكد أن القصة عامة (Public)\nMake sure the story is public", user_id, prog.message_id)
        except:
            bot.edit_message_text("❌ خطأ في الاتصال بالخدمة\nConnection error", user_id, prog.message_id)
