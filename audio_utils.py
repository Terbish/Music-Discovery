import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

log = logging.getLogger(__name__)

# ── Dependency Resolution ─────────────────────────────────────────────────────

def _get_bin_path(name: str) -> str:
    """Return the path to a binary, checking common macOS locations if not on PATH."""
    p = shutil.which(name)
    if p:
        return p
    
    # Common macOS homebrew locations
    standard_paths = [
        f"/opt/homebrew/bin/{name}",
        f"/usr/local/bin/{name}",
    ]
    for path in standard_paths:
        if os.path.exists(path):
            return path
            
    return name

FFMPEG_EXE = _get_bin_path("ffmpeg")
FFPROBE_EXE = _get_bin_path("ffprobe")

# ── Defaults ──────────────────────────────────────────────────────────────────

DEFAULT_AUDIO_FORMAT = "mp3"
DEFAULT_AUDIO_QUALITY = "192"

# ── Core Downloading Logic ───────────────────────────────────────────────────

def download_audio(
    query: str,
    output_path: Path,
    fmt: str = DEFAULT_AUDIO_FORMAT,
    quality: str = DEFAULT_AUDIO_QUALITY,
    quiet: bool = True,
    metadata: dict = None
) -> bool:
    """
    Search YouTube for *query* and download audio as a temporary file first.
    Applies Artist, Album, and Title tags if metadata is provided.
    Once finished, moves the final file to *output_path*.
    This ensures that folders watched by Music.app/iTunes don't see incomplete files.
    """
    if yt_dlp is None:
        log.error("yt-dlp not found. Please install it via pip install yt-dlp")
        return False

    # 1. Setup temporary staging directory
    temp_dir = Path("personal/temp")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # We use a unique temporary name inside the temp dir
    import uuid
    temp_filename = f"dl_{uuid.uuid4().hex}"
    temp_path = temp_dir / f"{temp_filename}.{fmt}"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(temp_path.with_suffix("")),   # yt-dlp appends the extension
        "quiet": quiet,
        "no_warnings": True,
        "logger": log,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": fmt,
                "preferredquality": quality,
            }
        ],
        "default_search": "ytsearch1",   # pick the top YouTube result
        "nooverwrites": True,
        "ffmpeg_location": FFMPEG_EXE,
    }

    try:
        # 2. Download into temp staging
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([query])
        
        if not temp_path.exists():
            log.error("Download failed: temp file not found at %s", temp_path)
            return False

        # 3. Apply metadata tagging while still in temp
        if metadata:
            _apply_metadata(temp_path, metadata)
            
        # 4. Atomic move to final destination
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path.replace(output_path)
            
        return True
    except yt_dlp.utils.DownloadError as exc:
        log.error("yt-dlp download failed for query '%s': %s", query, exc)
        return False
    except FileNotFoundError:
        log.error("ffmpeg not found on PATH. Please install ffmpeg to enable audio conversion.")
        return False
    except Exception as e:
        log.error("An unexpected error occurred during download: %s", e)
        return False
    finally:
        # Cleanup temp file if it still exists (e.g. on failure)
        if temp_path.exists():
            try:
                temp_path.unlink()
            except:
                pass

def _apply_metadata(path: Path, meta: dict):
    """Internal helper to apply id3-style tags via ffmpeg."""
    # We tag the file in-place (via a local temp file in the same temp dir)
    tagged_temp = path.with_suffix(".tagging" + path.suffix)
    
    cmd = [FFMPEG_EXE, "-y", "-i", str(path)]
    
    if meta.get("title"):
        cmd += ["-metadata", f"title={meta['title']}"]
    if meta.get("artist"):
        cmd += ["-metadata", f"artist={meta['artist']}"]
    if meta.get("album"):
        cmd += ["-metadata", f"album={meta['album']}"]
        
    cmd += ["-c", "copy", str(tagged_temp)]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            tagged_temp.replace(path)
        else:
            log.warning("Metadata tagging failed for %s: %s", path.name, result.stderr)
            if tagged_temp.exists():
                tagged_temp.unlink()
    except Exception as e:
        log.warning("Could not apply metadata to %s: %s", path.name, e)
        if tagged_temp.exists():
            tagged_temp.unlink()
