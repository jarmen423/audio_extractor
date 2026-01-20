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

## Requirements

- Python 3.7+
- FFmpeg (system-wide installation)
- moviepy (Python library)
- yt-dlp (for URL support)

## Project Structure

```
audio_extractor/
├── audio_extractor.py    # Main application
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
