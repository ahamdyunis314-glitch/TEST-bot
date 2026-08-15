import os
import threading
from flask import Flask
import telebot
from telebot import types
import pypdfium2 as pdfium
from PIL import Image

# سێرڤەری وێبی سەرەکی بۆ Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running perfectly!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# توکنی بۆتەکەت لێرە دابنێ
TOKEN = "7880955033:AAHd6GZx30SUTwzrsa4Jx63yuWUeVjmXWmo"
bot = telebot.TeleBot(TOKEN)

# داتابەیسی کاتی بۆ کۆکردنەوەی وێنەکان
user_images = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    first_name = message.from_user.first_name
    welcome_text = (
        f"سڵاو <b>{first_name}</b> 👋\n\n"
        "کاری من گۆڕینی وێنەیە بۆ PDF و بە پێچەوانەشەوە:\n\n"
        "📄 <b>PDF -> وێنە:</b> تەنها فایلی PDFەکە بنێرە.\n"
        "🖼 <b>وێنە -> PDF:</b> وێنەکان بنێرە و دواتر بنووسە /done"
    )
    
    markup = types.InlineKeyboardMarkup()
    try:
        bot_username = bot.get_me().username
        btn_share = types.InlineKeyboardButton(
            "بۆتەکە بڵاوبکەرەوە ↗️", 
            url=f"https://t.me/share/url?url=https://t.me/{bot_username}"
        )
        markup.add(btn_share)
    except Exception:
        pass

    bot.reply_to(message, welcome_text, reply_markup=markup, parse_mode='HTML')

# ۱. وەرگرتنی وێنەکان
@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    chat_id = message.chat.id
    if chat_id not in user_images:
        user_images[chat_id] = []

    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    img_path = f"temp_{chat_id}_{len(user_images[chat_id])}.jpg"
    with open(img_path, 'wb') as new_file:
        new_file.write(downloaded_file)

    user_images[chat_id].append(img_path)
    bot.reply_to(
        message, 
        f"📥 وێنەی ({len(user_images[chat_id])}) وەرگیرا.\n"
        "کاتێک هەموو وێنەکانت نارد بنووسە /done بۆ دروستکردنی PDF."
    )

# ۲. گۆڕینی وێنەکان بۆ PDF
@bot.message_handler(commands=['done'])
def make_pdf(message):
    chat_id = message.chat.id
    if chat_id not in user_images or not user_images[chat_id]:
        bot.reply_to(message, "⚠️ هیچ وێنەیەک نەدۆزرایەوە! تکایە سەرەتا چەند وێنەیەک بنێرە.")
        return

    msg = bot.reply_to(message, "⏳ لە پرۆسەی دروستکردنی PDFدایە، تکایە چاوەڕێ بکە...")
    
    try:
        images = []
        for img_p in user_images[chat_id]:
            img = Image.open(img_p).convert('RGB')
            images.append(img)

        pdf_path = f"converted_{chat_id}.pdf"
        images[0].save(pdf_path, save_all=True, append_images=images[1:])

        with open(pdf_path, 'rb') as pdf_file:
            bot.send_document(chat_id, pdf_file, caption="✅ فایلی PDFەکەت ئامادەیە!")

        # پاککردنەوە
        for img_p in user_images[chat_id]:
            if os.path.exists(img_p):
                os.remove(img_p)
        user_images[chat_id] = []
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

        bot.delete_message(chat_id, msg.message_id)
    except Exception as e:
        bot.reply_to(message, f"❌ هەڵەیەک ڕوویدا: {str(e)}")

# ۳. وەرگرتنی PDF و گۆڕینی بۆ وێنە
@bot.message_handler(content_types=['document'])
def handle_docs(message):
    try:
        if not message.document.file_name.lower().endswith('.pdf'):
            bot.reply_to(message, "تکایە تەنها فایلی PDF بنێرە.")
            return

        msg = bot.reply_to(message, "⏳ فایلی PDFەکە لە پرۆسەدا، دەکرێتە وێنە...")
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
        bot.reply_to(message, f"❌ هەڵەیەک ڕوویدا: {str(e)}")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("Bot is running...")
    bot.infinity_polling()
