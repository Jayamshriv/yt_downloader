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
        # Check if yt-dlp is available
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
            print(result.stdout)
            return True
        else:
            print("Failed to update yt-dlp with pip")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"Error updating yt-dlp: {e}")
        return False

def download_video_simple(url, output_path, ffmpeg_path=""):
    """Download video using the simplest method that works with HLS."""
    # Create output directory if it doesn't exist
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    # Prepare the output template
    output_template = os.path.join(output_path, "%(title)s [%(id)s].%(ext)s")
    output_template = output_template.replace("\\", "/")
    
    # Build the command - simplified approach
    cmd = ["yt-dlp"]
    
    # Add ffmpeg location if specified
    if ffmpeg_path:
        cmd.extend(["--ffmpeg-location", ffmpeg_path])
    
    # Don't specify format - let yt-dlp choose the best available
    # This works better with HLS streams
    
    # Add output template
    cmd.extend(["-o", output_template])
    
    # Add useful options
    cmd.extend([
        "--no-playlist",
        "--ignore-errors",
        "--embed-subs",
        "--write-auto-sub",
        "--merge-output-format", "mp4"  # Ensure final output is mp4
    ])
    
    # Add the URL
    cmd.append(url)
    
    print(f"\nDownloading with simplified command:")
    print(" ".join(cmd))
    print("\nDownload progress:")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Print output in real-time
        for line in process.stdout:
            print(line, end='')
        
        # Wait for the process to complete
        process.wait()
        
        if process.returncode == 0:
            print("\nDownload completed successfully!")
            return True
        else:
            print(f"\nDownload failed with return code {process.returncode}")
            return False
            
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        return False

def download_video_specific_format(url, output_path, ffmpeg_path=""):
    """Download video using specific format IDs from the available list."""
    # Create output directory if it doesn't exist
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    # Prepare the output template
    output_template = os.path.join(output_path, "%(title)s [%(id)s].%(ext)s")
    output_template = output_template.replace("\\", "/")
    
    # Format options based on the available formats shown in your log
    # Format IDs: 614 (1080p), 609 (720p), 606 (480p), 233/234 (audio)
    format_options = [
        "614+233",  # 1080p VP9 + audio
        "270+233",  # 1080p AVC + audio  
        "609+233",  # 720p VP9 + audio
        "232+233",  # 720p AVC + audio
        "614",      # 1080p video only
        "270",      # 1080p video only (AVC)
        "609",      # 720p video only
    ]
    
    for format_id in format_options:
        print(f"\nTrying format: {format_id}")
        
        cmd = ["yt-dlp"]
        
        if ffmpeg_path:
            cmd.extend(["--ffmpeg-location", ffmpeg_path])
        
        cmd.extend([
            "-f", format_id,
            "-o", output_template,
            "--no-playlist",
            "--ignore-errors",
            "--merge-output-format", "mp4",
            url
        ])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Download successful with format {format_id}!")
                print(result.stdout)
                return True
            else:
                print(f"Format {format_id} failed: {result.stderr}")
                
        except Exception as e:
            print(f"Error with format {format_id}: {e}")
    
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

# --- Main Execution ---
if __name__ == "__main__":
    print("--- YouTube Video Downloader using yt-dlp (HLS-Compatible Version) ---")
    
    # Check if yt-dlp is available
    if not check_requirements():
        print("Please install yt-dlp and try again.")
        sys.exit(1)
    
    # Try to update yt-dlp
    print("\nTrying to update yt-dlp...")
    if not update_ytdlp():
        print("Warning: Could not update yt-dlp. Continuing with current version...")
    
    # Validate the URL
    if not validate_url(VIDEO_URL):
        print("Please provide a valid YouTube URL.")
        sys.exit(1)
    
    print(f"\nVideo URL: {VIDEO_URL}")
    print(f"Download path: {os.path.abspath(DOWNLOAD_PATH)}")
    print(f"Maximum resolution: {MAX_HEIGHT}p")
    
    # Try the simple approach first (recommended)
    print("\n=== Attempting simple download (recommended) ===")
    success = download_video_simple(VIDEO_URL, DOWNLOAD_PATH, FFMPEG_PATH)
    
    if not success:
        print("\n=== Simple download failed, trying specific formats ===")
        success = download_video_specific_format(VIDEO_URL, DOWNLOAD_PATH, FFMPEG_PATH)
    
    if success:
        print("\nVideo download completed successfully!")
        print("Check your download folder for the video file.")
    else:
        print("\nAll download attempts failed.")
        print("\nManual command to try:")
        print(f'yt-dlp --ffmpeg-location "{FFMPEG_PATH}" -o "{DOWNLOAD_PATH}/%(title)s [%(id)s].%(ext)s" "{VIDEO_URL}"')
    
    print("------------------------------------------------")