import csv
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import requests

from music_discovery_app.settings import AppSettings, load_settings, resolve_data_dir


DEFAULT_USER_AGENT = "MusicDiscoveryBot/1.0"
ProgressCallback = Callable[[dict[str, Any]], None]


class DiscoveryServiceError(Exception):
    pass


def create_daily_discovery(
    settings: AppSettings | None = None,
    progress_callback: ProgressCallback | None = None,
) -> dict[str, Any]:
    current = settings or load_settings()
    data_dir = resolve_data_dir(current)
    taste_path = data_dir / "taste_profile.json"
    library_path = data_dir / "personal_library.json"
    output_dir = Path(current.output_path)

    if not taste_path.exists() or not library_path.exists():
        raise DiscoveryServiceError("Taste profile and personal library are required before creating discovery.")

    with open(taste_path, "r", encoding="utf-8") as f:
        taste = json.load(f)
    with open(library_path, "r", encoding="utf-8") as f:
        library = json.load(f)

    existing_tracks = {
        (track.get("title", "").lower(), track.get("artist", "").lower())
        for track in library.get("all_tracks", [])
    }
    genres = [row["genre"] for row in taste.get("top_genres", []) if row.get("count", 0) > 0]
    if not genres:
        raise DiscoveryServiceError("No genres found in the taste profile.")

    random.shuffle(genres)
    limit = max(1, int(current.batch_size or 20))
    selected_tracks: list[dict[str, Any]] = []
    seen_ids = set()

    _emit(progress_callback, "started", current=0, total=limit, message="Creating daily discovery")
    for genre in genres:
        if len(selected_tracks) >= limit:
            break

        _emit(
            progress_callback,
            "progress",
            current=len(selected_tracks),
            total=limit,
            message=f"Searching {genre}",
        )
        tracks = _get_deezer_tracks_by_genre(genre, DEFAULT_USER_AGENT)
        random.shuffle(tracks)

        for track in tracks:
            if len(selected_tracks) >= limit:
                break

            title = track.get("title", "")
            artist = track.get("artist", {}).get("name", "")
            deezer_id = track.get("id")
            if not title or not artist:
                continue
            if (title.lower(), artist.lower()) in existing_tracks or deezer_id in seen_ids:
                continue

            selected_tracks.append(
                {
                    "title": title,
                    "artist": artist,
                    "album": track.get("album", {}).get("title", ""),
                    "Genre (Source)": genre,
                    "Deezer ID": deezer_id,
                    "Preview URL": track.get("preview") or "",
                }
            )
            seen_ids.add(deezer_id)
            _emit(
                progress_callback,
                "progress",
                current=len(selected_tracks),
                total=limit,
                message=f"Selected {len(selected_tracks)} of {limit} tracks",
            )

    if not selected_tracks:
        raise DiscoveryServiceError("No new tracks found for today's discovery.")

    output_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    output_file = output_dir / f"discovery_{today}.csv"
    fieldnames = ["title", "artist", "album", "Genre (Source)", "Deezer ID", "Preview URL"]
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(selected_tracks)

    result = {
        "path": str(output_file),
        "date": today,
        "track_count": len(selected_tracks),
    }
    _emit(progress_callback, "succeeded", current=len(selected_tracks), total=limit, message="Daily discovery created", result=result)
    return result


def _get_deezer_tracks_by_genre(genre_name: str, user_agent: str, limit: int = 50) -> list[dict[str, Any]]:
    try:
        resp = requests.get(
            "https://api.deezer.com/search",
            params={"q": f'genre:"{genre_name}"', "limit": limit},
            headers={"User-Agent": user_agent},
            timeout=10,
        )
        if resp.status_code != 200:
            return []
        return resp.json().get("data", [])
    except Exception:
        return []


def _emit(progress_callback: ProgressCallback | None, event: str, **payload: Any) -> None:
    if progress_callback:
        progress_callback({"event": event, **payload})
