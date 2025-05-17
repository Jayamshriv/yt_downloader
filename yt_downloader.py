import sys
import os
import subprocess
import platform
import urllib.parse

# --- Configuration ---
VIDEO_URL = "https://www.youtube.com/watch?v=h2Xzq2fbafM"
DOWNLOAD_PATH = "D:/z_material/JAVA"  # Download directory

# Set this to the path of your ffmpeg executable if not in PATH
# Leave empty if ffmpeg is in your system PATH
FFMPEG_PATH = "E://ffmpeg"  # Example: "C:\\ffmpeg"

# Video quality options: 1080p, 720p, 480p, 360p, etc.
MAX_HEIGHT = "1080"  # Maximum height/resolution to download
# --- End Configuration ---

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

def download_video(url, output_path, max_height="1080", ffmpeg_path=""):
    """Download video using yt-dlp with specified quality."""
    # Create output directory if it doesn't exist
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    # Prepare the output template (Windows path handling)
    output_template = os.path.join(output_path, "%(title)s [%(id)s].%(ext)s")
    
    # Replace backslashes with forward slashes for command line
    output_template = output_template.replace("\\", "/")
    
    # Build the yt-dlp command
    cmd = ["yt-dlp"]
    
    # Add ffmpeg location if specified
    if ffmpeg_path:
        cmd.extend(["--ffmpeg-location", ffmpeg_path])
    
    # Add format selection
    format_string = f"bestvideo[ext=mp4][height<={max_height}]+bestaudio[ext=m4a]/best[ext=mp4][height<={max_height}]"
    cmd.extend(["-f", format_string])
    
    # Add output template
    cmd.extend(["-o", output_template])
    
    # Add verbose output
    cmd.append("-v")
    
    # Add the URL
    cmd.append(url)
    
    print("\nExecuting command:")
    print(" ".join(cmd))
    print("\nDownload progress:")
    
    # Execute the command
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
    print("--- YouTube Video Downloader using yt-dlp ---")
    
    # Check if yt-dlp is available
    if not check_requirements():
        print("Please install yt-dlp and try again.")
        sys.exit(1)
    
    # Validate the URL
    if not validate_url(VIDEO_URL):
        print("Please provide a valid YouTube URL.")
        sys.exit(1)
    
    print(f"Video URL: {VIDEO_URL}")
    print(f"Download path: {os.path.abspath(DOWNLOAD_PATH)}")
    print(f"Maximum resolution: {MAX_HEIGHT}p")
    
    # Start the download
    success = download_video(VIDEO_URL, DOWNLOAD_PATH, MAX_HEIGHT, FFMPEG_PATH)
    
    if success:
        print("\nVideo download process completed successfully.")
    else:
        print("\nVideo download process failed. Check the error messages above.")
    
    print("------------------------------------------------")