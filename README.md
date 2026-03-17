# Audio Extractor

A Python GUI application that extracts high-quality audio from video files and media URLs. Supports local video files (MP4, MKV, MOV, AVI) and online media from YouTube, Twitch, TikTok, and 1000+ other platforms.

## Features

- **Local File Support**: Extract audio from MP4, MKV, MOV, and AVI video files
- **URL Support**: Download and extract audio from YouTube, Twitch, TikTok, Instagram, and 1000+ other platforms
- **High-Quality Output**: Configurable bitrate (default 192k) and format (MP3, WAV)
- **User-Friendly GUI**: Simple Tkinter interface for easy file/URL selection
- **Automatic Cleanup**: Temporary files are automatically deleted after extraction

## Installation

### Prerequisites

1. **Python 3.7+**
2. **FFmpeg** (required by MoviePy)

#### Installing FFmpeg

**Windows:**
```bash
# Using Chocolatey
choco install ffmpeg

# Using winget
winget install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg  # Debian/Ubuntu
sudo yum install ffmpeg  # CentOS/RHEL
```

### Setup

```bash
# Create virtual environment
python -m venv .venv-audioextractor
.venv-audioextractor\Scripts activate  # Windows
# or
source .venv-audioextractor/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Running the Application

```bash
python audio_extractor.py
```

### Download Video From URL (CLI)

Use the dedicated downloader script for full video downloads:

```bash
python download_video.py "https://www.youtube.com/watch?v=example"
python download_video.py "https://www.instagram.com/reel/XXXXXXXXXXX/" -o downloads
python download_video.py "https://www.tiktok.com/@user/video/1234567890" --cookies-from-browser chrome
```

Options:
- `--audio-only`: Download audio only
- `--playlist`: Allow playlist/channel downloads
- `--no-overwrites`: Skip files that already exist

### Using Local Files

1. Launch the application
2. Select "No" when asked if you want to extract from a URL
3. Choose a video file (MP4, MKV, MOV, AVI)
4. Audio will be extracted and saved as MP3 (default) or WAV

### Using URLs

1. Launch the application
2. Select "Yes" when asked if you want to extract from a URL
3. Enter the media URL (YouTube, Twitch, TikTok, etc.)
4. Audio will be downloaded, extracted, and saved automatically

### Supported Platforms

The application supports 1000+ platforms including:
- **Video**: YouTube, Twitch, TikTok, Instagram, Facebook, Vimeo, Dailymotion
- **Audio**: SoundCloud, Bandcamp, Mixcloud, Spotify (limited)
- **Live Streams**: YouTube Live, Twitch, Facebook Live

## Command-Line Alternative

You can also use FFmpeg directly to extract audio from URLs:

```bash
ffmpeg -i "https://www.youtube.com/watch?v=example" -vn -acodec libmp3lame -b:a 192k output.mp3
```

## Frame Extraction Script

Use `extract_frames.py` when you want frame sampling controls, optional GUI pickers, and per-frame timestamps.

### Basic usage (GUI file picker)

```bash
python extract_frames.py
```

### Sample every 10 seconds and write timestamps CSV

```bash
python extract_frames.py "input.mp4" --mode fps --fps 1/10 --timestamps-csv
```

This writes extracted images to `frames_YYYYMMDD_HHMMSS/` and a `timestamps.csv` file in that folder.

### Add per-frame EXIF metadata (second pass with exiftool)

```bash
python extract_frames.py "input.mp4" --mode fps --fps 1/10 --timestamps-csv --write-exif
```

Notes:
- `--write-exif` requires `exiftool` installed and on your PATH.
- Metadata is written to `ImageDescription` and `Comment` as `video_timestamp=HH:MM:SS.mmm (X.XXXXXXs)`.

## Requirements

- Python 3.7+
- FFmpeg (system-wide installation)
- moviepy (Python library)
- yt-dlp (for URL support)

## Project Structure

```
audio_extractor/
├── audio_extractor.py    # Main application
├── download_video.py     # CLI video downloader for URL links
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── CLAUDE.md           # Developer documentation
```

## Troubleshooting

### FFmpeg Not Found
Ensure FFmpeg is installed and added to your system PATH.

### URL Download Failures
- Check if the URL is valid and accessible
- Some platforms may require authentication
- Check yt-dlp documentation for platform-specific requirements

### Permission Errors
Ensure you have write permissions for the output directory.
