import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from music_discovery_app.settings import AppSettings, environment_status, load_settings, resolve_data_dir


def read_dashboard_data(settings: AppSettings | None = None) -> dict[str, Any]:
    current = settings or load_settings()
    data_dir = resolve_data_dir(current)
    taste_path = data_dir / "taste_profile.json"
    library_path = data_dir / "personal_library.json"
    discovery_dir = Path(current.output_path)

    taste = _read_json(taste_path, {})
    library = _read_json(library_path, {})
    discoveries = _read_discovery_batches(discovery_dir)

    top_genre = None
    if taste.get("top_genres"):
        top_genre = taste["top_genres"][0]

    pending_downloads = sum(batch["track_count"] for batch in discoveries if not batch["audio_folder_exists"])
    recent_activity = _recent_activity(data_dir, discovery_dir, taste_path, library_path, discoveries)

    return {
        "settings": current.__dict__,
        "paths": {
            "data_dir": str(data_dir),
            "taste_profile": str(taste_path),
            "personal_library": str(library_path),
            "discovery_dir": str(discovery_dir),
        },
        "stats": {
            "library_size": int(taste.get("total_tracks") or len(library.get("all_tracks", []))),
            "top_genre": top_genre,
            "genre_count": len(taste.get("genre_counts", {})),
            "artist_count": len(taste.get("artist_counts", {})),
            "discovery_batches": len(discoveries),
            "pending_downloads": pending_downloads,
        },
        "top_genres": taste.get("top_genres", [])[:8],
        "top_artists": taste.get("top_artists", [])[:8],
        "discovery_batches": discoveries[:5],
        "recent_activity": recent_activity,
        "environment": environment_status(),
        "needs_setup": not taste_path.exists() or not library_path.exists(),
    }


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _read_discovery_batches(discovery_dir: Path) -> list[dict[str, Any]]:
    if not discovery_dir.exists():
        return []

    batches = []
    for csv_path in sorted(discovery_dir.glob("discovery_*.csv"), key=lambda path: path.stat().st_mtime, reverse=True):
        date_value = csv_path.stem.replace("discovery_", "")
        audio_folder = discovery_dir / date_value
        batches.append(
            {
                "date": date_value,
                "path": str(csv_path),
                "track_count": _count_csv_rows(csv_path),
                "audio_folder_exists": audio_folder.exists(),
                "modified_at": _format_timestamp(csv_path.stat().st_mtime),
            }
        )
    return batches


def _count_csv_rows(path: Path) -> int:
    with open(path, newline="", encoding="utf-8") as f:
        return sum(1 for _ in csv.DictReader(f))


def _recent_activity(
    data_dir: Path,
    discovery_dir: Path,
    taste_path: Path,
    library_path: Path,
    discoveries: list[dict[str, Any]],
) -> list[dict[str, str]]:
    candidates: list[tuple[float, str, str, Path]] = []
    for label, path in (
        ("Taste profile generated", taste_path),
        ("Personal library generated", library_path),
        ("Data directory ready", data_dir),
        ("Discovery directory ready", discovery_dir),
    ):
        if path.exists():
            candidates.append((path.stat().st_mtime, label, str(path), path))

    for batch in discoveries:
        path = Path(batch["path"])
        if path.exists():
            candidates.append((path.stat().st_mtime, f"Discovery batch {batch['date']}", str(path), path))

    return [
        {
            "label": label,
            "path": path_text,
            "when": _format_timestamp(timestamp),
        }
        for timestamp, label, path_text, _ in sorted(candidates, reverse=True)[:6]
    ]


def _format_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")

