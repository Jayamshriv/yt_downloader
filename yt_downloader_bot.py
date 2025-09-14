import os
import subprocess
import logging
import asyncio
import sys
import tempfile
import shutil
import hashlib
import json
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp
import requests

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = "7777439852:AAEYhS6yZs7xB9I_vlkPmk7N2Us88aH3e4U"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit for Telegram

# Store URL mappings to avoid long callback data
url_cache = {}

def update_ytdlp():
    """
    Update yt-dlp to the latest version using pip.
    
    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        print("🔄 Updating yt-dlp to latest version...")
        logger.info("Updating yt-dlp to latest version...")
        
        # First, uninstall the current version completely
        subprocess.run([
            sys.executable, "-m", "pip", "uninstall", "-y", "yt-dlp"
        ], capture_output=True, text=True, timeout=60)
        
        # Then install the latest version
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "--no-cache-dir", "yt-dlp"
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ yt-dlp updated successfully")
            logger.info("yt-dlp updated successfully")
            if result.stdout:
                logger.info(f"Update output: {result.stdout.strip()}")
            return True
        else:
            print("❌ Failed to update yt-dlp")
            logger.error(f"Failed to update yt-dlp: {result.stderr}")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Update timed out after 2 minutes")
        logger.error("yt-dlp update timed out after 120 seconds")
        return False
        
    except FileNotFoundError:
        print("❌ Python or pip not found in PATH")
        logger.error("Python executable not found")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error during update: {e}")
        logger.error(f"Error updating yt-dlp: {e}")
        return False

def check_ytdlp_installation():
    """Check if yt-dlp is properly installed and working."""
    try:
        import yt_dlp
        # Try to create a YoutubeDL instance to verify it's working
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            pass
        return True
    except ImportError:
        logger.error("yt-dlp is not installed")
        return False
    except Exception as e:
        logger.error(f"yt-dlp installation issue: {e}")
        return False
    
def generate_url_hash(url):
    """Generate a short hash for URL to use in callback data."""
    hash_object = hashlib.md5(url.encode())
    return hash_object.hexdigest()[:10]

class YouTubeDownloader:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temp directory: {self.temp_dir}")
    
    def get_video_info(self, url):
        """Get video information without downloading."""
        # Enhanced yt-dlp options to bypass restrictions
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
            'no_check_certificates': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['configs'],
                }
            },
            # Add headers to mimic browser requests
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Extracting info for URL: {url}")
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    logger.error("No info extracted from URL")
                    return None
                
                # Handle playlist
                if info.get('_type') == 'playlist':
                    entries = info.get('entries', [])
                    # Filter out None entries and limit for display
                    valid_entries = [entry for entry in entries if entry is not None]
                    limited_entries = valid_entries[:5] if len(valid_entries) > 5 else valid_entries
                    
                    return {
                        'title': info.get('title', 'Unknown Playlist'),
                        'uploader': info.get('uploader', 'Unknown'),
                        'playlist_count': len(valid_entries),
                        'is_playlist': True,
                        'entries': limited_entries,
                        'full_entries': valid_entries
                    }
                else:
                    return {
                        'title': info.get('title', 'Unknown'),
                        'duration': info.get('duration', 0),
                        'uploader': info.get('uploader', 'Unknown'),
                        'view_count': info.get('view_count', 0),
                        'upload_date': info.get('upload_date', 'Unknown'),
                        'is_playlist': False,
                        'id': info.get('id', ''),
                        'formats': info.get('formats', [])
                    }
                    
        except yt_dlp.DownloadError as e:
            logger.error(f"yt-dlp download error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return None
    
    def download_video(self, url, quality='best', audio_only=False):
        """Download video or audio with enhanced options."""
        filename_template = '%(title)s.%(ext)s'
        output_path = os.path.join(self.temp_dir, filename_template)
        
        # Enhanced yt-dlp options to bypass restrictions
        base_opts = {
            'outtmpl': output_path,
            'no_check_certificates': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['configs'],
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            },
            # Additional options to handle restrictions
            'writesubtitles': False,
            'writeautomaticsub': False,
            'ignoreerrors': False,
            'extract_flat': False,
        }
        
        if audio_only:
            ydl_opts = {
                **base_opts,
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
        else:
            # Format selection based on quality
            if quality == 'high':
                format_selector = 'best[height<=720][filesize<?50M]/bestvideo[height<=720]+bestaudio/best[height<=720]'
            elif quality == 'medium':
                format_selector = 'best[height<=480][filesize<?50M]/bestvideo[height<=480]+bestaudio/best[height<=480]'
            else:  # best
                format_selector = 'best[filesize<?50M]/bestvideo+bestaudio/best'
            
            ydl_opts = {
                **base_opts,
                'format': format_selector,
                'merge_output_format': 'mp4',
            }
        
        try:
            logger.info(f"Starting download: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
                # Find the downloaded file
                downloaded_files = []
                for file in os.listdir(self.temp_dir):
                    if file.endswith(('.mp4', '.mp3', '.webm', '.mkv', '.m4a')):
                        downloaded_files.append(file)
                
                if not downloaded_files:
                    logger.error("No downloaded files found")
                    return None, "Download completed but file not found."
                
                # Get the most recent file (in case of multiple)
                latest_file = max(downloaded_files, key=lambda f: os.path.getctime(os.path.join(self.temp_dir, f)))
                file_path = os.path.join(self.temp_dir, latest_file)
                file_size = os.path.getsize(file_path)
                
                logger.info(f"Downloaded file: {latest_file}, size: {file_size} bytes")
                
                if file_size > MAX_FILE_SIZE:
                    os.remove(file_path)
                    return None, f"File too large ({file_size/1024/1024:.1f}MB > 50MB). Try lower quality."
                
                if file_size == 0:
                    os.remove(file_path)
                    return None, "Downloaded file is empty."
                
                return file_path, None
                        
        except yt_dlp.DownloadError as e:
            error_msg = str(e)
            logger.error(f"yt-dlp download error: {error_msg}")
            if "HTTP Error 403" in error_msg:
                return None, "❌ Video is restricted or unavailable. Try another video."
            elif "Private video" in error_msg:
                return None, "❌ This video is private."
            elif "Video unavailable" in error_msg:
                return None, "❌ Video is unavailable."
            elif "Sign in to confirm your age" in error_msg:
                return None, "❌ Video requires age verification."
            else:
                return None, f"❌ Download failed: {error_msg[:100]}..."
                
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None, f"❌ Unexpected error: {str(e)[:100]}..."
    
    def cleanup(self):
        """Clean up temporary files."""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temp directory: {self.temp_dir}")
            self.temp_dir = tempfile.mkdtemp()  # Create new temp dir
            logger.info(f"Created new temp directory: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

# Global downloader instance
downloader = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler."""
    welcome_message = """
🎥 **Welcome to YouTube Downloader Bot!**

📝 **How to use:**
1. Send me a YouTube URL
2. Choose your preferred format
3. Wait for download to complete

🎯 **Supported:**
• Single videos
• Playlists (first 3 videos)
• Audio extraction (MP3)
• Multiple quality options

⚠️ **Limitations:**
• Max file size: 50MB
• Some videos may be restricted
• Processing time: 1-3 minutes

Just send me a YouTube URL to get started! 🚀
"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command handler."""
    help_text = """
🔧 **Bot Commands:**

/start - Welcome message
/help - Show this help

🎬 **Download Options:**
• **Best Quality** - Highest available quality
• **High Quality** - 720p maximum
• **Medium Quality** - 480p maximum  
• **Audio Only** - MP3 format

📋 **Playlist Support:**
• Downloads first 3 videos automatically
• Each video processed separately
• Audio-only option available

⚠️ **Important Notes:**
• Maximum file size: 50MB per file
• Some videos may be geo-restricted
• Private videos cannot be downloaded
• Processing may take a few minutes

🆘 **Troubleshooting:**
If a video fails to download, try:
1. Different quality option
2. Another video
3. Check if video is public
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

def create_quality_keyboard(url_hash, is_playlist=False, playlist_count=0):
    """Create inline keyboard for quality selection using URL hash."""
    keyboard = []
    
    if is_playlist:
        keyboard.append([InlineKeyboardButton(
            f"📹 Download Videos (First 3 of {playlist_count})", 
            callback_data=f"pl_vid_{url_hash}"
        )])
        keyboard.append([InlineKeyboardButton(
            f"🎵 Download Audio (First 3 of {playlist_count})", 
            callback_data=f"pl_aud_{url_hash}"
        )])
    else:
        keyboard.append([InlineKeyboardButton("📹 Best Quality", callback_data=f"vid_best_{url_hash}")])
        keyboard.append([InlineKeyboardButton("📹 High (720p)", callback_data=f"vid_high_{url_hash}")])
        keyboard.append([InlineKeyboardButton("📹 Medium (480p)", callback_data=f"vid_med_{url_hash}")])
        keyboard.append([InlineKeyboardButton("🎵 Audio Only", callback_data=f"aud_{url_hash}")])
    
    return InlineKeyboardMarkup(keyboard)

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle YouTube URL messages."""
    global downloader
    
    if not downloader:
        await update.message.reply_text("❌ Downloader not initialized. Please restart the bot.")
        return
    
    url = update.message.text.strip()
    
    # Basic URL validation
    if not any(domain in url.lower() for domain in ['youtube.com', 'youtu.be', 'youtube']):
        await update.message.reply_text("❌ Please send a valid YouTube URL.")
        return
    
    # Generate hash for URL and store it
    url_hash = generate_url_hash(url)
    url_cache[url_hash] = url
    
    # Show processing message
    processing_msg = await update.message.reply_text("🔍 Analyzing URL... Please wait.")
    
    try:
        # Get video info
        info = downloader.get_video_info(url)
        if not info:
            await processing_msg.edit_text("❌ Could not retrieve video information. The video might be:\n• Private or restricted\n• Unavailable in your region\n• Deleted\n• Age-restricted\n\nPlease try another video.")
            return
        
        if info['is_playlist']:
            playlist_count = info['playlist_count']
            info_text = f"""
🎬 **Playlist Information**

📋 **Title:** {info['title'][:60]}{'...' if len(info['title']) > 60 else ''}
👤 **Channel:** {info['uploader']}
📊 **Total Videos:** {playlist_count}

⚠️ **Note:** Due to size limits, only first 3 videos will be downloaded.

Choose download option:
"""
        else:
            # Format duration and views
            duration = info.get('duration', 0)
            duration_str = f"{duration//60}:{duration%60:02d}" if duration else "Unknown"
            
            views = info.get('view_count', 0)
            views_str = f"{views:,}" if views else "Unknown"
            
            info_text = f"""
🎬 **Video Information**

📋 **Title:** {info['title'][:60]}{'...' if len(info['title']) > 60 else ''}
👤 **Channel:** {info['uploader']}
⏱️ **Duration:** {duration_str}
👁️ **Views:** {views_str}

Choose download quality:
"""
        
        keyboard = create_quality_keyboard(
            url_hash, 
            info['is_playlist'], 
            info.get('playlist_count', 0)
        )
        await processing_msg.edit_text(info_text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"URL handling error: {e}")
        await processing_msg.edit_text("❌ An error occurred while processing the URL. Please try again or use a different video.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button presses."""
    query = update.callback_query
    await query.answer()
    
    try:
        # Parse callback data
        parts = query.data.split('_')
        if len(parts) < 2:
            await query.edit_message_text("❌ Invalid selection.")
            return
        
        url_hash = parts[-1]  # Last part is always the hash
        url = url_cache.get(url_hash)
        
        if not url:
            await query.edit_message_text("❌ Session expired. Please send the URL again.")
            return
        
        # Determine action
        if query.data.startswith('pl_'):
            # Playlist download
            is_audio = 'aud' in query.data
            await download_playlist(query, url, is_audio, context)
        else:
            # Single video download
            is_audio = query.data.startswith('aud_')
            quality = 'best'  # default
            
            if 'high' in query.data:
                quality = 'high'
            elif 'med' in query.data:
                quality = 'medium'
            
            await download_single(query, url, quality, is_audio)
            
    except Exception as e:
        logger.error(f"Button callback error: {e}")
        await query.edit_message_text("❌ An error occurred. Please try again.")

async def download_single(query, url, quality, is_audio):
    """Download a single video/audio."""
    global downloader
    
    await query.edit_message_text("⬇️ Starting download... This may take 1-3 minutes.")
    
    try:
        file_path, error = downloader.download_video(url, quality, is_audio)
        
        if error:
            await query.edit_message_text(error)
            return
        
        if not file_path or not os.path.exists(file_path):
            await query.edit_message_text("❌ Download failed or file not found.")
            return
        
        # Send the file
        await send_file(query, file_path, is_audio)
        
    except Exception as e:
        logger.error(f"Single download error: {e}")
        await query.edit_message_text(f"❌ Download failed: {str(e)[:100]}...")

async def download_playlist(query, url, is_audio, context):
    """Download playlist (first 3 videos)."""
    global downloader
    
    await query.edit_message_text("📋 Processing playlist... Downloading first 3 videos.")
    
    try:
        # Get playlist info
        info = downloader.get_video_info(url)
        if not info or not info['is_playlist']:
            await query.edit_message_text("❌ Could not process playlist.")
            return
        
        entries = info.get('entries', [])[:3]  # Limit to first 3
        successful_downloads = 0
        
        for i, entry in enumerate(entries):
            if not entry:
                continue
                
            video_url = entry.get('url') or f"https://youtube.com/watch?v={entry.get('id')}"
            video_title = entry.get('title', f'Video {i+1}')
            
            await query.edit_message_text(f"⬇️ Downloading {i+1}/3: {video_title[:50]}...")
            
            file_path, error = downloader.download_video(video_url, 'best', is_audio)
            
            if error:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"❌ Failed to download '{video_title}': {error}"
                )
                continue
            
            if file_path and os.path.exists(file_path):
                success = await send_file_to_chat(query.message.chat_id, file_path, is_audio, context)
                if success:
                    successful_downloads += 1
        
        if successful_downloads > 0:
            await query.edit_message_text(f"✅ Playlist download completed! Successfully downloaded {successful_downloads}/3 videos.")
        else:
            await query.edit_message_text("❌ All playlist downloads failed.")
        
    except Exception as e:
        logger.error(f"Playlist download error: {e}")
        await query.edit_message_text(f"❌ Playlist download failed: {str(e)[:100]}...")

async def send_file(query, file_path, is_audio):
    """Send file through query edit."""
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    
    await query.edit_message_text(f"📤 Uploading {file_name[:30]}... ({file_size/1024/1024:.1f}MB)")
    
    try:
        with open(file_path, 'rb') as file:
            if is_audio:
                await query.message.reply_audio(
                    audio=file,
                    title=file_name.replace('.mp3', ''),
                    caption="🎵 Downloaded audio"
                )
            else:
                await query.message.reply_video(
                    video=file,
                    caption="🎬 Downloaded video"
                )
        
        await query.edit_message_text("✅ Download completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"File send error: {e}")
        await query.edit_message_text("❌ Failed to send file. It might be too large.")
        return False
    finally:
        # Clean up file
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"File cleanup error: {e}")

async def send_file_to_chat(chat_id, file_path, is_audio, context):
    """Send file directly to chat."""
    try:
        with open(file_path, 'rb') as file:
            if is_audio:
                await context.bot.send_audio(
                    chat_id=chat_id,
                    audio=file,
                    caption="🎵 Downloaded audio"
                )
            else:
                await context.bot.send_video(
                    chat_id=chat_id,
                    video=file,
                    caption="🎬 Downloaded video"
                )
        return True
    except Exception as e:
        logger.error(f"File send error: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Failed to send file. It might be too large."
        )
        return False
    finally:
        # Clean up file
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"File cleanup error: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Main function to run the bot."""
    global downloader
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Please set your bot token in the BOT_TOKEN variable!")
        print("Get your token from @BotFather on Telegram")
        return
    
    print("🔍 Checking yt-dlp installation...")
    if not check_ytdlp_installation():
        print("🔄 yt-dlp not working properly, attempting to fix...")
        if update_ytdlp():
            print("✅ yt-dlp updated successfully")
            if not check_ytdlp_installation():
                print("❌ yt-dlp still not working after update")
                return
        else:
            print("❌ Could not fix yt-dlp installation")
            return
    else:
        print("✅ yt-dlp is working properly")
    
    # Initialize downloader
    try:
        downloader = YouTubeDownloader()
        print("✅ Downloader initialized")
    except Exception as e:
        print(f"❌ Failed to initialize downloader: {e}")
        return
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_error_handler(error_handler)
    
    print("🤖 Bot is starting...")
    print("Press Ctrl+C to stop the bot")
    
    # Run the bot
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Bot error: {e}")
        print(f"❌ Bot error: {e}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Critical error: {e}")
        logger.error(f"Critical error: {e}")
    finally:
        if downloader:
            downloader.cleanup()
        print("🧹 Cleanup completed")