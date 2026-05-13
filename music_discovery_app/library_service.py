import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable


ProgressCallback = Callable[[dict[str, Any]], None]


class LibraryProcessingError(Exception):
    """Raised when an enriched library CSV cannot be processed."""


def process_library(
    input_csv: str | Path,
    taste_profile_json: str | Path,
    personal_library_json: str | Path,
    progress_callback: ProgressCallback | None = None,
) -> dict[str, Any]:
    """Build taste profile and personal library files from an enriched CSV."""
    input_path = Path(input_csv)
    if not input_path.exists():
        raise LibraryProcessingError(f"Input file not found: {input_path}")

    all_tracks: list[dict[str, Any]] = []
    genre_counts: Counter[str] = Counter()
    artist_counts: Counter[str] = Counter()
    genre_to_tracks: dict[str, list[dict[str, Any]]] = {}

    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        _validate_columns(reader.fieldnames or [], input_path)
        rows = list(reader)

    total = len(rows)
    _emit(progress_callback, "started", current=0, total=total, message="Processing library")

    for index, row in enumerate(rows, 1):
        title = row["title"].strip()
        artist = row["artist"].strip()
        genre_str = row["Genres"].strip()
        service_id = row["Spotify ID"].strip()
        album = row.get("album", "").strip()
        added_date = row.get("added_date", "").strip()
        genres = [g.strip() for g in genre_str.split(",") if g.strip()] if genre_str and genre_str != "Unknown" else []

        track_info = {
            "title": title,
            "artist": artist,
            "album": album,
            "added_date": added_date,
            "genres": genres,
            "track_id": service_id,
        }
        all_tracks.append(track_info)

        for genre in genres:
            genre_counts[genre] += 1
            genre_to_tracks.setdefault(genre, []).append(track_info)

        if artist:
            artist_counts[artist] += 1

        _emit(
            progress_callback,
            "progress",
            current=index,
            total=total,
            message=f"Processed {index} of {total} tracks",
        )

    top_genres = [{"genre": genre, "count": count} for genre, count in genre_counts.most_common(20)]
    top_artists = [{"artist": artist, "count": count} for artist, count in artist_counts.most_common(50)]

    taste_profile = {
        "total_tracks": len(all_tracks),
        "top_genres": top_genres,
        "genre_counts": dict(genre_counts),
        "top_artists": top_artists,
        "artist_counts": dict(artist_counts),
    }
    personal_library = {
        "genres": genre_to_tracks,
        "all_tracks": all_tracks,
        "download_sources": _read_existing_download_sources(library_path),
    }

    taste_path = Path(taste_profile_json)
    library_path = Path(personal_library_json)
    _write_json(taste_path, taste_profile)
    _write_json(library_path, personal_library)

    result = {
        "total_tracks": len(all_tracks),
        "top_genres": top_genres,
        "top_artists": top_artists,
        "outputs": {
            "taste_profile": str(taste_path),
            "personal_library": str(library_path),
        },
    }
    _emit(progress_callback, "succeeded", current=total, total=total, message="Library processed", result=result)
    return result


def _validate_columns(fieldnames: list[str], input_path: Path) -> None:
    required = {"title", "artist", "Genres", "Spotify ID"}
    missing = sorted(required.difference(fieldnames))
    if missing:
        available = ", ".join(fieldnames) if fieldnames else "none"
        raise LibraryProcessingError(
            f"{input_path} is missing required columns: {', '.join(missing)}. Available columns: {available}"
        )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False)


def _read_existing_download_sources(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            existing = json.load(f)
        return existing.get("download_sources", {})
    except (OSError, json.JSONDecodeError):
        return {}


def _emit(progress_callback: ProgressCallback | None, event: str, **payload: Any) -> None:
    if progress_callback:
        progress_callback({"event": event, **payload})
