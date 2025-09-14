import sys
import os
import subprocess
import platform
import urllib.parse

# --- Configuration ---
VIDEO_URL = "https://www.youtube.com/watch?v=-1GB6m39-rM"
DOWNLOAD_PATH = "D:/z_material/JAVA" 
FFMPEG_PATH = "E://ffmpeg"  
MAX_HEIGHT = "1080"  

def check_requirements():
    """Check if yt-dlp is installed and available."""
    try:
        result = subprocess.run(
            ["yt-dlp", "--version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            print(f"yt-dlp version: {result.stdout.strip()}")
            return True
        else:
            print("yt-dlp not found. Please install it with: pip install yt-dlp")
            return False
    except FileNotFoundError:
        print("yt-dlp not found. Please install it with: pip install yt-dlp")
        return False

def update_ytdlp():
    """Update yt-dlp to the latest version using pip."""
    print("Updating yt-dlp to the latest version using pip...")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("yt-dlp updated successfully")
            return True
        else:
            print("Failed to update yt-dlp with pip")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"Error updating yt-dlp: {e}")
        return False

def validate_url(url):
    """Validate that the URL is a proper YouTube URL."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.netloc in ('www.youtube.com', 'youtube.com', 'youtu.be'):
            return True
        print(f"Invalid YouTube URL: {url}")
        return False
    except:
        print(f"Invalid URL format: {url}")
        return False

def download_single_video(url, output_path, ffmpeg_path="", max_height="1080"):
    """Download a single video with audio in best quality up to specified height."""
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    output_template = os.path.join(output_path, "%(title)s [%(id)s].%(ext)s")
    output_template = output_template.replace("\\", "/")
    
    cmd = ["yt-dlp"]
    
    if ffmpeg_path:
        cmd.extend(["--ffmpeg-location", ffmpeg_path])
    
    # Format selection for best video+audio up to max height
    format_selector = f"bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]"
    
    cmd.extend([
        "-f", format_selector,
        "-o", output_template,
        "--no-playlist",
        "--ignore-errors",
        "--embed-subs",
        "--write-auto-sub",
        "--merge-output-format", "mp4",
        url
    ])
    
    return execute_download(cmd, "Single Video Download")

def download_single_audio(url, output_path, ffmpeg_path=""):
    """Download only audio from a single video."""
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    output_template = os.path.join(output_path, "%(title)s [%(id)s].%(ext)s")
    output_template = output_template.replace("\\", "/")
    
    cmd = ["yt-dlp"]
    
    if ffmpeg_path:
        cmd.extend(["--ffmpeg-location", ffmpeg_path])
    
    cmd.extend([
        "-f", "bestaudio/best",
        "-o", output_template,
        "--no-playlist",
        "--ignore-errors",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",  # Best quality
        url
    ])
    
    return execute_download(cmd, "Single Audio Download")

def download_playlist_videos(url, output_path, ffmpeg_path="", max_height="1080"):
    """Download all videos from a playlist with audio."""
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    # Create playlist subfolder
    playlist_path = os.path.join(output_path, "Playlist_Videos")
    if not os.path.exists(playlist_path):
        os.makedirs(playlist_path)
    
    output_template = os.path.join(playlist_path, "%(playlist_index)02d - %(title)s [%(id)s].%(ext)s")
    output_template = output_template.replace("\\", "/")
    
    cmd = ["yt-dlp"]
    
    if ffmpeg_path:
        cmd.extend(["--ffmpeg-location", ffmpeg_path])
    
    format_selector = f"bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]"
    
    cmd.extend([
        "-f", format_selector,
        "-o", output_template,
        "--yes-playlist",
        "--ignore-errors",
        "--embed-subs",
        "--write-auto-sub",
        "--merge-output-format", "mp4",
        url
    ])
    
    return execute_download(cmd, "Playlist Video Download")

def download_playlist_audio(url, output_path, ffmpeg_path=""):
    """Download only audio from all videos in a playlist."""
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    # Create playlist audio subfolder
    playlist_path = os.path.join(output_path, "Playlist_Audio")
    if not os.path.exists(playlist_path):
        os.makedirs(playlist_path)
    
    output_template = os.path.join(playlist_path, "%(playlist_index)02d - %(title)s [%(id)s].%(ext)s")
    output_template = output_template.replace("\\", "/")
    
    cmd = ["yt-dlp"]
    
    if ffmpeg_path:
        cmd.extend(["--ffmpeg-location", ffmpeg_path])
    
    cmd.extend([
        "-f", "bestaudio/best",
        "-o", output_template,
        "--yes-playlist",
        "--ignore-errors",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",  # Best quality
        url
    ])
    
    return execute_download(cmd, "Playlist Audio Download")

def execute_download(cmd, download_type):
    """Execute the download command and handle output."""
    print(f"\n=== {download_type} ===")
    print(f"Command: {' '.join(cmd)}")
    print("\nDownload progress:")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        for line in process.stdout:
            print(line, end='')
        
        process.wait()
        
        if process.returncode == 0:
            print(f"\n{download_type} completed successfully!")
            return True
        else:
            print(f"\n{download_type} failed with return code {process.returncode}")
            return False
            
    except Exception as e:
        print(f"\nAn error occurred during {download_type}: {e}")
        return False

def display_menu():
    """Display the download options menu."""
    print("\n" + "="*60)
    print("YouTube Downloader - Choose your option:")
    print("="*60)
    print("1. Download single video with audio (best quality)")
    print("2. Download single video - audio only (MP3)")
    print("3. Download playlist - all videos with audio")
    print("4. Download playlist - audio only (MP3)")
    print("5. Exit")
    print("="*60)

def get_user_choice():
    """Get and validate user choice."""
    while True:
        try:
            choice = int(input("\nEnter your choice (1-5): "))
            if 1 <= choice <= 5:
                return choice
            else:
                print("Please enter a number between 1 and 5.")
        except ValueError:
            print("Please enter a valid number.")

def get_url_input():
    """Get URL input from user."""
    while True:
        try:
            url = input("\nEnter YouTube URL: ").strip()
            if url:  # Make sure URL is not empty
                return url
            else:
                print("URL cannot be empty. Please enter a valid YouTube URL.")
        except EOFError:
            print("\nInput error. Please try again.")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            sys.exit(0)

def is_playlist_url(url):
    """Check if the URL is a playlist URL."""
    return 'list=' in url or 'playlist' in url.lower()

# --- Main Execution ---
if __name__ == "__main__":
    print("--- Enhanced YouTube Video Downloader using yt-dlp ---")
    
    # Check if yt-dlp is available
    if not check_requirements():
        print("Please install yt-dlp and try again.")
        sys.exit(1)
    
    # Try to update yt-dlp
    print("\nTrying to update yt-dlp...")
    if not update_ytdlp():
        print("Warning: Could not update yt-dlp. Continuing with current version...")
    
    print(f"\nDefault download path: {os.path.abspath(DOWNLOAD_PATH)}")
    print(f"Maximum video resolution: {MAX_HEIGHT}p")
    
    while True:
        display_menu()
        choice = get_user_choice()
        
        if choice == 5:
            print("Goodbye!")
            break
        
        url = get_url_input()
        
        # Validate the URL
        if not validate_url(url):
            print("Please provide a valid YouTube URL.")
            continue
        
        success = False
        
        if choice == 1:
            # Single video with audio
            if is_playlist_url(url):
                print("Warning: Playlist URL detected, but downloading only the first video.")
                url += "&index=1"
            success = download_single_video(url, DOWNLOAD_PATH, FFMPEG_PATH, MAX_HEIGHT)
            
        elif choice == 2:
            # Single audio only
            if is_playlist_url(url):
                print("Warning: Playlist URL detected, but downloading only the first video's audio.")
                url += "&index=1"
            success = download_single_audio(url, DOWNLOAD_PATH, FFMPEG_PATH)
            
        elif choice == 3:
            # Playlist videos
            if not is_playlist_url(url):
                print("Warning: This doesn't appear to be a playlist URL.")
                print("If it's a single video, it will be downloaded to the playlist folder.")
            success = download_playlist_videos(url, DOWNLOAD_PATH, FFMPEG_PATH, MAX_HEIGHT)
            
        elif choice == 4:
            # Playlist audio
            if not is_playlist_url(url):
                print("Warning: This doesn't appear to be a playlist URL.")
                print("If it's a single video, its audio will be downloaded to the playlist folder.")
            success = download_playlist_audio(url, DOWNLOAD_PATH, FFMPEG_PATH)
        
        if success:
            print(f"\nDownload completed successfully!")
            print(f"Files saved to: {os.path.abspath(DOWNLOAD_PATH)}")
        else:
            print(f"\nDownload failed. Please check the URL and try again.")
            
        # Ask if user wants to continue
        continue_choice = input("\nDo you want to download something else? (y/n): ").lower().strip()
        if continue_choice not in ['y', 'yes']:
            print("Goodbye!")
            break
    
    print("\n" + "="*60)