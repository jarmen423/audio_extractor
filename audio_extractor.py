"""
Module: audio_extractor.py
Purpose: Extracts high-quality audio from MP4 video files.
Dependencies: moviepy
Role in Codebase: Standalone utility for preprocessing video-to-audio assets.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from moviepy import VideoFileClip

def extract_audio_from_video(video_path, output_ext="mp3", bitrate="192k"):
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

    Args:
        video_path (str): The local system path to the source MP4 file.
        output_ext (str): The desired audio format extension (e.g., "mp3", "wav"). 
                          Defaults to "mp3".

    Returns:
        str: The path to the successfully created audio file.

    Raises:
        FileNotFoundError: If the provided video_path does not exist.
        IOError: If the video file is corrupted or cannot be read.

    Key Technologies/APIs:
        - MoviePy: High-level Python library for video editing.
        - FFmpeg: The underlying engine used by MoviePy for codec processing.
    """

    # Generate output filename by swapping extension
    base_name = os.path.splitext(video_path)[0]
    output_path = f"{base_name}.{output_ext}"

    print(f"Loading video: {video_path}...")
    
    # Context manager ensures resources are closed properly
    with VideoFileClip(video_path) as video_clip:
        audio_clip = video_clip.audio
        print(f"Writing audio to: {output_path}...")
        audio_clip.write_audiofile(
            output_path,
            bitrate=bitrate,
            codec='libmp3lame'
        )
        
    return output_path

def run_gui():
    """
    initialize a tkinter window to handle file selection and processing
    """
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True) # bring to front

    # 1. open file picker
    file_path = filedialog.askopenfilename(
        title="select mp4 video for audio extractor",
        filetypes=[("Video Files", "*.mp4 *.mkv *.mov *.avi"), ("All Files", "*.*")]
    )
    if not file_path:
        print("no file selected. exiting.")
        return
    try:
        # 2. process file
        output_file = extract_audio_from_video(file_path, bitrate="192k")

        # 3. success message
        messagebox.showinfo("Success", f"Audio extracted successfully!\nSaved to: {output_file}")
    except Exception as e:
        messagebox.showerror("error", f"failed to extract audio:\n{str(e)}")
    root.destroy()

if __name__ == "__main__":
    run_gui()