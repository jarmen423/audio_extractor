"""
Module: video_extractor.py
Purpose: Extracts high-quality video from video files, removing all audio streams.
Dependencies: moviepy
Role in Codebase: Standalone utility for preprocessing video assets by removing audio tracks.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from moviepy import VideoFileClip

def extract_video_without_audio(video_path, output_ext="mp4", codec="libx264"):
    """
    Extracts the video track from a video file and saves it as a standalone file without audio.

    Summary:
        Loads a video file using MoviePy, removes the audio stream, and 
        writes the video-only content to a new file in the specified format.

    Extended Description (Deep Education):
        MoviePy uses the VideoFileClip object to read the video container. 
        By setting the .audio attribute to None, we remove all audio streams from the clip. 
        The write_videofile method then uses FFmpeg under the hood to encode the 
        video track into the desired format with specified codec parameters.

    Args:
        video_path (str): The local system path to the source video file.
        output_ext (str): The desired video format extension (e.g., "mp4", "mkv"). 
                          Defaults to "mp4".
        codec (str): The video codec to use for encoding (e.g., "libx264", "libx265").
                      Defaults to "libx264" for high compatibility.

    Returns:
        str: The path to the successfully created video-only file.

    Raises:
        FileNotFoundError: If the provided video_path does not exist.
        IOError: If the video file is corrupted or cannot be read.

    Key Technologies/APIs:
        - MoviePy: High-level Python library for video editing.
        - FFmpeg: The underlying engine used by MoviePy for codec processing.
        - libx264: Open-source H.264 video codec for high-quality compression.
    """

    # Generate output filename by swapping extension
    base_name = os.path.splitext(video_path)[0]
    output_path = f"{base_name}_no_audio.{output_ext}"

    print(f"Loading video: {video_path}...")
    
    # Context manager ensures resources are closed properly
    with VideoFileClip(video_path) as video_clip:
        # Remove audio track
        video_clip = video_clip.without_audio()
        
        print(f"Writing video (without audio) to: {output_path}...")
        video_clip.write_videofile(
            output_path,
            codec=codec,
            audio=False  # Explicitly confirm no audio
        )
        
    return output_path

def run_gui():
    """
    Initialize a tkinter window to handle file selection and processing
    """
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)  # bring to front

    # 1. Open file picker
    file_path = filedialog.askopenfilename(
        title="Select video file for video extraction (remove audio)",
        filetypes=[("Video Files", "*.mp4 *.mkv *.mov *.avi"), ("All Files", "*.*")]
    )
    if not file_path:
        print("No file selected. Exiting.")
        return
    try:
        # 2. Process file
        output_file = extract_video_without_audio(file_path, codec="libx264")

        # 3. Success message
        messagebox.showinfo("Success", f"Video extracted successfully (without audio)!\nSaved to: {output_file}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to extract video:\n{str(e)}")
    root.destroy()

if __name__ == "__main__":
    run_gui()