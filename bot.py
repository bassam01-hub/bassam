# -*- coding: utf-8 -*-
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import yt_dlp

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# الحصول على التوكن من متغيرات البيئة
BOT_TOKEN = os.environ.get('BOT_TOKEN', '----')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📥 جودة المصدر", callback_data="format_source")],
        [InlineKeyboardButton("🎥 1080p", callback_data="format_1080")],
        [InlineKeyboardButton("📹 720p", callback_data="format_720")],
        [InlineKeyboardButton("💾 MP3", callback_data="format_audio")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "مرحباً! 👋\n"
        "أرسل لي رابط فيديو من:\n"
        "• يوتيوب\n• إنستغرام\n• تيك توك\n• تويتر\n\n"
        "اختر جودة التحميل:",
        reply_markup=reply_markup
    )

def download_video(url, format_choice='format_source'):
    # إعدادات الجودة
    format_settings = {
        'format_source': {
            'format': 'best',
            'description': 'جودة المصدر'
        },
        'format_1080': {
            'format': 'best[height<=1080]',
            'description': 'جودة 1080p'
        },
        'format_720': {
            'format': 'best[height<=720]', 
            'description': 'جودة 720p'
        },
        'format_audio': {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'description': 'صوت MP3'
        }
    }
    
    settings = format_settings.get(format_choice, format_settings['format_source'])
    
    ydl_opts = {
        'outtmpl': 'downloaded_media.%(ext)s',
        'socket_timeout': 30,
        'no_check_certificate': True,
        'ignoreerrors': True,
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        },
    }
    
    # دمج الإعدادات
    ydl_opts.update(settings)
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # تعديل اسم الملف إذا كان تحميل صوت
            if format_choice == 'format_audio':
                filename = os.path.splitext(filename)[0] + '.mp3'
                
            return filename, info.get('title', 'ميديا'), settings['description']
            
    except Exception as e:
        raise Exception(f"فشل في التحميل: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    
    # التحقق من أن النص يحتوي على رابط
    supported_domains = [
        'youtube.com', 'youtu.be', 
        'instagram.com', 'instagr.am',
        'tiktok.com', 'vm.tiktok.com',
        'twitter.com', 'x.com'
    ]
    
    if not any(domain in message_text for domain in supported_domains):
        await update.message.reply_text("❌ يرجى إرسال رابط فيديو صالح من إحدى المنصات المدعومة.")
        return
    
    format_choice = context.user_data.get('format', 'format_source')
    wait_message = await update.message.reply_text("⏳ جاري تحميل الفيديو...")
    
    try:
        file_path, media_title, quality_description = download_video(message_text, format_choice)
        
        file_extension = os.path.splitext(file_path)[1].lower()
        
        with open(file_path, 'rb') as media_file:
            if file_extension == '.mp3':
                await update.message.reply_audio(
                    audio=media_file,
                    caption=f"✅ {media_title}\n🎵 {quality_description}"
                )
            else:
                await update.message.reply_video(
                    video=media_file,
                    caption=f"✅ {media_title}\n🎬 {quality_description}"
                )
        
        # تنظيف الملف المؤقت
        if os.path.exists(file_path):
            os.remove(file_path)
        
        await wait_message.delete()
        
    except Exception as e:
        error_msg = f"❌ حدث خطأ: {str(e)}"
        await update.message.reply_text(error_msg)
        await wait_message.delete()

async def format_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    format_choice = query.data
    context.user_data['format'] = format_choice
    
    format_names = {
        'format_source': 'جودة المصدر (الأفضل)',
        'format_1080': 'جودة 1080p',
        'format_720': 'جودة 720p', 
        'format_audio': 'صوت MP3'
    }
    
    await query.edit_message_text(
        f"✅ تم اختيار: {format_names[format_choice]}\n"
        f"الآن أرسل رابط الفيديو."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📥 جودة المصدر", callback_data="format_source")],
        [InlineKeyboardButton("🎥 1080p", callback_data="format_1080")],
        [InlineKeyboardButton("📹 720p", callback_data="format_720")],
        [InlineKeyboardButton("💾 MP3", callback_data="format_audio")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🆘 المساعدة:\n\n"
        "📋 المنصات المدعومة:\n"
        "• يوتيوب\n• إنستجرام\n• تيك توك\n• تويتر\n\n"
        "🎛️ خيارات الجودة:\n"
        "• جودة المصدر: أفضل جودة متاحة\n"
        "• 1080p: جودة عالية FHD\n" 
        "• 720p: جودة متوسطة HD\n"
        "• MP3: صوت فقط بجودة 320kbps\n\n"
        "اختر الجودة:",
        reply_markup=reply_markup
    )

def main():
    # التحقق من وجود التوكن
    if not BOT_TOKEN:
        print("❌ خطأ: لم يتم تعيين BOT_TOKEN")
        print("🔧 يرجى تعيين متغير البيئة BOT_TOKEN على Railway")
        return
    
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CallbackQueryHandler(format_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print("🤖 البوت يعمل الآن على Railway...")
        print("✅ يمكنه تحميل الفيديوهات من جميع المنصات بدون مشاكل!")
        application.run_polling()
        
    except Exception as e:
        print(f"❌ خطأ في تشغيل البوت: {e}")

if __name__ == "__main__":
    main()
