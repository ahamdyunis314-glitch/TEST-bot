import os
import telebot
import pypdfium2 as pdfium

# توکنی بۆتەکەت لێرە دایبنێ
TOKEN = "7880955033:AAE7NS-_TbuCQcuN1SJewnFtdmiFuNJ2PyU"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "سڵاو! فایلی PDFم بۆ بنێرە تا بۆت بپەڕێنمەوە بۆ وێنە (JPG).")

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

print("Bot is running...")
bot.infinity_polling()
