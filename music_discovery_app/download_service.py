import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from audio_utils import download_audio_from_url, yt_dlp
from discovery_utils import sanitize_filename
from music_discovery_app.settings import AppSettings, environment_status, load_settings, resolve_data_dir


class DownloadServiceError(Exception):
    pass


ProgressCallback = Callable[[dict[str, Any]], None]


def read_download_queue(settings: AppSettings | None = None) -> dict[str, Any]:
    current = settings or load_settings()
    discovery_dir = Path(current.output_path)
    batches = _read_batches(discovery_dir)
    tracks = _read_batch_tracks(batches[0]["path"], current) if batches else []

    return {
        "environment": environment_status(),
        "settings": {
            "audio_output_path": current.audio_output_path,
            "audio_format": current.audio_format,
            "discovery_dir": current.output_path,
        },
        "batches": batches,
        "active_batch": batches[0] if batches else None,
        "tracks": tracks,
    }


def create_library_download_queue(settings: AppSettings | None = None) -> dict[str, Any]:
    current = settings or load_settings()
    library_path = resolve_data_dir(current) / "personal_library.json"
    if not library_path.exists():
        raise DownloadServiceError("Personal library is required before adding it to the download queue.")

    with open(library_path, "r", encoding="utf-8") as f:
        library = json.load(f)

    tracks = library.get("all_tracks", [])
    if not tracks:
        raise DownloadServiceError("No tracks found in the personal library.")

    output_dir = Path(current.output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_file = output_dir / f"queue_library_{timestamp}.csv"
    fieldnames = ["title", "artist", "album", "added_date", "Genres", "Spotify ID"]

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for track in tracks:
            writer.writerow(
                {
                    "title": track.get("title", ""),
                    "artist": track.get("artist", ""),
                    "album": track.get("album", ""),
                    "added_date": track.get("added_date", ""),
                    "Genres": ", ".join(track.get("genres", [])),
                    "Spotify ID": track.get("track_id", ""),
                }
            )

    return {
        "path": str(output_file),
        "track_count": len(tracks),
        "label": "Library queue",
    }


def search_youtube_sources(track: dict[str, Any], limit: int = 8) -> dict[str, Any]:
    if yt_dlp is None:
        raise DownloadServiceError("yt-dlp is not installed.")

    title = str(track.get("title") or "").strip()
    artist = str(track.get("artist") or "").strip()
    if not title or not artist:
        raise DownloadServiceError("Track title and artist are required before searching sources.")

    query = f"{artist} - {title} official audio"
    opts = {
        "extract_flat": True,
        "quiet": True,
        "no_warnings": True,
        "default_search": "ytsearch",
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            result = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
    except Exception as exc:
        raise DownloadServiceError(f"Could not search YouTube sources: {exc}") from exc

    entries = result.get("entries", []) if result else []
    candidates = [_candidate_from_entry(entry, track, index) for index, entry in enumerate(entries, 1)]
    candidates.sort(key=lambda candidate: candidate["confidence"], reverse=True)

    return {
        "query": query,
        "track": _track_identity(track),
        "candidates": candidates,
    }


def search_queue_sources(
    tracks: list[dict[str, Any]],
    limit: int = 8,
    progress_callback: ProgressCallback | None = None,
    settings: AppSettings | None = None,
) -> dict[str, Any]:
    results = []
    total = len(tracks)
    _emit(progress_callback, "started", current=0, total=total, message="Searching sources")
    for index, track in enumerate(tracks, 1):
        track_id = str(track.get("id") or "")
        _emit(
            progress_callback,
            "progress",
            current=index,
            total=total,
            message=f"Searching {track.get('artist', '')} - {track.get('title', '')}".strip(" -"),
        )
        try:
            data = search_youtube_sources(track, limit)
            save_track_sources(track, data["candidates"], data["query"], settings=settings)
            results.append(
                {
                    "ok": True,
                    "track_id": track_id,
                    "source_key": source_key_for_track(track),
                    "track": data["track"],
                    "query": data["query"],
                    "candidates": data["candidates"],
                }
            )
            _emit(progress_callback, "track_succeeded", current=index, total=total, message="Sources found")
        except DownloadServiceError as exc:
            results.append(
                {
                    "ok": False,
                    "track_id": track_id,
                    "source_key": source_key_for_track(track),
                    "error": str(exc),
                }
            )
            _emit(progress_callback, "track_failed", current=index, total=total, message=str(exc))

    result = {
        "searched": len(tracks),
        "succeeded": sum(1 for result in results if result["ok"]),
        "failed": sum(1 for result in results if not result["ok"]),
        "results": results,
    }
    _emit(progress_callback, "succeeded", current=total, total=total, message="Source search complete", result=result)
    return result


def download_best_sources(
    tracks: list[dict[str, Any]],
    limit: int = 8,
    progress_callback: ProgressCallback | None = None,
    settings: AppSettings | None = None,
) -> dict[str, Any]:
    current = settings or load_settings()
    total = len(tracks)
    results = []
    _emit(progress_callback, "started", current=0, total=total, message="Downloading best sources")

    for index, track in enumerate(tracks, 1):
        try:
            candidates = list(track.get("candidates") or [])
            query = str(track.get("source_query") or "")
            if not candidates:
                data = search_youtube_sources(track, limit)
                candidates = data["candidates"]
                query = data["query"]
                save_track_sources(track, candidates, query, settings=current)

            source = _best_source(candidates)
            if not source:
                raise DownloadServiceError("No source candidates found.")

            result = download_selected_source(track, source, settings=current, replace_existing=False)
            if not result.get("skipped"):
                save_downloaded_source(track, source, result["path"], candidates, query, settings=current)
            results.append(
                {
                    "ok": True,
                    "track_id": track.get("id", ""),
                    "source_key": source_key_for_track(track),
                    "source": source,
                    "download": result,
                }
            )
            _emit(progress_callback, "progress", current=index, total=total, message=f"Downloaded {track.get('title', '')}")
        except DownloadServiceError as exc:
            results.append(
                {
                    "ok": False,
                    "track_id": track.get("id", ""),
                    "source_key": source_key_for_track(track),
                    "error": str(exc),
                }
            )
            _emit(progress_callback, "progress", current=index, total=total, message=str(exc))

    result = {
        "processed": total,
        "succeeded": sum(1 for row in results if row["ok"]),
        "failed": sum(1 for row in results if not row["ok"]),
        "results": results,
    }
    _emit(progress_callback, "succeeded", current=total, total=total, message="Best source downloads complete", result=result)
    return result


def download_selected_source(
    track: dict[str, Any],
    source: dict[str, Any],
    settings: AppSettings | None = None,
    replace_existing: bool = False,
) -> dict[str, Any]:
    current = settings or load_settings()
    url = source.get("webpage_url") or source.get("url")
    if not url:
        raise DownloadServiceError("The selected source does not include a YouTube URL.")

    title = str(track.get("title") or "").strip()
    artist = str(track.get("artist") or "").strip()
    if not title or not artist:
        raise DownloadServiceError("Track title and artist are required before downloading.")

    fmt = current.audio_format or "mp3"
    output_dir = Path(current.audio_output_path)
    output_path = output_dir / f"{sanitize_filename(f'{artist} - {title}')}.{fmt}"
    if output_path.exists() and not replace_existing:
        return {
            "path": str(output_path),
            "skipped": True,
            "message": "Track already exists in the audio output folder.",
        }

    metadata = {
        "title": title,
        "artist": artist,
        "album": track.get("album") or "",
    }
    ok = download_audio_from_url(url, output_path, fmt=fmt, metadata=metadata)
    if not ok:
        raise DownloadServiceError("Download or audio conversion failed.")

    save_downloaded_source(track, source, str(output_path), settings=current)
    return {
        "path": str(output_path),
        "skipped": False,
        "message": "Replaced downloaded source." if replace_existing else "Downloaded selected source.",
    }


def save_track_sources(
    track: dict[str, Any],
    candidates: list[dict[str, Any]],
    query: str,
    settings: AppSettings | None = None,
) -> None:
    library_path, library = _read_personal_library(settings)
    ledger = library.setdefault("download_sources", {})
    key = source_key_for_track(track)
    existing = ledger.get(key, {})
    selected_source_id = existing.get("selected_source_id")
    if not selected_source_id and candidates:
        selected_source_id = candidates[0].get("id")

    ledger[key] = {
        **existing,
        "track": _track_identity(track),
        "searched_at": _now_iso(),
        "query": query,
        "candidates": candidates,
        "selected_source_id": selected_source_id,
    }
    _write_personal_library(library_path, library)


def save_downloaded_source(
    track: dict[str, Any],
    source: dict[str, Any],
    path: str,
    candidates: list[dict[str, Any]] | None = None,
    query: str | None = None,
    settings: AppSettings | None = None,
) -> None:
    library_path, library = _read_personal_library(settings)
    ledger = library.setdefault("download_sources", {})
    key = source_key_for_track(track)
    existing = ledger.get(key, {})
    existing_candidates = candidates if candidates is not None else existing.get("candidates", [])
    ledger[key] = {
        **existing,
        "track": _track_identity(track),
        "query": query if query is not None else existing.get("query", ""),
        "candidates": existing_candidates,
        "selected_source_id": source.get("id"),
        "downloaded": {
            "source_id": source.get("id"),
            "source_title": source.get("title", ""),
            "path": path,
            "downloaded_at": _now_iso(),
        },
    }
    _write_personal_library(library_path, library)


def _read_batches(discovery_dir: Path) -> list[dict[str, Any]]:
    if not discovery_dir.exists():
        return []

    batches = []
    csv_paths = list(discovery_dir.glob("discovery_*.csv")) + list(discovery_dir.glob("queue_*.csv"))
    for path in sorted(csv_paths, key=lambda item: item.stat().st_mtime, reverse=True):
        date_value = path.stem.replace("discovery_", "").replace("queue_", "")
        batches.append(
            {
                "date": date_value,
                "path": str(path),
                "kind": "Discovery" if path.name.startswith("discovery_") else "Queue",
                "track_count": _count_rows(path),
            }
        )
    return batches


def _read_batch_tracks(csv_path: str, settings: AppSettings) -> list[dict[str, Any]]:
    output_dir = Path(settings.audio_output_path)
    fmt = settings.audio_format or "mp3"
    _, library = _read_personal_library(settings, create_if_missing=False)
    source_ledger = library.get("download_sources", {})
    rows = []

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for index, row in enumerate(reader, 1):
            title = _first_value(row, "title", "Track name", "track")
            artist = _first_value(row, "artist", "Artist name")
            album = _first_value(row, "album", "Album name")
            added_date = _first_value(row, "added_date", "Date added", "Added date", "Added At")
            filename = sanitize_filename(f"{artist} - {title}") if title and artist else ""
            output_path = output_dir / f"{filename}.{fmt}" if filename else None
            source_id = _first_value(row, "Deezer ID", "Spotify - id", "Spotify ID", "track_id")
            track = {
                "id": _track_id(title, artist, index),
                "index": index,
                "title": title,
                "artist": artist,
                "album": album,
                "added_date": added_date,
                "genre": _first_value(row, "Genre (Source)", "Genres", "genre"),
                "preview_url": _first_value(row, "Preview URL", "preview"),
                "source_id": source_id,
                "source_id_kind": _source_id_kind(row),
                "output_path": str(output_path) if output_path else "",
            }
            source_key = source_key_for_track(track)
            source_record = source_ledger.get(source_key, {})
            downloaded = source_record.get("downloaded", {})
            downloaded_path = downloaded.get("path", "")
            track.update(
                {
                    "source_key": source_key,
                    "status": "downloaded"
                    if (output_path and output_path.exists()) or (downloaded_path and Path(downloaded_path).exists())
                    else "needs_source",
                    "candidates": source_record.get("candidates", []),
                    "source_query": source_record.get("query", ""),
                    "selected_source_id": source_record.get("selected_source_id", ""),
                    "downloaded_source": downloaded,
                }
            )
            rows.append(track)

    return rows


def _candidate_from_entry(entry: dict[str, Any], track: dict[str, Any], index: int) -> dict[str, Any]:
    title = entry.get("title") or ""
    uploader = entry.get("uploader") or entry.get("channel") or ""
    duration = int(entry.get("duration") or 0)
    badges = _classify_source(title, uploader, duration)
    confidence = _confidence_score(track, title, uploader, duration, badges)
    source_id = entry.get("id") or ""
    webpage_url = entry.get("webpage_url") or entry.get("url") or ""
    if source_id and not webpage_url.startswith("http"):
        webpage_url = f"https://www.youtube.com/watch?v={source_id}"

    return {
        "rank": index,
        "id": source_id,
        "title": title,
        "uploader": uploader,
        "duration": duration,
        "duration_text": _format_duration(duration),
        "webpage_url": webpage_url,
        "url": webpage_url,
        "badges": badges,
        "confidence": confidence,
    }


def _classify_source(title: str, uploader: str, duration: int) -> list[str]:
    haystack = f"{title} {uploader}".lower()
    badges = []
    if "topic" in uploader.lower() or "provided to youtube" in haystack:
        badges.append("Topic")
    if "official audio" in haystack:
        badges.append("Official audio")
    elif "official video" in haystack or "music video" in haystack:
        badges.append("Official video")
    if re.search(r"\blive\b|concert|session", haystack):
        badges.append("Live")
    if "radio edit" in haystack:
        badges.append("Radio edit")
    if "lyrics" in haystack or "lyric video" in haystack:
        badges.append("Lyrics")
    if "cover" in haystack:
        badges.append("Cover")
    if "remaster" in haystack:
        badges.append("Remaster")
    if "remix" in haystack or "mix)" in haystack:
        badges.append("Remix")
    if duration >= 600:
        badges.append("Long")
    return badges or ["Candidate"]


def _confidence_score(track: dict[str, Any], title: str, uploader: str, duration: int, badges: list[str]) -> int:
    haystack = _normalize(f"{title} {uploader}")
    track_title = _normalize(track.get("title") or "")
    artist = _normalize(track.get("artist") or "")
    score = 40

    if track_title and track_title in haystack:
        score += 25
    if artist and artist in haystack:
        score += 20
    if "Topic" in badges:
        score += 12
    if "Official audio" in badges:
        score += 12
    if "Official video" in badges:
        score += 7
    for badge in ("Live", "Cover", "Remix", "Long"):
        if badge in badges:
            score -= 16
    if "Lyrics" in badges:
        score -= 6
    if duration and duration < 75:
        score -= 10

    return max(0, min(score, 100))


def _first_value(row: dict[str, Any], *keys: str) -> str:
    lowered = {key.lower(): value for key, value in row.items()}
    for key in keys:
        if key in row and row[key]:
            return str(row[key]).strip()
        value = lowered.get(key.lower())
        if value:
            return str(value).strip()
    return ""


def _count_rows(path: Path) -> int:
    with open(path, newline="", encoding="utf-8-sig") as f:
        return sum(1 for _ in csv.DictReader(f))


def source_key_for_track(track: dict[str, Any]) -> str:
    source_key = str(track.get("source_key") or "").strip()
    if source_key:
        return source_key

    source_id = str(track.get("source_id") or track.get("track_id") or "").strip()
    if source_id:
        kind = str(track.get("source_id_kind") or "").strip()
        if kind:
            return f"{kind}:{source_id}"
        return f"source:{source_id}"

    return f"fingerprint:{_track_id(track.get('title', ''), track.get('artist', ''), 0)}"


def _track_id(title: str, artist: str, index: int) -> str:
    digest = hashlib.sha1(f"{artist}\0{title}\0{index}".encode("utf-8")).hexdigest()
    return digest[:12]


def _track_identity(track: dict[str, Any]) -> dict[str, str]:
    return {
        "title": str(track.get("title") or ""),
        "artist": str(track.get("artist") or ""),
        "album": str(track.get("album") or ""),
        "source_key": source_key_for_track(track),
    }


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _format_duration(seconds: int) -> str:
    if not seconds:
        return ""
    minutes, remainder = divmod(seconds, 60)
    return f"{minutes}:{remainder:02d}"


def _best_source(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not candidates:
        return None
    return max(candidates, key=lambda candidate: int(candidate.get("confidence") or 0))


def _source_id_kind(row: dict[str, Any]) -> str:
    if _first_value(row, "Deezer ID"):
        return "deezer"
    if _first_value(row, "Spotify - id", "Spotify ID"):
        return "spotify"
    return ""


def _read_personal_library(
    settings: AppSettings | None = None,
    create_if_missing: bool = True,
) -> tuple[Path, dict[str, Any]]:
    current = settings or load_settings()
    path = resolve_data_dir(current) / "personal_library.json"
    if not path.exists():
        if create_if_missing:
            return path, {"genres": {}, "all_tracks": [], "download_sources": {}}
        return path, {}

    with open(path, "r", encoding="utf-8") as f:
        library = json.load(f)
    library.setdefault("download_sources", {})
    return path, library


def _write_personal_library(path: Path, library: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(library, f, indent=4, ensure_ascii=False)


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _emit(progress_callback: ProgressCallback | None, event: str, **payload: Any) -> None:
    if progress_callback:
        progress_callback({"event": event, **payload})
