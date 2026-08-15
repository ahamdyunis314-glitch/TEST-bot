import os
import telebot
from PIL import Image
from pdf2image import convert_from_path

BOT_TOKEN = "7880955033:AAGfk0-THionUx9surZwnda_CjC4YBM7fvE"

bot = telebot.TeleBot(BOT_TOKEN)

try:
    bot.remove_webhook()
except Exception:
    pass

user_photos = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "سڵاو! بەخێربێیت 👋\n\n"
        "🛠 تایبەتمەندییەکانی من:\n"
        "1- وێنە 👈 PDF: چەند وێنەیەکم بۆ بنێرە و دواتر فەرمانی /make_pdf بنێرە.\n"
        "2- PDF 👈 وێنە: هەر فایلیێکی PDFم بۆ بنێریت، ڕاستەوخۆ دەیکەمەوە بە وێنە و بۆت دەنێرمەوە!"
    )
    bot.reply_to(message, welcome_text)

# --- 1. بەشی گۆڕینی وێنە بۆ PDF ---

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    chat_id = message.chat.id
    
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    photo_path = f"photo_{chat_id}_{message.message_id}.jpg"
    with open(photo_path, 'wb') as new_file:
        new_file.write(downloaded_file)
    
    if chat_id not in user_photos:
        user_photos[chat_id] = []
    
    user_photos[chat_id].append(photo_path)
    bot.reply_to(message, f"📸 وێنەکە وەرگیرا! (کۆی وێنەکان: {len(user_photos[chat_id])})\nوێنەی تر بنێرە یان /make_pdf بنووسە.")

@bot.message_handler(commands=['make_pdf'])
def convert_to_pdf(message):
    chat_id = message.chat.id
    
    if chat_id not in user_photos or len(user_photos[chat_id]) == 0:
        bot.reply_to(message, "هیچ وێنەیەک نییە! تکایە سەرەتا چەند وێنەیەک بنێرە.")
        return

    msg = bot.reply_to(message, "فایلی PDF دروست دەکرێت... ⏳")

    try:
        image_list = []
        for path in user_photos[chat_id]:
            img = Image.open(path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            image_list.append(img)
            
        pdf_path = f"document_{chat_id}.pdf"
        image_list[0].save(pdf_path, save_all=True, append_images=image_list[1:])
        
        with open(pdf_path, 'rb') as pdf_file:
            bot.send_document(chat_id, pdf_file, caption="📄 فایلی PDFەکەت ئامادەیە!")
            
        for path in user_photos[chat_id]:
            if os.path.exists(path):
                os.remove(path)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            
        user_photos[chat_id] = []

    except Exception as e:
        bot.edit_message_text(f"کێشەیەک ڕوویدا: {str(e)}", chat_id, msg.message_id)

# --- 2. بەشی گۆڕینی PDF بۆ وێنە ---

@bot.message_handler(content_types=['document'])
def handle_document(message):
    chat_id = message.chat.id
    file_name = message.document.file_name
    
    if not file_name.lower().endswith('.pdf'):
        bot.reply_to(message, "تکایە فایلی PDF بنێرە!")
        return

    msg = bot.reply_to(message, "فایلی PDFەکە دەگۆڕدرێت بۆ وێنە... ⏳")

    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        pdf_path = f"input_{chat_id}.pdf"
        with open(pdf_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        images = convert_from_path(pdf_path)
        
        for i, image in enumerate(images):
            img_path = f"page_{chat_id}_{i+1}.jpg"
            image.save(img_path, 'JPEG')
            
            with open(img_path, 'rb') as img_file:
                bot.send_photo(chat_id, img_file, caption=f"🖼 لاپەڕەی {i+1}")
                
            if os.path.exists(img_path):
                os.remove(img_path)
                
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    except Exception as e:
        bot.edit_message_text(f"کێشەیەک ڕوویدا: {str(e)}", chat_id, msg.message_id)

print("بۆتەکە بە سەرکەوتوویی کارا بوو...")
bot.polling(non_stop=True)
