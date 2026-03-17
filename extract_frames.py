"""
Module: extract_frames.py
Purpose: Extract still frames from a video with configurable sampling modes.
Dependencies: ffmpeg, ffprobe (system tools)
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import math
import pathlib
import re
import subprocess
import sys

try:
    import tkinter as tk
    from tkinter import filedialog
except Exception:  # pragma: no cover - environment dependent
    tk = None
    filedialog = None


TIME_RE = re.compile(r"^(?:(\d+):)?(?:(\d+):)?(\d+(?:\.\d+)?)$")
SHOWINFO_PTS_RE = re.compile(r"pts_time:([+-]?\d+(?:\.\d+)?)")
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")


def parse_time_to_seconds(value: str) -> float:
    """Parse time in seconds or HH:MM:SS(.ms) / MM:SS(.ms) format."""
    raw = value.strip()
    if not raw:
        raise ValueError("Empty time value")

    if raw.replace(".", "", 1).isdigit():
        return float(raw)

    match = TIME_RE.match(raw)
    if not match:
        raise ValueError(
            f"Invalid time '{value}'. Use seconds (e.g. 12.5) or HH:MM:SS(.ms)."
        )

    g1, g2, g3 = match.groups()
    if g1 is None and g2 is None:
        return float(g3)
    if g1 is None:
        minutes = int(g2)
        seconds = float(g3)
        return minutes * 60 + seconds

    hours = int(g1)
    minutes = int(g2 or "0")
    seconds = float(g3)
    return hours * 3600 + minutes * 60 + seconds


def run_capture(command: list[str]) -> str:
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"Command not found: {command[0]}. Ensure it is installed and on PATH."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(exc.stderr.strip() or exc.stdout.strip() or str(exc)) from exc
    return result.stdout.strip()


def run_ffmpeg(command: list[str], capture_stderr: bool) -> subprocess.CompletedProcess[str]:
    kwargs = {"text": True, "check": True}
    if capture_stderr:
        kwargs["capture_output"] = True
    return subprocess.run(command, **kwargs)


def get_video_duration_seconds(input_file: pathlib.Path, ffprobe_bin: str) -> float:
    output = run_capture(
        [
            ffprobe_bin,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(input_file),
        ]
    )
    try:
        duration = float(output)
    except ValueError as exc:
        raise RuntimeError(f"Unable to parse ffprobe duration output: '{output}'") from exc

    if not math.isfinite(duration) or duration <= 0:
        raise RuntimeError(f"Invalid video duration returned by ffprobe: {duration}")
    return duration


def default_output_dir() -> pathlib.Path:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return pathlib.Path(f"frames_{stamp}")


def build_filter(args: argparse.Namespace, effective_duration: float | None) -> str:
    if args.mode == "fps":
        return f"fps={args.fps}"

    if args.mode == "every-n":
        return f"select='not(mod(n\\,{args.every_n}))'"

    if args.mode == "count":
        if effective_duration is None or effective_duration <= 0:
            raise RuntimeError("Cannot use --mode count without a valid duration.")
        fps = args.count / effective_duration
        return f"fps={fps:.10g}"

    raise RuntimeError(f"Unsupported mode: {args.mode}")


def clean_ansi(text: str) -> str:
    return ANSI_ESCAPE_RE.sub("", text)


def parse_pts_times(ffmpeg_stderr: str) -> list[float]:
    times: list[float] = []
    for line in ffmpeg_stderr.splitlines():
        line_clean = clean_ansi(line)
        if "showinfo" not in line_clean:
            continue
        match = SHOWINFO_PTS_RE.search(line_clean)
        if not match:
            continue
        times.append(float(match.group(1)))
    return times


def format_timestamp_hms(seconds: float) -> str:
    total_ms = int(round(seconds * 1000))
    if total_ms < 0:
        total_ms = 0
    h, remainder = divmod(total_ms, 3_600_000)
    m, remainder = divmod(remainder, 60_000)
    s, ms = divmod(remainder, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def natural_sort_key(path: pathlib.Path) -> list[object]:
    parts = re.split(r"(\d+)", path.name)
    key: list[object] = []
    for part in parts:
        if part.isdigit():
            key.append(int(part))
        else:
            key.append(part.lower())
    return key


def snapshot_dir_files(directory: pathlib.Path) -> dict[str, tuple[int, int]]:
    snapshot: dict[str, tuple[int, int]] = {}
    for item in directory.iterdir():
        if not item.is_file():
            continue
        stat = item.stat()
        snapshot[item.name] = (stat.st_mtime_ns, stat.st_size)
    return snapshot


def detect_changed_files(
    directory: pathlib.Path, before: dict[str, tuple[int, int]]
) -> list[pathlib.Path]:
    changed: list[pathlib.Path] = []
    for item in directory.iterdir():
        if not item.is_file():
            continue
        stat = item.stat()
        prev = before.get(item.name)
        current = (stat.st_mtime_ns, stat.st_size)
        if prev is None or prev != current:
            changed.append(item)
    changed.sort(key=natural_sort_key)
    return changed


def write_timestamps_csv(
    csv_path: pathlib.Path,
    files: list[pathlib.Path],
    timestamps: list[float],
    source_video: pathlib.Path,
) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "index",
                "filename",
                "timestamp_seconds",
                "timestamp_hms",
                "source_video",
            ]
        )
        for index, (file_path, seconds) in enumerate(zip(files, timestamps), start=1):
            writer.writerow(
                [
                    index,
                    file_path.name,
                    f"{seconds:.6f}",
                    format_timestamp_hms(seconds),
                    str(source_video),
                ]
            )


def write_exif_metadata(
    files: list[pathlib.Path], timestamps: list[float], exiftool_bin: str
) -> None:
    for file_path, seconds in zip(files, timestamps):
        ts_hms = format_timestamp_hms(seconds)
        description = f"video_timestamp={ts_hms} ({seconds:.6f}s)"
        try:
            subprocess.run(
                [
                    exiftool_bin,
                    "-overwrite_original",
                    f"-ImageDescription={description}",
                    f"-Comment={description}",
                    str(file_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                f"exiftool not found: {exiftool_bin}. Install exiftool or pass --exiftool-bin."
            ) from exc
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            stdout = (exc.stdout or "").strip()
            msg = stderr or stdout or f"exiftool failed for {file_path.name}"
            raise RuntimeError(msg) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract frames from a video using ffmpeg."
    )
    parser.add_argument(
        "input",
        nargs="?",
        type=pathlib.Path,
        help="Path to input video. If omitted, a Tkinter file picker is shown.",
    )
    parser.add_argument(
        "--mode",
        choices=["fps", "every-n", "count"],
        default="fps",
        help="Frame extraction mode (default: fps)",
    )
    parser.add_argument(
        "--fps",
        default="1/10",
        help="Used by --mode fps. Supports values like 0.5 or 1/10 (default: 1/10)",
    )
    parser.add_argument(
        "--every-n",
        type=int,
        default=30,
        help="Used by --mode every-n. Keep every Nth frame (default: 30)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=120,
        help="Used by --mode count. Approximate target number of output images (default: 120)",
    )
    parser.add_argument(
        "--start",
        help="Optional start time (seconds or HH:MM:SS[.ms])",
    )
    parser.add_argument(
        "--end",
        help="Optional end time (seconds or HH:MM:SS[.ms])",
    )
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=default_output_dir(),
        help="Output directory for frames (default: frames_YYYYMMDD_HHMMSS)",
    )
    parser.add_argument(
        "--pattern",
        default="frame_%06d.jpg",
        help="Output filename pattern inside output dir (default: frame_%%06d.jpg)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files in output directory",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print ffmpeg command without running it",
    )
    parser.add_argument(
        "--timestamps-csv",
        type=pathlib.Path,
        nargs="?",
        const=pathlib.Path("timestamps.csv"),
        help="Write frame timestamps to CSV. Optional path (default: <output-dir>/timestamps.csv)",
    )
    parser.add_argument(
        "--write-exif",
        action="store_true",
        help="After extraction, write per-frame timestamp metadata with exiftool",
    )
    parser.add_argument(
        "--exiftool-bin",
        default="exiftool",
        help="exiftool executable name/path (default: exiftool)",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Use Tkinter dialogs to select input video and output folder",
    )
    parser.add_argument(
        "--ffmpeg-bin",
        default="ffmpeg",
        help="ffmpeg executable name/path (default: ffmpeg)",
    )
    parser.add_argument(
        "--ffprobe-bin",
        default="ffprobe",
        help="ffprobe executable name/path (default: ffprobe)",
    )
    return parser


def pick_input_file() -> pathlib.Path | None:
    if tk is None or filedialog is None:
        raise RuntimeError("Tkinter is not available in this Python environment.")

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    selected = filedialog.askopenfilename(
        title="Select video file",
        filetypes=[
            ("Video files", "*.mp4 *.mkv *.mov *.avi *.webm *.m4v"),
            ("All files", "*.*"),
        ],
    )
    root.destroy()
    if not selected:
        return None
    return pathlib.Path(selected)


def pick_output_directory() -> pathlib.Path | None:
    if tk is None or filedialog is None:
        raise RuntimeError("Tkinter is not available in this Python environment.")

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    selected = filedialog.askdirectory(title="Select output folder for frames")
    root.destroy()
    if not selected:
        return None
    return pathlib.Path(selected)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    selected_input = args.input
    if args.gui or selected_input is None:
        try:
            selected_input = pick_input_file()
        except RuntimeError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        if selected_input is None:
            print("No input file selected.", file=sys.stderr)
            return 1

    input_file = selected_input.resolve()
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}", file=sys.stderr)
        return 1

    if args.every_n < 1:
        print("Error: --every-n must be >= 1", file=sys.stderr)
        return 1
    if args.count < 1:
        print("Error: --count must be >= 1", file=sys.stderr)
        return 1

    start_seconds = 0.0
    if args.start:
        try:
            start_seconds = parse_time_to_seconds(args.start)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        if start_seconds < 0:
            print("Error: --start must be >= 0", file=sys.stderr)
            return 1

    end_seconds = None
    if args.end:
        try:
            end_seconds = parse_time_to_seconds(args.end)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        if end_seconds <= start_seconds:
            print("Error: --end must be greater than --start", file=sys.stderr)
            return 1

    output_dir_value = args.output_dir
    if args.gui:
        try:
            selected_output = pick_output_directory()
        except RuntimeError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        if selected_output is not None:
            output_dir_value = selected_output

    output_dir: pathlib.Path = output_dir_value.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_pattern = output_dir / args.pattern

    csv_requested = args.timestamps_csv is not None
    exif_requested = args.write_exif
    need_frame_timestamps = csv_requested or exif_requested

    full_duration = None
    effective_duration = None

    if args.mode == "count" or end_seconds is not None:
        try:
            full_duration = get_video_duration_seconds(input_file, args.ffprobe_bin)
        except RuntimeError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

        if start_seconds >= full_duration:
            print(
                f"Error: --start ({start_seconds:.3f}s) is beyond video duration ({full_duration:.3f}s)",
                file=sys.stderr,
            )
            return 1

        if end_seconds is not None and end_seconds > full_duration:
            end_seconds = full_duration

    if full_duration is not None:
        segment_end = end_seconds if end_seconds is not None else full_duration
        effective_duration = segment_end - start_seconds
        if effective_duration <= 0:
            print("Error: Selected time window has no duration.", file=sys.stderr)
            return 1

    try:
        vf = build_filter(args, effective_duration)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if need_frame_timestamps:
        vf = f"{vf},showinfo"

    command = [args.ffmpeg_bin, "-hide_banner"]
    command.append("-y" if args.overwrite else "-n")
    command.extend(["-i", str(input_file)])

    if start_seconds > 0:
        command.extend(["-ss", f"{start_seconds:.6f}"])
    if end_seconds is not None:
        command.extend(["-to", f"{end_seconds:.6f}"])

    command.extend(["-vf", vf])
    if args.mode == "every-n":
        command.extend(["-vsync", "vfr"])
    command.append(str(output_pattern))

    print("Running command:")
    print(" ".join(command))

    if args.dry_run:
        return 0

    before_snapshot = snapshot_dir_files(output_dir) if need_frame_timestamps else {}

    try:
        result = run_ffmpeg(command, capture_stderr=need_frame_timestamps)
    except FileNotFoundError:
        print(
            f"Error: ffmpeg binary not found: {args.ffmpeg_bin}",
            file=sys.stderr,
        )
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"Error: ffmpeg failed with exit code {exc.returncode}", file=sys.stderr)
        return 1

    print(f"Frames saved to: {output_dir}")

    if need_frame_timestamps:
        changed_files = detect_changed_files(output_dir, before_snapshot)
        pts_times = parse_pts_times(result.stderr or "")

        # showinfo reports times relative to extraction start when -ss is used after -i.
        absolute_times = [value + start_seconds for value in pts_times]
        pair_count = min(len(changed_files), len(absolute_times))
        if pair_count == 0:
            print(
                "Warning: No frame/timestamp pairs available for CSV/EXIF export.",
                file=sys.stderr,
            )
            return 0

        if len(changed_files) != len(absolute_times):
            print(
                f"Warning: Frame count ({len(changed_files)}) and timestamp count ({len(absolute_times)}) differ. "
                f"Using first {pair_count} entries.",
                file=sys.stderr,
            )

        files_for_meta = changed_files[:pair_count]
        timestamps_for_meta = absolute_times[:pair_count]

        csv_path: pathlib.Path | None = None
        if csv_requested:
            if args.timestamps_csv == pathlib.Path("timestamps.csv"):
                csv_path = output_dir / "timestamps.csv"
            else:
                csv_path = args.timestamps_csv.resolve()
            write_timestamps_csv(csv_path, files_for_meta, timestamps_for_meta, input_file)
            print(f"Timestamps CSV written: {csv_path}")

        if exif_requested:
            try:
                write_exif_metadata(files_for_meta, timestamps_for_meta, args.exiftool_bin)
            except RuntimeError as exc:
                print(f"Error: {exc}", file=sys.stderr)
                return 1
            print("EXIF metadata written to extracted frames.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
