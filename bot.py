import logging
import requests
import yt_dlp
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import os

# Replace with your bot's API token
API_TOKEN = '7884394642:AAGhS5MSoR3DoWed14Ae4AmJlaqcmfoJIZc'

# YouTube Data API key
YOUTUBE_API_KEY = 'AIzaSyDN6z1KtI9TYbHVzUKGOI7Dbnoui_wGGtc'

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Ensure the downloads folder exists
os.makedirs("downloads", exist_ok=True)

# Start command
async def start(update: Update, context) -> None:
    await update.message.reply_text(
        "Hello! Welcome to MelodyFetch, I can help you search for music and download them. Send me the song name!"
    )

# Search for music using YouTube Data API
def search_music(query: str) -> list:
    api_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&type=video&key={YOUTUBE_API_KEY}"
    response = requests.get(api_url)
    data = response.json()

    results = []
    for item in data.get("items", [])[:5]:  # Limit to top 5 results
        title = item["snippet"]["title"]
        video_id = item["id"]["videoId"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        results.append({"title": title, "url": video_url, "video_id": video_id})

    return results

# Create inline buttons with music results
def create_buttons(results):
    keyboard = [
        [InlineKeyboardButton(result["title"], callback_data=result["video_id"])]
        for result in results
    ]
    return InlineKeyboardMarkup(keyboard)

# Handle the user's message and search for music
async def handle_message(update: Update, context) -> None:
    query = update.message.text
    await update.message.reply_text(f"Searching for: {query}")

    # Get search results
    results = search_music(query)

    if results:
        message = "Here are the top results:"
        await update.message.reply_text(message, reply_markup=create_buttons(results))
    else:
        await update.message.reply_text("No results found. Try a different query.")

# A function to download the song asynchronously using yt-dlp
async def download_song(video_url, video_id):
    ydl_opts = {
        "format": "bestaudio/best",  # Downloads the best available audio format
        "outtmpl": f"downloads/{video_id}.%(ext)s",  # Saves the audio in a folder called downloads
        "postprocessors": [],  # Do not use postprocessors like ffmpeg
    }

    loop = asyncio.get_event_loop()
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = await loop.run_in_executor(None, ydl.extract_info, video_url)
        return f"downloads/{info_dict['id']}.webm"  # Return path to downloaded audio file

# Handle the button press and download the song
async def button_handler(update: Update, context) -> None:
    query = update.callback_query
    video_id = query.data
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    await query.answer()
    await query.edit_message_text(text="Downloading music... Please wait a moment.")

    try:
        # Start the download
        song_path = await download_song(video_url, video_id)
        
        # Send the downloaded song back
        await query.message.reply_audio(open(song_path, "rb"))
        os.remove(song_path)
    except Exception as e:
        await query.message.reply_text(f"Error downloading music: {e}")

# Main function to set up the bot
def main() -> None:
    # Create the application
    application = Application.builder().token(API_TOKEN).build()

    # Add command handler for /start
    application.add_handler(CommandHandler("start", start))

    # Add handler for regular text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Add handler for inline button press (search results)
    application.add_handler(CallbackQueryHandler(button_handler))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
