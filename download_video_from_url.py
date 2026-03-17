#!/usr/bin/env python3
"""Download video from URL(s) using yt-dlp.

Examples:
  python download_video.py "https://www.youtube.com/watch?v=..."
  python download_video.py "https://www.instagram.com/reel/..." -o downloads
  python download_video.py "https://www.tiktok.com/@user/video/..." --cookies-from-browser chrome
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Download video from media URLs (YouTube, Instagram, TikTok, and other "
            "yt-dlp-supported platforms)."
        )
    )
    parser.add_argument(
        "urls",
        nargs="+",
        help="One or more media URLs to download.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=".",
        help="Output directory (default: current directory).",
    )
    parser.add_argument(
        "-n",
        "--filename-template",
        default="%(uploader|unknown)s_%(title).120B_%(id)s.%(ext)s",
        help=(
            "yt-dlp output template (default: "
            "%%(uploader|unknown)s_%%(title).120B_%%(id)s.%%(ext)s)."
        ),
    )
    parser.add_argument(
        "-f",
        "--format",
        default="bestvideo+bestaudio/best",
        help=(
            "yt-dlp format selector for video downloads "
            '(default: "bestvideo+bestaudio/best").'
        ),
    )
    parser.add_argument(
        "--audio-only",
        action="store_true",
        help="Download best available audio only.",
    )
    parser.add_argument(
        "--cookies-from-browser",
        choices=["chrome", "firefox", "edge", "brave", "chromium"],
        help="Use browser cookies for private/login-gated content.",
    )
    parser.add_argument(
        "--playlist",
        action="store_true",
        help="Allow playlist/channel downloads (default: off).",
    )
    parser.add_argument(
        "--no-overwrites",
        action="store_true",
        help="Skip files that already exist.",
    )
    return parser


def validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")


def is_tiktok_url(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return "tiktok.com" in host


def run_download(yt_dlp_module, url: str, options: dict[str, object]) -> None:
    with yt_dlp_module.YoutubeDL(options) as ydl:
        ydl.download([url])


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    for url in args.urls:
        try:
            validate_url(url)
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
        "noplaylist": not args.playlist,
        "quiet": False,
        "merge_output_format": "mp4",
        "overwrites": not args.no_overwrites,
    }

    if args.audio_only:
        ydl_opts["format"] = "bestaudio/best"
    else:
        ydl_opts["format"] = args.format

    print(f"Saving to: {output_dir}")
    print(f"URLs: {len(args.urls)}")

    failed_urls: list[str] = []
    script_dir = Path(__file__).resolve().parent
    tiktok_cookie_file = script_dir / "cookies" / "tiktok_cookies.txt"

    for url in args.urls:
        try:
            if not is_tiktok_url(url):
                opts = dict(ydl_opts)
                if args.cookies_from_browser:
                    opts["cookiesfrombrowser"] = (args.cookies_from_browser,)
                run_download(yt_dlp, url, opts)
                continue

            print(f"TikTok URL detected: {url}")

            attempts: list[tuple[str, dict[str, object]]] = []
            base_tiktok_opts = dict(ydl_opts)
            base_tiktok_opts.pop("cookiesfrombrowser", None)

            if tiktok_cookie_file.exists():
                cookie_opts = dict(base_tiktok_opts)
                cookie_opts["cookiefile"] = str(tiktok_cookie_file)
                attempts.append(
                    (f"cookies file ({tiktok_cookie_file})", cookie_opts)
                )
            else:
                print(
                    f"TikTok cookie file not found at {tiktok_cookie_file}, "
                    "skipping cookiefile attempt."
                )

            browser = args.cookies_from_browser or "edge"
            browser_opts = dict(base_tiktok_opts)
            browser_opts["cookiesfrombrowser"] = (browser,)
            attempts.append((f"browser cookies ({browser})", browser_opts))

            ua_opts = dict(base_tiktok_opts)
            ua_opts["http_headers"] = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                )
            }
            attempts.append(("no-cookies fallback (desktop User-Agent)", ua_opts))

            attempt_errors: list[str] = []
            success = False
            for label, attempt_opts in attempts:
                print(f"Attempt: {label}")
                try:
                    run_download(yt_dlp, url, attempt_opts)
                    print(f"Success via: {label}")
                    success = True
                    break
                except Exception as exc:
                    error_text = str(exc)
                    print(f"Attempt failed ({label}): {error_text}")
                    attempt_errors.append(f"{label}: {error_text}")

            if not success:
                failed_urls.append(url)
                print(
                    "TikTok download failed after all fallbacks:\n  - "
                    + "\n  - ".join(attempt_errors),
                    file=sys.stderr,
                )

        except Exception as exc:
            failed_urls.append(url)
            print(f"Download failed for {url}: {exc}", file=sys.stderr)

    if failed_urls:
        print(
            "Some downloads failed:\n  - " + "\n  - ".join(failed_urls),
            file=sys.stderr,
        )
        return 1

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
