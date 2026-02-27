import os
import tempfile
import shutil
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import yt_dlp

# ========== CONFIGURATION ==========
TOKEN = "8244318260:AAE3y35QsXmWNgPY4OtD6-LstYQ_trtkPBI"  # Replace with your actual bot token

# ========== DOWNLOADER ==========
class Downloader:
    def download(self, url, quality):
        temp_dir = tempfile.mkdtemp()
        try:
            if quality == '480p':
                fmt = 'best[height<=480][ext=mp4]/best[height<=480]/best'
            else:
                fmt = 'best[height<=720][ext=mp4]/best[height<=720]/best'

            ydl_opts = {
                'format': fmt,
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'quiet': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                files = os.listdir(temp_dir)
                if not files:
                    return None, "No file downloaded"
                return {
                    'path': os.path.join(temp_dir, files[0]),
                    'title': info.get('title', 'Video'),
                    'temp_dir': temp_dir
                }, None
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return None, str(e)

    def cleanup(self, temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)

dl = Downloader()
user_sessions = {}  # Temporary storage for URLs

# ========== BOT HANDLERS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎥 **Instagram Reel Downloader**\n\n"
        "Send me any Instagram Reel link and I'll download it for you!\n"
        "Example: `https://www.instagram.com/reel/ABC123/`\n\n"
        "Choose quality after sending the link.",
        parse_mode='Markdown'
    )

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text

    if 'instagram.com' not in url and 'instagr.am' not in url:
        await update.message.reply_text("❌ That's not an Instagram link.")
        return

    user_sessions[user_id] = {'url': url}
    keyboard = [
        [InlineKeyboardButton("480p", callback_data='480p'),
         InlineKeyboardButton("720p", callback_data='720p')]
    ]
    await update.message.reply_text(
        "Choose quality:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def quality_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in user_sessions:
        await query.edit_message_text("❌ Session expired. Send the link again.")
        return

    quality = query.data
    url = user_sessions[user_id]['url']

    await query.edit_message_text(f"⏳ Downloading {quality}...")

    try:
        result, error = dl.download(url, quality)
        if error:
            await query.edit_message_text(f"❌ {error}")
            return

        # Send video
        with open(result['path'], 'rb') as f:
            await query.message.reply_video(f)

        await query.message.reply_text("✅ Download complete!")
        dl.cleanup(result['temp_dir'])

    except Exception as e:
        await query.edit_message_text(f"❌ Error: {str(e)}")
    finally:
        if user_id in user_sessions:
            del user_sessions[user_id]

# ========== MAIN ==========
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(quality_callback, pattern='^(480p|720p)$'))
    print("✅ Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
