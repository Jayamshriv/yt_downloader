import sys
import os
from pytube import YouTube
from pytube.exceptions import PytubeError, VideoUnavailable
import time # To potentially add delays if needed
# /*
#  yt-dlp --ffmpeg-location "C:\ffmpeg" -f "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]" -o "D:\z_material\JAVA\%(title)s [%(id)s].%(ext)s" "https://www.youtube.com/watch?v=vMWvPN1R3yI"
# */
# --- Configuration ---
# VIDEO_URL = "https://www.youtube.com/watch?v=fmX84zu-5gs"
VIDEO_URL = "https://www.youtube.com/watch?v=vMWvPN1R3yI"
# Optional: Set a specific download path, otherwise it downloads to the script's directory
DOWNLOAD_PATH = "D:/z_material/JAVA"  # "." means current directory
# --- End Configuration ---

# --- Progress Callback ---
def on_progress(stream, chunk, bytes_remaining):
    """Callback function to show download progress."""
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage_of_completion = (bytes_downloaded / total_size) * 100
    # Use sys.stdout.write for better compatibility with '\r' (carriage return)
    # This overwrites the previous line in the console
    sys.stdout.write(f"\rDownloading: {percentage_of_completion:.1f}% Completed ({bytes_downloaded / (1024*1024):.2f}MB / {total_size / (1024*1024):.2f}MB)")
    sys.stdout.flush()
# --- End Progress Callback ---

def download_highest_quality(url, output_path):
    """
    Downloads the highest resolution progressive stream (video+audio combined)
    for the given YouTube URL.
    """
    try:
        print(f"Attempting to access video: {url}")
        # Register the progress callback function
        yt = YouTube(url, on_progress_callback=on_progress)

        print(f"\nVideo Title: {yt.title}")
        # Calculate and print video length
        hours = yt.length // 3600
        minutes = (yt.length % 3600) // 60
        seconds = yt.length % 60
        print(f"Video Length: {hours}h {minutes}m {seconds}s")

        print("\nSearching for the highest resolution progressive stream (MP4 preferred)...")

        # 1. Try to get the highest resolution progressive MP4 stream
        # Progressive streams have both video and audio
        # .order_by('resolution').desc() sorts by resolution descending
        # .first() gets the top one
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()

        # 2. If no MP4 progressive stream is found, get the highest resolution progressive of any type
        if not stream:
            print("No progressive MP4 stream found. Searching for any highest progressive stream...")
            stream = yt.streams.filter(progressive=True).order_by('resolution').desc().first()

        # 3. Check if *any* suitable stream was found
        if not stream:
            print("\nError: Could not find a suitable progressive stream with both video and audio.")
            print("Higher resolutions might require downloading video and audio separately (requires ffmpeg).")
            return False

        # Display stream details
        print(f"\nFound best progressive stream:")
        print(f"  Resolution: {stream.resolution}")
        print(f"  FPS: {stream.fps}")
        print(f"  Type: {stream.mime_type}")
        # Note: Filesize might be approximate or fail for very long/live streams initially
        try:
            filesize_gb = stream.filesize / (1024 * 1024 * 1024)
            print(f"  Approximate File Size: {filesize_gb:.2f} GB")
            print("\nWARNING: This is a very large file. Ensure you have enough disk space!")
        except Exception as e:
            print(f"  Could not accurately determine file size beforehand (Error: {e}). Be prepared for a large download.")


        print(f"\nStarting download to directory: '{os.path.abspath(output_path)}'")
        print("Progress will be shown below:")

        # Start the download
        stream.download(output_path=output_path)

        # Print a newline character after the progress bar finishes
        print("\n\nDownload finished successfully!")
        print(f"File saved as: {os.path.join(os.path.abspath(output_path), stream.default_filename)}")
        return True

    except VideoUnavailable:
        print(f"\nError: Video {url} is unavailable.")
        print("It might be private, deleted, age-restricted (without login), or region-restricted.")
        return False
    except PytubeError as e:
        print(f"\nAn error occurred with pytube: {e}")
        print("This could be due to YouTube API changes. Try updating pytube (`pip install --upgrade pytube`)")
        return False
    except Exception as e:
        # Catch any other unexpected errors (network issues, disk full, etc.)
        print(f"\nAn unexpected error occurred: {e}")
        return False

# --- Main Execution ---
if __name__ == "__main__":
    print("--- YouTube High-Quality Progressive Downloader ---")
    # Ensure the download directory exists
    if DOWNLOAD_PATH != "." and not os.path.exists(DOWNLOAD_PATH):
        print(f"Creating download directory: {DOWNLOAD_PATH}")
        os.makedirs(DOWNLOAD_PATH)

    success = download_highest_quality(VIDEO_URL, DOWNLOAD_PATH)

    if success:
        print("\nDownload process completed.")
    else:
        print("\nDownload process failed.")
    print("-------------------------------------------------")
# --- End Main Execution ---