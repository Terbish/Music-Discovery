import csv
import json
import math
import random
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import requests

from music_discovery_app.settings import AppSettings, load_settings, resolve_data_dir


DEFAULT_USER_AGENT = "MusicDiscoveryBot/1.0"
MAX_DISCOVERY_GENRES = 12
FETCH_LIMIT_PER_GENRE = 75
MIN_STRICT_SCORE = 24
ProgressCallback = Callable[[dict[str, Any]], None]

NOISY_VERSION_PATTERNS = (
    "chillout",
    "karaoke",
    "tribute",
    "cover",
    "made famous by",
    "sound-a-like",
    "sound alike",
    "workout",
    "fitness",
    "lullaby",
    "sleep",
)
HARD_REJECT_PATTERNS = tuple(pattern for pattern in NOISY_VERSION_PATTERNS if pattern != "chillout")

VERSION_WORD_PATTERN = re.compile(
    r"\b(chillout|remix|mix|edit|version|live|karaoke|tribute|cover|instrumental|remaster|rework)\b",
    re.IGNORECASE,
)


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

    existing_tracks = set()
    for track in library.get("all_tracks", []):
        existing_tracks.update(_track_lookup_keys(track.get("title", ""), track.get("artist", "")))
    avoided_tracks = _read_avoided_track_keys(library, output_dir)
    top_genres = [row for row in taste.get("top_genres", []) if row.get("genre") and row.get("count", 0) > 0]
    genres = [row["genre"] for row in top_genres]
    if not genres:
        raise DiscoveryServiceError("No genres found in the taste profile.")

    genre_counts = {row["genre"]: int(row.get("count") or 0) for row in top_genres}
    genre_ranks = {row["genre"]: index for index, row in enumerate(top_genres)}
    random.shuffle(genres)
    limit = max(1, int(current.batch_size or 20))
    candidates: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_pool_keys: set[tuple[str, str]] = set()
    max_per_genre = max(2, min(4, math.ceil(limit / 4)))
    max_per_artist = 1
    max_per_album = 1
    max_per_version_bucket = 2

    _emit(progress_callback, "started", current=0, total=limit, message="Creating daily discovery")
    discovery_genres = genres[:MAX_DISCOVERY_GENRES]
    for index, genre in enumerate(discovery_genres, 1):
        if len(candidates) >= limit * 8:
            break

        _emit(
            progress_callback,
            "progress",
            current=min(len(candidates), limit),
            total=limit,
            message=f"Searching {genre} ({index} of {len(discovery_genres)})",
        )
        tracks = _get_deezer_tracks_by_genre(genre, DEFAULT_USER_AGENT, limit=FETCH_LIMIT_PER_GENRE)
        random.shuffle(tracks)

        for track in tracks:
            title = track.get("title", "")
            artist = track.get("artist", {}).get("name", "")
            deezer_id = track.get("id")
            if not title or not artist:
                continue
            track_keys = _track_lookup_keys(title, artist)
            pool_key = (_normalize(str(title or "")), _normalize(str(artist or "")))
            if existing_tracks.intersection(track_keys) or avoided_tracks.intersection(track_keys) or pool_key in seen_pool_keys:
                continue
            if deezer_id and str(deezer_id) in seen_ids:
                continue
            if _looks_low_quality_title(title, artist):
                continue

            candidate = _candidate_from_deezer_track(
                track,
                source_genre=genre,
                genre_counts=genre_counts,
                genre_ranks=genre_ranks,
            )
            candidates.append(candidate)
            seen_pool_keys.add(pool_key)
            if deezer_id:
                seen_ids.add(str(deezer_id))

    selected_tracks = _select_diverse_tracks(
        candidates,
        limit=limit,
        max_per_genre=max_per_genre,
        max_per_artist=max_per_artist,
        max_per_album=max_per_album,
        max_per_version_bucket=max_per_version_bucket,
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


def _candidate_from_deezer_track(
    track: dict[str, Any],
    source_genre: str,
    genre_counts: dict[str, int],
    genre_ranks: dict[str, int],
) -> dict[str, Any]:
    title = str(track.get("title") or "").strip()
    artist = str(track.get("artist", {}).get("name") or "").strip()
    album = str(track.get("album", {}).get("title") or "").strip()
    rank = _safe_int(track.get("rank"))
    score = _candidate_score(
        title=title,
        artist=artist,
        album=album,
        source_genre=source_genre,
        preview_url=str(track.get("preview") or ""),
        rank=rank,
        genre_counts=genre_counts,
        genre_ranks=genre_ranks,
    )
    return {
        "title": title,
        "artist": artist,
        "album": album,
        "Genre (Source)": source_genre,
        "Deezer ID": track.get("id"),
        "Preview URL": track.get("preview") or "",
        "_score": score,
        "_artist_key": _normalize(artist),
        "_album_key": _normalize(f"{artist} {album}") if album else "",
        "_version_bucket": _version_bucket(title),
    }


def _candidate_score(
    *,
    title: str,
    artist: str,
    album: str,
    source_genre: str,
    preview_url: str,
    rank: int,
    genre_counts: dict[str, int],
    genre_ranks: dict[str, int],
) -> int:
    score = 20
    max_count = max(genre_counts.values(), default=1)
    source_count = genre_counts.get(source_genre, 0)
    score += round(18 * math.sqrt(source_count / max_count)) if source_count else 0

    genre_rank = genre_ranks.get(source_genre, len(genre_ranks))
    score += max(0, 12 - genre_rank)

    if preview_url:
        score += 8
    if rank:
        score += min(18, round(math.log10(max(rank, 1)) * 4))
    if album:
        score += 3

    haystack = f"{title} {artist} {album}".lower()
    if any(pattern in haystack for pattern in NOISY_VERSION_PATTERNS):
        score -= 18
    if VERSION_WORD_PATTERN.search(title):
        score -= 6
    if len(_normalize(title).split()) <= 1:
        score -= 4

    return score


def _select_diverse_tracks(
    candidates: list[dict[str, Any]],
    *,
    limit: int,
    max_per_genre: int,
    max_per_artist: int,
    max_per_album: int,
    max_per_version_bucket: int,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    genre_counts: Counter[str] = Counter()
    artist_counts: Counter[str] = Counter()
    album_counts: Counter[str] = Counter()
    version_counts: Counter[str] = Counter()

    for candidate in sorted(candidates, key=lambda item: item["_score"], reverse=True):
        if len(selected) >= limit:
            break
        if candidate["_score"] < MIN_STRICT_SCORE:
            continue

        genre = candidate["Genre (Source)"]
        artist_key = candidate["_artist_key"]
        album_key = candidate["_album_key"]
        version_bucket = candidate["_version_bucket"]

        if genre_counts[genre] >= max_per_genre:
            continue
        if artist_key and artist_counts[artist_key] >= max_per_artist:
            continue
        if album_key and album_counts[album_key] >= max_per_album:
            continue
        if version_bucket and version_counts[version_bucket] >= max_per_version_bucket:
            continue

        selected.append(_public_track(candidate))
        genre_counts[genre] += 1
        if artist_key:
            artist_counts[artist_key] += 1
        if album_key:
            album_counts[album_key] += 1
        if version_bucket:
            version_counts[version_bucket] += 1

    if len(selected) >= limit:
        return selected

    # If strict caps cannot fill a batch, allow a little more depth without
    # letting one noisy genre or repeated version label dominate the queue.
    relaxed_genre_cap = max(max_per_genre + 1, math.ceil(limit / 3))
    selected_keys = {_track_key(track["title"], track["artist"]) for track in selected}
    for candidate in sorted(candidates, key=lambda item: item["_score"], reverse=True):
        if len(selected) >= limit:
            break
        track_key = _track_key(candidate["title"], candidate["artist"])
        if track_key in selected_keys:
            continue

        genre = candidate["Genre (Source)"]
        artist_key = candidate["_artist_key"]
        version_bucket = candidate["_version_bucket"]
        if genre_counts[genre] >= relaxed_genre_cap:
            continue
        if artist_key and artist_counts[artist_key] >= max_per_artist:
            continue
        if version_bucket and version_counts[version_bucket] >= max_per_version_bucket + 1:
            continue

        selected.append(_public_track(candidate))
        selected_keys.add(track_key)
        genre_counts[genre] += 1
        if artist_key:
            artist_counts[artist_key] += 1
        if version_bucket:
            version_counts[version_bucket] += 1

    return selected


def _public_track(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": candidate["title"],
        "artist": candidate["artist"],
        "album": candidate["album"],
        "Genre (Source)": candidate["Genre (Source)"],
        "Deezer ID": candidate["Deezer ID"],
        "Preview URL": candidate["Preview URL"],
    }


def _read_avoided_track_keys(library: dict[str, Any], output_dir: Path) -> set[tuple[str, str]]:
    avoided = set()
    for record in library.get("download_sources", {}).values():
        if not record.get("no_sources"):
            continue
        track = record.get("track") or {}
        avoided.update(_track_lookup_keys(track.get("title", ""), track.get("artist", "")))

    if not output_dir.exists():
        return avoided

    for path in output_dir.glob("discovery_*.csv"):
        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    avoided.update(_track_lookup_keys(row.get("title", ""), row.get("artist", "")))
        except OSError:
            continue
    return avoided


def _looks_low_quality_title(title: str, artist: str) -> bool:
    haystack = f"{title} {artist}".lower()
    if any(pattern in haystack for pattern in HARD_REJECT_PATTERNS):
        return True
    if re.search(r"\b(as made famous by|originally performed by|backing track)\b", haystack):
        return True
    return False


def _version_bucket(title: str) -> str:
    matches = VERSION_WORD_PATTERN.findall(title)
    if not matches:
        return ""
    normalized = sorted({_normalize(match) for match in matches if _normalize(match)})
    return " ".join(normalized)


def _track_key(title: Any, artist: Any) -> tuple[str, str, str]:
    normalized_title = _normalize(str(title or ""))
    normalized_artist = _normalize(str(artist or ""))
    base_title = _normalize(re.sub(r"\([^)]*\)|\[[^]]*\]", " ", str(title or "")))
    return normalized_title, normalized_artist, base_title


def _track_lookup_keys(title: Any, artist: Any) -> set[tuple[str, str]]:
    normalized_artist = _normalize(str(artist or ""))
    normalized_title, _, base_title = _track_key(title, artist)
    if not normalized_title or not normalized_artist:
        return set()
    keys = {(normalized_title, normalized_artist)}
    if base_title and base_title != normalized_title:
        keys.add((base_title, normalized_artist))
    return keys


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _emit(progress_callback: ProgressCallback | None, event: str, **payload: Any) -> None:
    if progress_callback:
        progress_callback({"event": event, **payload})
