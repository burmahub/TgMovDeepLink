import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from database import init_db, save_video, get_video
from dotenv import load_dotenv

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command with deep link parameters."""
    if not update.message:
        return
    args = context.args
    if args and args[0].startswith("video_"):
        video_id = args[0].replace("video_", "")
        video_data = get_video(video_id)
        if video_data:
            file_id, _ = video_data
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=file_id,
                caption="Here is the video you requested!"
            )
        else:
            await update.message.reply_text("Video not found or expired.")
    else:
        await update.message.reply_text("Welcome! Click a video link from the group to get the video.")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new videos in the group and generate deep links."""
    if not update.message or not update.message.video:
        return
    video = update.message.video
    message_id = str(update.message.message_id)
    chat_id = update.message.chat_id
    file_id = video.file_id

    # Save video metadata to database
    save_video(message_id, file_id, chat_id)

    # Generate deep link
    deep_link = f"https://t.me/{BOT_USERNAME}?start=video_{message_id}"
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Access this video: {deep_link}",
        reply_to_message_id=update.message.message_id
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors gracefully."""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Run the bot."""
    # Initialize database
    init_db()

    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VIDEO & filters.ChatType.GROUPS, handle_video))
    application.add_error_handler(error_handler)

    # Start the bot with webhook
    port = int(os.environ.get("PORT", 8443))
    webhook_url = os.environ.get("WEBHOOK_URL")
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TOKEN,
        webhook_url=f"{webhook_url}/{TOKEN}"
    )

if __name__ == "__main__":
    main()
