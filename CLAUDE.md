# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python GUI application that extracts audio from video files and media URLs. Supports local video files (MP4, MKV, MOV, AVI) and online media from YouTube, Twitch, TikTok, and 1000+ other platforms. Single-file architecture - all code is in `audio_extractor.py`.

## Commands

```bash
# Setup
python -m venv .venv-audioextractor
.venv-audioextractor\Scripts activate  # Windows
# or
source .venv-audioextractor/bin/activate  # macOS/Linux

pip install -r requirements.txt

# Run
python audio_extractor.py
```

**Requirements:**
- FFmpeg must be installed (MoviePy dependency)
- yt-dlp must be installed (for URL support)

## Architecture

```
audio_extractor.py
├── extract_audio_from_video(video_path, output_ext, bitrate)
│   └── Uses VideoFileClip to load video, extracts audio via .audio attribute,
│       writes using write_audiofile with libmp3lame codec
├── download_media_from_url(url, output_dir)
│   └── Uses yt-dlp to download media from 1000+ platforms,
│       handles authentication and format selection
└── run_gui()
    └── Tkinter dialog for URL or file selection,
        routes to appropriate extraction method,
        shows success/error via messagebox
```

## Key Technologies

### MoviePy
- High-level Python library for video editing
- Wraps FFmpeg for codec processing
- Uses `VideoFileClip` to load video containers (MP4, MKV, MOV, AVI)
- Accesses audio via `.audio` attribute without manual decoding

### yt-dlp
- Command-line tool and Python library for downloading media
- Supports 1000+ platforms (YouTube, Twitch, TikTok, Instagram, etc.)
- Handles authentication for login-required platforms
- Uses FFmpeg internally for downloading and transcoding
- More actively maintained than youtube-dl

### FFmpeg
- Underlying engine used by both MoviePy and yt-dlp
- Required for all audio/video processing operations

## URL Support Implementation

### download_media_from_url()
- Downloads media from URL to temporary directory
- Uses yt-dlp with format selection options
- Returns local file path for subsequent audio extraction
- Handles authentication and platform-specific requirements
- Cleans up temporary files after extraction

### run_gui() URL Flow
1. User selects "Yes" for URL input
2. Enters media URL (YouTube, Twitch, TikTok, etc.)
3. yt-dlp downloads media to temp directory
4. extract_audio_from_video() extracts audio
5. Temporary file is deleted
6. Success message displayed

## Supported Platforms

The application supports 1000+ platforms including:
- **Video**: YouTube, Twitch, TikTok, Instagram, Facebook, Vimeo, Dailymotion
- **Audio**: SoundCloud, Bandcamp, Mixcloud, Spotify (limited)
- **Live Streams**: YouTube Live, Twitch, Facebook Live

## Known Issues

- **Line 67 bug:** `tk.tk()` should be `tk.Tk()` - missing `import tkinter as tk` at top of file
- **Duplicate import:** `from moviepy.editor import VideoFileClip` appears twice (lines 9 and 11)

## Security Considerations

- Never hardcode credentials or API keys
- Validate URL format before processing
- Clean up temporary files after extraction
- Ensure temp directory is writable
- Handle authentication errors gracefully

## Error Handling

- Invalid URLs → `ValueError`
- Download failures → `RuntimeError`
- Corrupted files → `IOError`
- Authentication failures → `RuntimeError` (yt-dlp specific)

## Testing

To test URL support:
1. Run `python audio_extractor.py`
2. Select "Yes" for URL input
3. Enter a valid YouTube/Twitch/TikTok URL
4. Verify audio extraction succeeds
5. Check that temporary files are cleaned up

## Dependencies

```txt
moviepy>=1.0.3
yt-dlp>=2023.12.30
```

## Future Enhancements

- Add format selection dialog (MP3, WAV, AAC, FLAC)
- Add bitrate selection dialog
- Add playlist support for URLs
- Add progress bar for downloads
- Add batch processing for multiple URLs
