import os
import threading
from flask import Flask
import telebot
from telebot import types
import pypdfium2 as pdfium

# دروستکردنی سێرڤەری خۆڕایی بۆ Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# توکنی بۆتەکەت
TOKEN = "7880955033:AAH_s-_annj1tK22xpXL55Wk-B9ryGx1E5Q"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    first_name = message.from_user.first_name

    welcome_text = (
        f"سڵاو <b>{first_name}</b>\n\n"
        "کاری من گۆرینی وێنەیە بۆ PDF وە بە پێچەوانەشەوە ئەتوانی تەنها وێنەیەک یان فایلێک بنێرە بنێرە 🗳"
    )
    
    markup = types.InlineKeyboardMarkup()
    # گۆڕینی switch_inline_query بۆ url بۆ ئەوەی هەڵە نەدات
    btn_share = types.InlineKeyboardButton("بۆتەکە بڵاوبکەرەوە ↗️", url=f"https://t.me/share/url?url=https://t.me/{bot.get_me().username}")
    markup.add(btn_share)
    
    bot.reply_to(message, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    try:
        if not message.document.file_name.lower().endswith('.pdf'):
            bot.reply_to(message, "تکایە تەنها فایلی PDF بنێرە.")
            return

        msg = bot.reply_to(message, "فایلەکە لە وەرگرتندایە و دەکرێتە وێنە، تکایە چاوەڕێ بکە...")
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        pdf_path = f"temp_{message.chat.id}.pdf"
        with open(pdf_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        pdf = pdfium.PdfDocument(pdf_path)
        for i, page in enumerate(pdf):
            image = page.render(scale=2).to_pil()
            img_path = f"page_{i+1}.jpg"
            image.save(img_path, "JPEG")
            
            with open(img_path, 'rb') as img_file:
                bot.send_photo(message.chat.id, img_file, caption=f"لاپەڕەی {i+1}")
            
            if os.path.exists(img_path):
                os.remove(img_path)

        pdf.close()
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            
        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"ڕووداوێک ڕوویدا لە کاتی پرۆسەکەدا: {str(e)}")

if __name__ == "__main__":
    # داگیرساندنی پۆرتی خۆڕایی
    threading.Thread(target=run_flask).start()
    print("Bot is running...")
    bot.infinity_polling()
