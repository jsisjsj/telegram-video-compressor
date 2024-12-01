import os
import requests
import subprocess
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables.")

VIDEO_DIR = "./videos/"
os.makedirs(VIDEO_DIR, exist_ok=True)


async def start(update: Update, context: CallbackContext):
    """Handler for the /start command."""
    await update.message.reply_text("Send me a URL of a video, and I'll compress it for you!")


async def handle_url(update: Update, context: CallbackContext):
    """Handles incoming video URLs."""
    url = update.message.text.strip()
    user_id = update.message.chat_id

    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("Invalid URL! Please send a valid URL.")
        return

    try:
        response = requests.head(url, allow_redirects=True)
        if response.status_code != 200:
            await update.message.reply_text(f"URL is not accessible! Status code: {response.status_code}")
            return
        content_length = response.headers.get("content-length", "unknown")
        await update.message.reply_text(f"URL is valid! File size: {content_length} bytes")
    except Exception as e:
        await update.message.reply_text(f"Error validating URL: {e}")
        return

    await update.message.reply_text("Downloading video... Please wait.")
    try:
        file_path = os.path.join(VIDEO_DIR, f"{user_id}_video.mp4")
        download_video(url, file_path)

        compressed_path = os.path.join(VIDEO_DIR, f"{user_id}_compressed.mp4")
        compress_video(file_path, compressed_path)

        await update.message.reply_text("Video compressed successfully!")
        await update.message.reply_document(document=open(compressed_path, "rb"))
    except Exception as e:
        await update.message.reply_text(f"Error processing video: {e}")


def download_video(url: str, file_path: str):
    """Downloads the video file."""
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(file_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def compress_video(input_file: str, output_file: str):
    """Compresses the video using ffmpeg."""
    command = ["ffmpeg", "-i", input_file, "-vcodec", "libx264", "-crf", "32", output_file]
    subprocess.run(command, check=True)


def main():
    """Main entry point for the bot."""
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

    app.run_polling()


if __name__ == "__main__":
    main()
