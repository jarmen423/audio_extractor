# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python GUI application that extracts audio from MP4 video files using MoviePy (which wraps FFmpeg). Single-file architecture - all code is in `audio_extractor.py`.

## Commands

```bash
# Setup
python -m venv .venv-audioextractor
.\.venv-audioextractor\Scripts activate
pip install -r requirements.txt

# Run
python audio_extractor.py
```

**Requirements:** FFmpeg must be installed (MoviePy dependency).

## Architecture

```
audio_extractor.py
├── extract_audio_from_video(video_path, output_ext, bitrate)
│   └── Uses VideoFileClip to load video, extracts audio via .audio attribute,
│       writes using write_audiofile with libmp3lame codec
└── run_gui()
    └── Tkinter file dialog for MP4 selection, calls extract function,
        shows success/error via messagebox
```

## Known Issues

- **Line 67 bug:** `tk.tk()` should be `tk.Tk()` - missing `import tkinter as tk` at top of file
- **Duplicate import:** `from moviepy.editor import VideoFileClip` appears twice (lines 9 and 11)
