import logging
import os
import psycopg2
import random
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)

# --- CONFIGURATION ---
BOT_USERNAME = os.environ.get("BOT_USERNAME", "YourBotUsername")
DATABASE_URL = os.environ["DATABASE_URL"]
GROUP_ID = int(os.environ.get("GROUP_ID", "-1001234567890"))  # Change to your group ID

# --- LOGGING SETUP ---
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# --- DATABASE SETUP ---
def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def init_db():
    with get_conn() as con:
        with con.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS videos (
                    payload_id BIGINT PRIMARY KEY,
                    file_id TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS access_logs (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    payload_id BIGINT NOT NULL,
                    accessed_at TIMESTAMPTZ NOT NULL
                )
                """
            )
        con.commit()

def insert_video(payload_id, file_id):
    with get_conn() as con:
        with con.cursor() as cur:
            cur.execute(
                "INSERT INTO videos (payload_id, file_id, created_at) VALUES (%s, %s, %s)",
                (payload_id, file_id, datetime.utcnow()),
            )
        con.commit()

def get_file_id(payload_id):
    with get_conn() as con:
        with con.cursor() as cur:
            cur.execute("SELECT file_id FROM videos WHERE payload_id = %s", (payload_id,))
            row = cur.fetchone()
            return row[0] if row else None

def log_access(user_id, payload_id):
    with get_conn() as con:
        with con.cursor() as cur:
            cur.execute(
                "INSERT INTO access_logs (user_id, payload_id, accessed_at) VALUES (%s, %s, %s)",
                (user_id, payload_id, datetime.utcnow()),
            )
        con.commit()

# --- PAYLOAD GENERATION ---
def generate_unique_payload_id():
    with get_conn() as con:
        with con.cursor() as cur:
            while True:
                payload_id = random.randint(1000000000, 9999999999)
                cur.execute("SELECT 1 FROM videos WHERE payload_id = %s", (payload_id,))
                if not cur.fetchone():
                    return payload_id

# --- HANDLERS ---
async def handle_group_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.video:
        user = update.effective_user
        chat = update.effective_chat
        if chat.id != GROUP_ID:
            return  # Only process videos from the correct group

        file_id = update.message.video.file_id
        payload_id = generate_unique_payload_id()
        insert_video(payload_id, file_id)
        deep_link = f"https://t.me/{BOT_USERNAME}?start={payload_id}"

        logger.info(f"Saved video file_id={file_id} with payload_id={payload_id} by user {user.id}")
        await update.message.reply_text(
            f"🔗 Deep link for this video:\n{deep_link}\n\n"
            "Share this link to let users get this video via the bot."
        )

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    user = update.effective_user

    if args and args[0].isdigit():
        payload_id = int(args[0])
        file_id = get_file_id(payload_id)
        if file_id:
            logger.info(f"User {user.id} requested payload {payload_id} (OK)")
            log_access(user.id, payload_id)
            await update.message.reply_video(file_id)
        else:
            logger.info(f"User {user.id} requested payload {payload_id} (NOT FOUND)")
            await update.message.reply_text("❌ This video is not available.")
    else:
        await update.message.reply_text(
            "Welcome! Send me a valid deep link to receive a video."
        )

# --- MAIN ENTRYPOINT ---
def main():
    init_db()
    token = os.environ["BOT_TOKEN"]
    app = ApplicationBuilder().token(token).build()

    app.add_handler(MessageHandler(
        filters.Chat(GROUP_ID) & filters.VIDEO,
        handle_group_video,
    ))
    app.add_handler(CommandHandler("start", start_command))

    logger.info("Bot started. Waiting for messages...")
    app.run_polling()

if __name__ == "__main__":
    main()