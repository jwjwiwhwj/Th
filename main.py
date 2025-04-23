import telebot
import requests
from bs4 import BeautifulSoup
import os
from flask import Flask, request
import logging

# إعداد التسجيل لتتبع الأخطاء
logging.basicConfig(level=logging.INFO)

# توكن البوت من متغير بيئي
BOT_TOKEN = os.getenv('6275381938:AAG56EI1LbVwhBtJE9rik0esRQhU4_L_wN4')
if not BOT_TOKEN:
    raise ValueError("لم يتم العثور على BOT_TOKEN في متغيرات البيئة!")

# إنشاء البوت
bot = telebot.TeleBot(BOT_TOKEN)

# إنشاء تطبيق Flask لدعم Webhook
app = Flask(__name__)

# التعامل مع الأمر /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحبًا! أرسل رابط فيديو تيك توك وسأقوم بتحميله بدون علامة مائية.")

# التعامل مع روابط تيك توك
@bot.message_handler(regexp=r'https?://(vm\.tiktok\.com|www\.tiktok\.com)/.*')
def download_tiktok(message):
    video_url = message.text
    try:
        bot.reply_to(message, "جاري تحميل الفيديو، انتظر قليلاً...")

        # إعداد رأس الطلب لتجنب الحظر
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # استخدام ssstik.io لتحميل الفيديو
        download_url = f"https://ssstik.io/abc?url={video_url}"
        response = requests.get(download_url, headers=headers, timeout=30)
        response.raise_for_status()

        # استخراج رابط التحميل
        soup = BeautifulSoup(response.text, 'html.parser')
        download_link = soup.find('a', {'class': 'download-link'})
        if not download_link:
            bot.reply_to(message, "عذرًا، لم أتمكن من العثور على رابط التحميل. جرب رابطًا آخر.")
            return

        # تحميل الفيديو
        video_response = requests.get(download_link['href'], headers=headers, timeout=30)
        video_response.raise_for_status()

        video_file = f"video_{message.chat.id}.mp4"
        with open(video_file, 'wb') as f:
            f.write(video_response.content)

        # إرسال الفيديو
        with open(video_file, 'rb') as video:
            bot.send_video(message.chat.id, video, timeout=60)

        # حذف الملف المؤقت
        os.remove(video_file)
        bot.reply_to(message, "تم تحميل الفيديو بنجاح!")

    except requests.exceptions.RequestException as e:
        bot.reply_to(message, f"خطأ في الاتصال: {str(e)}")
        logging.error(f"Connection error: {e}")
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ: {str(e)}")
        logging.error(f"General error: {e}")

# Webhook لاستقبال التحديثات
@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK'
    return 'Invalid request', 403

# إعداد Webhook وتشغيل الخادم
if __name__ == '__main__':
    # إزالة Webhook قديم إن وجد
    bot.remove_webhook()
    # إعداد Webhook (يتم تحديث الرابط تلقائيًا على Railway)
    webhook_url = f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}/{BOT_TOKEN}"
    bot.set_webhook(url=webhook_url)
    # تشغيل Flask
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
