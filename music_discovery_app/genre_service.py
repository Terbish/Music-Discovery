import csv
import logging
import re
import time
from pathlib import Path
from typing import Any, Callable

import requests

from discovery_utils import parse_csv


DEFAULT_USER_AGENT = "MusicLibraryEnricher/1.0 (contact@example.com)"
ENRICHED_COLUMNS = {"title", "artist", "Genres", "Spotify ID"}
ENRICHED_FIELDNAMES = ["title", "artist", "album", "added_date", "Genres", "Spotify ID"]
ProgressCallback = Callable[[dict[str, Any]], None]

log = logging.getLogger(__name__)


class GenreEnrichmentError(Exception):
    """Raised when a library CSV cannot be enriched with genres."""


def is_enriched_csv(csv_path: str | Path) -> bool:
    path = Path(csv_path)
    if not path.exists():
        return False

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return ENRICHED_COLUMNS.issubset(set(reader.fieldnames or []))


def enrich_library(
    input_csv: str | Path,
    output_csv: str | Path,
    user_agent: str = DEFAULT_USER_AGENT,
    progress_callback: ProgressCallback | None = None,
) -> dict[str, Any]:
    """Enrich an exported library CSV and write the app's canonical CSV format."""
    input_path = Path(input_csv)
    if not input_path.exists():
        raise GenreEnrichmentError(f"Input file not found: {input_path}")

    output_path = _resolve_output_path(input_path, Path(output_csv))

    try:
        ids, metadata = parse_csv(str(input_path))
    except SystemExit as exc:
        raise GenreEnrichmentError(str(exc)) from exc

    total = len(ids)
    enriched_data = []
    unknown_count = 0
    _emit(progress_callback, "started", current=0, total=total, message="Enriching genres")

    for index, track_id in enumerate(ids, 1):
        track = metadata[track_id]
        raw_artist = track["artist"]
        raw_title = track["title"]
        artist = clean_search_query(raw_artist)
        title = clean_search_query(raw_title)

        genres = get_itunes_genres(artist, title, user_agent)
        if not genres:
            genres = get_musicbrainz_genres(artist, title, user_agent)
        if not genres:
            genres = get_deezer_genres(artist, title)

        if not genres:
            unknown_count += 1

        enriched_data.append(
            {
                "title": raw_title,
                "artist": raw_artist,
                "album": track.get("album", ""),
                "added_date": track.get("added_date", ""),
                "Genres": ", ".join(genres) if genres else "Unknown",
                "Spotify ID": track_id,
            }
        )
        _emit(
            progress_callback,
            "progress",
            current=index,
            total=total,
            message=f"Enriched {index} of {total} tracks",
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ENRICHED_FIELDNAMES)
        writer.writeheader()
        writer.writerows(enriched_data)

    result = {
        "input_csv": str(input_path),
        "output_csv": str(output_path),
        "total_tracks": total,
        "unknown_genres": unknown_count,
    }
    _emit(progress_callback, "succeeded", current=total, total=total, message="Genre enrichment complete", result=result)
    return result


def clean_search_query(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"[\(\[](feat\.|with|ft\.|featuring).*?[\)\]]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[\(\[](official|lyrics|video|mv|hd|visual).?[\)\]]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[\(\[]live.*?[\)\]]", "", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


def get_itunes_genres(artist: str, title: str, user_agent: str = DEFAULT_USER_AGENT) -> list[str]:
    try:
        resp = requests.get(
            "https://itunes.apple.com/search",
            params={"term": f"{artist} {title}", "entity": "song", "limit": 1},
            headers={"User-Agent": user_agent},
            timeout=10,
        )
        time.sleep(3.0)
        if resp.status_code != 200:
            return []

        data = resp.json()
        if data.get("resultCount", 0) > 0:
            genre = data["results"][0].get("primaryGenreName")
            return [genre] if genre else []
        return []
    except Exception as exc:
        log.debug("iTunes error for %s - %s: %s", artist, title, exc)
        return []


def get_musicbrainz_genres(artist: str, title: str, user_agent: str = DEFAULT_USER_AGENT) -> list[str]:
    try:
        resp = requests.get(
            "https://musicbrainz.org/ws/2/recording",
            params={"query": f'recording:"{title}" AND artist:"{artist}"', "fmt": "json"},
            headers={"User-Agent": user_agent},
            timeout=10,
        )
        time.sleep(1.0)
        if resp.status_code != 200:
            return []

        recordings = resp.json().get("recordings", [])
        if not recordings:
            return []

        artist_credit = recordings[0].get("artist-credit", [])
        artist_id = artist_credit[0].get("artist", {}).get("id") if artist_credit else None
        if not artist_id:
            return []

        resp = requests.get(
            f"https://musicbrainz.org/ws/2/artist/{artist_id}",
            params={"inc": "tags", "fmt": "json"},
            headers={"User-Agent": user_agent},
            timeout=10,
        )
        time.sleep(1.0)
        if resp.status_code != 200:
            return []

        tags = resp.json().get("tags", [])
        return [tag["name"] for tag in tags if tag.get("count", 0) >= 0][:5]
    except Exception as exc:
        log.debug("MusicBrainz error for %s - %s: %s", artist, title, exc)
        return []


def get_deezer_genres(artist: str, title: str) -> list[str]:
    try:
        resp = requests.get(
            "https://api.deezer.com/search",
            params={"q": f'artist:"{artist}" track:"{title}"'},
            timeout=10,
        )
        if resp.status_code != 200:
            return []

        tracks = resp.json().get("data", [])
        if not tracks:
            return []

        album_id = tracks[0].get("album", {}).get("id")
        if not album_id:
            return []

        resp = requests.get(f"https://api.deezer.com/album/{album_id}", timeout=10)
        if resp.status_code != 200:
            return []

        genres = resp.json().get("genres", {}).get("data", [])
        return [genre["name"] for genre in genres]
    except Exception as exc:
        log.debug("Deezer error for %s - %s: %s", artist, title, exc)
        return []


def _resolve_output_path(input_path: Path, output_path: Path) -> Path:
    if output_path.is_dir():
        return output_path / f"{input_path.stem}_enriched.csv"
    return output_path


def _emit(progress_callback: ProgressCallback | None, event: str, **payload: Any) -> None:
    if progress_callback:
        progress_callback({"event": event, **payload})
