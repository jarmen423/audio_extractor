#!/usr/bin/env python3
"""Download Instagram videos using yt-dlp.

Usage examples:
  python download_instagram_video.py "https://www.instagram.com/reel/XXXXXXXXXXX/"
  python download_instagram_video.py "<url>" -o downloads
  python download_instagram_video.py "<url>" --cookies-from-browser chrome
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download an Instagram video (reel/post) using yt-dlp."
    )
    parser.add_argument("url", help="Instagram reel/post URL")
    parser.add_argument(
        "-o",
        "--output-dir",
        default=".",
        help="Output directory (default: current directory)",
    )
    parser.add_argument(
        "-n",
        "--filename-template",
        default="%(uploader)s_%(id)s.%(ext)s",
        help="yt-dlp output template (default: %%(uploader)s_%%(id)s.%%(ext)s)",
    )
    parser.add_argument(
        "--cookies-from-browser",
        choices=["chrome", "firefox", "edge", "brave", "chromium"],
        help="Use browser cookies for private/login-gated content",
    )
    parser.add_argument(
        "--audio-only",
        action="store_true",
        help="Download audio only",
    )
    return parser


def validate_instagram_url(url: str) -> None:
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    if "instagram.com" not in host:
        raise ValueError("URL must be an instagram.com link.")
    if not parsed.path:
        raise ValueError("Invalid Instagram URL path.")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        validate_instagram_url(args.url)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        import yt_dlp  # type: ignore
    except Exception:
        print(
            "yt-dlp is not installed. Install it with: pip install yt-dlp",
            file=sys.stderr,
        )
        return 1

    outtmpl = str(output_dir / args.filename_template)
    ydl_opts: dict[str, object] = {
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": False,
    }

    if args.audio_only:
        ydl_opts["format"] = "bestaudio/best"

    if args.cookies_from_browser:
        ydl_opts["cookiesfrombrowser"] = (args.cookies_from_browser,)

    print(f"Downloading: {args.url}")
    print(f"Saving to:   {output_dir}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([args.url])
    except Exception as exc:
        print(f"Download failed: {exc}", file=sys.stderr)
        return 1

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
