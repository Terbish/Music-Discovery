#!/usr/bin/env python3
"""
discovery_to_audio.py
-------------------
Given a list of track IDs, this script:
  1. Reads track metadata (title, artist) from a music library CSV export, OR
     scrapes a service page as a fallback (no API key needed)
  2. Searches YouTube for the best matching video via yt-dlp
  3. Downloads and extracts audio-only with yt-dlp + ffmpeg

Requirements:
    pip install yt-dlp requests

External tools:
    - ffmpeg  (must be on PATH — brew install ffmpeg / apt install ffmpeg)

Usage:
    # Pass IDs directly
    python discovery_to_audio.py 3n3Ppam7vgaVa1iaRUIOKE 1BxfuPKGuaTgP7aM0Bbdwr

    # Or edit TRACK_IDS at the top of the script, then:
    python discovery_to_audio.py

    # Options
    python discovery_to_audio.py -o my_music -f flac <id1> <id2>
"""

import re
import sys
import argparse
import logging
import requests
from pathlib import Path
from tqdm import tqdm

from discovery_utils import parse_csv, sanitize_filename, CsvMetadata
from audio_utils import download_audio


# ── Configuration ─────────────────────────────────────────────────────────────

TRACK_IDS: list[str] = []

DEFAULT_OUTPUT_DIR: str  = "personal/audio_output"
DEFAULT_FORMAT: str      = "mp3"
DEFAULT_QUALITY: str     = "192"
DEFAULT_SEARCH_SUFFIX: str = "official audio"
DEFAULT_CSV_PATH: str    = "personal/music_library_with_genres.csv"

# ── Logging ───────────────────────────────────────────────────────────────────

LOG_FILE = Path("personal/temp/processing.log")

class TqdmLoggingHandler(logging.Handler):
    """Handler that uses tqdm.write to avoid breaking the progress bar."""
    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.write(msg)
            self.flush()
        except Exception:
            self.handleError(record)

def setup_logging():
    """Configure logging to both file (detailed) and console (errors only)."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # File handler: detailed processing info
    file_handler = logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter("%(asctime)s  %(levelname)-7s  %(message)s", datefmt="%H:%M:%S")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Stream handler: errors and warnings to console (using tqdm.write)
    stream_handler = TqdmLoggingHandler()
    stream_handler.setLevel(logging.WARNING)
    stream_formatter = logging.Formatter("%(asctime)s  %(levelname)-7s  %(message)s", datefmt="%H:%M:%S")
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)

setup_logging()
log = logging.getLogger(__name__)


# ── Metadata scraping fallback ────────────────────────────────────────────────

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


from typing import Dict, Optional

def get_service_metadata(track_id: str) -> Optional[dict]:
    """
    Attempt to scrape title and artist from service page.
    Returns {"title": ..., "artist": ...} or None on failure.
    """
    url = f"https://open.spotify.com/track/{track_id}"
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        log.error("Could not fetch page for %s: %s", track_id, exc)
        return None

    html = resp.text

    # og:title  →  "Track Title"
    title_match = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', html)
    # og:description  →  "Song · Artist · Album · Year"
    desc_match  = re.search(r'<meta\s+property="og:description"\s+content="([^"]+)"', html)

    if not title_match:
        log.warning(
            "Could not parse title for %s — site returned a JS shell page. "
            "Pass a --csv file to use offline metadata instead.",
            track_id,
        )
        return None

    title = title_match.group(1).strip()

    artist = "Unknown Artist"
    album  = "Unknown Album"
    if desc_match:
        # Description format: "Song · Artist · Album · 2024"
        parts = [p.strip() for p in desc_match.group(1).split("·")]
        if len(parts) >= 2:
            artist = parts[1]
        if len(parts) >= 3:
            album = parts[2]

    return {"title": title, "artist": artist, "album": album}


# ── Main pipeline ─────────────────────────────────────────────────────────────

def process_track(
    track_id: str,
    output_dir: Path,
    fmt: str,
    quality: str,
    search_suffix: str,
    csv_meta: Optional[Dict[str, str]] = None,
) -> bool:
    log.info("── Processing: %s", track_id)

    # 1. Prefer metadata from CSV; fall back to scraping service
    if csv_meta and csv_meta.get("title"):
        meta = csv_meta
        log.info("  Track (from CSV): %s — %s [%s]", meta["artist"], meta["title"], meta.get("album", "Unknown Album"))
    else:
        meta = get_service_metadata(track_id)
        if not meta:
            return False
        log.info("  Track (scraped): %s — %s [%s]", meta["artist"], meta["title"], meta.get("album", "Unknown Album"))

    # 2. Build YouTube search query
    query = f"{meta['artist']} - {meta['title']} {search_suffix}".strip()
    log.info("  Searching YouTube: %s", query)

    # 3. Output path
    safe_name = sanitize_filename(f"{meta['artist']} - {meta['title']}")
    output_path = output_dir / f"{safe_name}.{fmt}"

    if output_path.exists():
        log.info("  ⏭  Already exists, skipping: %s", output_path.name)
        return True

    # 4. Download + extract audio via yt-dlp → ffmpeg
    ok = download_audio(query, output_path, fmt, quality, quiet=True, metadata=meta)

    if ok:
        log.info("  ✅  Saved: %s", output_path.name)
    return ok


def main(
    track_ids: list[str],
    output_dir: str = DEFAULT_OUTPUT_DIR,
    fmt: str = DEFAULT_FORMAT,
    quality: str = DEFAULT_QUALITY,
    search_suffix: str = DEFAULT_SEARCH_SUFFIX,
    all_metadata: Optional[CsvMetadata] = None,
) -> None:
    if not track_ids:
        sys.exit(
            "❌  No IDs provided.\n"
            "    Pass them as arguments, or edit TRACK_IDS at the top of the script."
        )

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    results: dict[str, list[str]] = {"ok": [], "fail": []}

    print(f"🚀  Processing {len(track_ids)} tracks...")
    with tqdm(total=len(track_ids), unit="track", dynamic_ncols=True) as pbar:
        for tid in track_ids:
            tid = tid.strip()
            if not tid:
                pbar.update(1)
                continue

            csv_meta = (all_metadata or {}).get(tid)
            
            # Simple UI: update progress bar with current track
            display_name = tid
            if csv_meta:
                display_name = f"{csv_meta['artist']} - {csv_meta['title']}"
            pbar.set_description(f"📥 {display_name[:40]}")
            
            success = process_track(tid, out, fmt, quality, search_suffix, csv_meta)
            (results["ok"] if success else results["fail"]).append(tid)
            pbar.update(1)

    # Final summary to CLI
    print(f"\n── Done: {len(results['ok'])} succeeded, {len(results['fail'])} failed")
    if results["fail"]:
        print(f"⚠️  Failed IDs: {', '.join(results['fail'])}")
        print(f"📄  Detailed logs available in: {LOG_FILE}")
    else:
        # If everything succeeded, remove the log file as requested
        if LOG_FILE.exists():
            LOG_FILE.unlink()
        print("✨  All tracks processed successfully!")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Download tracks as audio files via YouTube + ffmpeg.\n"
            "No API key required — scrapes metadata directly."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "ids",
        nargs="*",
        help="Track IDs (overrides TRACK_IDS list in script)",
    )
    parser.add_argument(
        "-o", "--output",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output folder (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "-f", "--format",
        default=DEFAULT_FORMAT,
        choices=["mp3", "m4a", "wav", "flac", "opus", "ogg"],
        help=f"Audio format (default: {DEFAULT_FORMAT})",
    )
    parser.add_argument(
        "-q", "--quality",
        default=DEFAULT_QUALITY,
        help=f"Audio bitrate kbps for lossy formats (default: {DEFAULT_QUALITY})",
    )
    parser.add_argument(
        "-s", "--search-suffix",
        default=DEFAULT_SEARCH_SUFFIX,
        dest="search_suffix",
        help=f'Appended to YouTube search query (default: "{DEFAULT_SEARCH_SUFFIX}")',
    )
    parser.add_argument(
        "-c", "--csv",
        default=DEFAULT_CSV_PATH,
        metavar="CSV_FILE",
        help=f"Path to music library CSV export (default: {DEFAULT_CSV_PATH})",
    )
    args = parser.parse_args()

    all_metadata: Optional[CsvMetadata] = None
    csv_path = Path(args.csv)
    
    if csv_path.exists():
        csv_ids, all_metadata = parse_csv(args.csv)
    elif args.csv != DEFAULT_CSV_PATH:
        sys.exit(f"❌  CSV file not found: {args.csv}")
    else:
        csv_ids = []

    if args.ids:
        ids = args.ids
    else:
        ids = csv_ids if csv_ids else TRACK_IDS
    main(ids, args.output, args.format, args.quality, args.search_suffix, all_metadata)