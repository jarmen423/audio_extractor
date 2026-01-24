"""
Module: audio_extractor.py
Purpose: Extracts high-quality audio from MP4 video files and URLs using yt-dlp and MoviePy.
Dependencies: moviepy, yt-dlp
Role in Codebase: Standalone utility for preprocessing video-to-audio assets.
"""

import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from urllib.parse import urlparse
import urllib.error
from moviepy import VideoFileClip
import yt_dlp
import imageio_ffmpeg

# Constants
DEFAULT_BITRATE = '192k'
TEMP_FILENAME_PREFIX = 'downloaded_'
DEFAULT_OUTPUT_EXT = 'mp3'
VIDEO_EXTENSIONS = ['.mp4', '.mkv', '.mov', '.avi', '.webm']
TEMP_DOWNLOAD_DIR = 'temp_downloads'


def is_valid_url(url):
    """
    Validates the format of a URL.

    Summary:
        Checks if a string is a properly formatted URL with scheme and netloc.

    Extended Description (Deep Education):
        URL validation is crucial for security and error prevention. A valid URL must
        have a scheme (e.g., http, https) and a network location (netloc). The
        urlparse function from urllib.parse parses URLs into components, allowing
        us to validate the structure without making network requests.

    Contextual Purpose (Project Role):
        This utility function provides input validation for URL-based operations,
        preventing invalid URLs from causing errors in downstream processing.

    Args:
        url (str): The URL string to validate.

    Returns:
        bool: True if the URL is valid, False otherwise.

    Raises:
        None (returns False for invalid input).

    Key Technologies/APIs:
        - urllib.parse.urlparse: Python's standard library for URL parsing.
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except (ValueError, AttributeError):
        return False


def extract_audio_from_video(video_path, output_ext=DEFAULT_OUTPUT_EXT, bitrate=DEFAULT_BITRATE):
    """
    Extracts the audio track from a video file and saves it as a standalone file.

    Summary:
        Loads a video file using MoviePy, isolates the audio stream, and 
        writes it to a new file in the specified format.

    Extended Description (Deep Education):
        MoviePy uses the VideoFileClip object to read the video container (MP4). 
        The .audio attribute provides access to the underlying audio stream without 
        needing to manually decode the video frames. By using write_audiofile, 
        we invoke FFmpeg under the hood to transcode that stream into a common 
        format like MP3 or WAV.

    Contextual Purpose (Project Role):
        This function serves as the core audio extraction utility used by both 
        the GUI interface and command-line workflows to convert video assets 
        into standalone audio files for further processing.

    Args:
        video_path (str): The local system path to the source video file.
        output_ext (str): The desired audio format extension (e.g., "mp3", "wav"). 
                          Defaults to "mp3".
        bitrate (str): The audio bitrate for the output file (e.g., "192k", "320k"). 
                       Defaults to "192k".

    Returns:
        str: The path to the successfully created audio file.

    Raises:
        FileNotFoundError: If the provided video_path does not exist.
        ValueError: If the video file has no audio track or is invalid.
        IOError: If the video file is corrupted or cannot be read.

    Key Technologies/APIs:
        - MoviePy: High-level Python library for video editing.
        - FFmpeg: The underlying engine used by MoviePy for codec processing.
    """
    # Validate input file exists
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Validate file extension
    _, ext = os.path.splitext(video_path)
    if ext.lower() not in VIDEO_EXTENSIONS:
        raise ValueError(f"Unsupported video format: {ext}. Supported formats: {', '.join(VIDEO_EXTENSIONS)}")

    # Generate output filename by swapping extension
    base_name = os.path.splitext(video_path)[0]
    output_path = f"{base_name}.{output_ext}"

    print(f"Loading video: {video_path}...")
    
    # Context manager ensures resources are closed properly
    with VideoFileClip(video_path) as video_clip:
        # Check if video has audio
        if video_clip.audio is None:
            raise ValueError("The video file does not contain an audio track")
        
        audio_clip = video_clip.audio
        print(f"Writing audio to: {output_path}...")
        audio_clip.write_audiofile(
            output_path,
            bitrate=bitrate,
            codec='libmp3lame'
        )
        
    return output_path

def download_media_from_url(url, output_dir=TEMP_DOWNLOAD_DIR):
    """
    Downloads video/audio from URL to local temp file.

    Summary:
        Uses yt-dlp to download media from various platforms including YouTube,
        Twitch, TikTok, Instagram, and more. Handles authentication, playlist
        downloading, and format selection. Library uses FFmpeg internally for
        downloading and transcoding.

    Extended Description (Deep Education):
        yt-dlp is a fork of youtube-dl that supports 1000+ platforms. It uses
        FFmpeg under the hood to merge video and audio streams when downloading
        formats like 'bestvideo+bestaudio'. The tool can handle authentication
        for private content, playlist downloads, and format selection. The
        download process is asynchronous and provides detailed information about
        the media being downloaded.

    Contextual Purpose (Project Role):
        This nested function provides the core download functionality for the
        URL-based extraction workflow, ensuring that all downloaded media is
        properly handled and returned as an absolute file path.

    Args:
        url (str): URL to the content.
        output_dir (str): Directory to save downloaded files. Defaults to
                            TEMP_DOWNLOAD_DIR constant.

    Returns:
        str: Absolute path to the downloaded file.

    Raises:
        ValueError: If URL is invalid or download fails.
        RuntimeError: If yt-dlp is not installed or fails to download.

    Key Technologies/APIs:
        - yt_dlp.YoutubeDL: Python wrapper for yt-dlp functionality.
        - FFmpeg: Underlying engine used by yt-dlp for media processing.
    """
    # Validate URL format
    if not is_valid_url(url):
        raise ValueError(f"Invalid URL format: {url}")

    # Create temp directory
    os.makedirs(output_dir, exist_ok=True)

    # Generate unique filename using constant
    temp_filename = f'{TEMP_FILENAME_PREFIX}{int(time.time())}.%(ext)s'
    output_template = os.path.join(output_dir, temp_filename)

    # yt-dlp options
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'ffmpeg_location': imageio_ffmpeg.get_ffmpeg_exe(),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # Get the actual downloaded filename
            downloaded_file = ydl.prepare_filename(info)

            # Handle case where extension might be different
            if not os.path.exists(downloaded_file):
                # Find the actual file
                files = [f for f in os.listdir(output_dir) 
                        if f.startswith(os.path.basename(downloaded_file))]
                if files:
                    downloaded_file = os.path.join(output_dir, files[0])

            # Validate downloaded file path
            if not os.path.isabs(downloaded_file):
                downloaded_file = os.path.abspath(downloaded_file)

            return downloaded_file

    except (yt_dlp.utils.DownloadError, ValueError, urllib.error.URLError) as e:
        raise RuntimeError(f'Failed to download media from URL: {str(e)}')
    except Exception as e:
        raise RuntimeError(f'Unexpected error during download: {str(e)}')        
def run_gui():
    """
    Initializes a tkinter window to handle file selection and processing.
    Detects if input is URL or local file path and routes to appropriate extraction method.

    Summary:
        Creates a GUI dialog that asks users whether they want to extract audio from
        a URL or a local file, then processes the input accordingly.

    Extended Description (Deep Education):
        The GUI uses tkinter's messagebox and dialog widgets to create a user-friendly
        interface. The askyesno dialog provides a simple Yes/No choice for input type.
        For URL input, simpledialog.askstring prompts for the URL. For file input,
        filedialog.askopenfilename provides a file picker dialog. The GUI then delegates
        to the appropriate extraction function based on user selection.

    Contextual Purpose (Project Role):
        This function serves as the main entry point for the GUI interface, providing
        a user-friendly way to access the audio extraction functionality without
        requiring command-line usage.

    Args:
        None.

    Returns:
        None (GUI runs until closed by user).

    Raises:
        None (all exceptions are caught and displayed to user).

    Key Technologies/APIs:
        - tkinter: Python's standard GUI library.
        - messagebox: tkinter widget for user notifications.
        - filedialog: tkinter widget for file selection dialogs.
        - simpledialog: tkinter widget for simple text input dialogs.
    """
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)  # Bring to front

    # Ask if input is URL or file
    input_type = messagebox.askyesno(
        "Input Type",
        "Extract from URL?\n\nYes = URL (YouTube, Twitch, etc)\nNo = Local File"
    )

    if input_type:
        # URL input
        url = simpledialog.askstring(
            'URL Input',
            'Enter the video/audio clip URL:',
            parent=root
        )

        if not url:
            print('No URL provided. Exiting.')
            return

        try:
            # Download first
            downloaded_file = download_media_from_url(url)
            # Then extract audio
            output_file = extract_audio_from_video(downloaded_file, bitrate=DEFAULT_BITRATE)

            # Clean up downloaded file (only if it's not the same as output)
            if downloaded_file != output_file and os.path.exists(downloaded_file):
                try:
                    os.remove(downloaded_file)
                except OSError as e:
                    print(f"Warning: Could not cleanup temp file: {e}")

            messagebox.showinfo('Success', f'Audio extracted successfully!\nSaved to: {output_file}')

        except (ValueError, RuntimeError) as e:
            messagebox.showerror('Error', f'Failed to extract audio:\n{str(e)}')
        except Exception as e:
            messagebox.showerror('Error', f'Unexpected error:\n{str(e)}')

    else:
        # File input
        file_path = filedialog.askopenfilename(
            title="Select video for audio extractor",
            filetypes=[("Video Files", " ".join([f"*{ext}" for ext in VIDEO_EXTENSIONS])), ("All Files", "*.*")]
        )

        if not file_path:
            print("No file selected. Exiting.")
            return

        try:
            # Process file
            output_file = extract_audio_from_video(file_path, bitrate=DEFAULT_BITRATE)

            # Success message
            messagebox.showinfo("Success", f"Audio extracted successfully!\nSaved to: {output_file}")

        except (FileNotFoundError, ValueError, IOError) as e:
            messagebox.showerror("Error", f"Failed to extract audio:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")

    root.destroy()

if __name__ == "__main__":
    run_gui()