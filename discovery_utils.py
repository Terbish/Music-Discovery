import csv
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Maps track_id -> {"title": ..., "artist": ...}
CsvMetadata = Dict[str, Dict[str, str]]

def parse_csv(csv_path: str) -> Tuple[List[str], CsvMetadata]:
    """
    Parse a music library CSV export.
    Returns:
      - ordered list of unique IDs
      - dict mapping each ID to {"title": ..., "artist": ...}

    Expected columns (case-insensitive matching):
      'Spotify - id'  →  track ID
      'Track name'    →  song title
      'Artist name'   →  artist
    """
    path = Path(csv_path)
    if not path.exists():
        sys.exit(f"❌  CSV file not found: {csv_path}")

    ids: List[str] = []
    metadata: CsvMetadata = {}
    seen: set = set()

    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        fields = reader.fieldnames or []

        def find_col(*keywords: str) -> Optional[str]:
            """Return the first column whose name contains all keywords (case-insensitive)."""
            kw_lower = [k.lower() for k in keywords]
            return next(
                (col for col in fields if all(k in col.lower() for k in kw_lower)),
                None,
            )

        id_col     = find_col("spotify", "id")
        title_col  = find_col("track")
        artist_col = find_col("artist")
        album_col  = find_col("album")

        if id_col is None:
            sys.exit(
                f"❌  Could not find an ID column in {csv_path}.\n"
                f"    Available columns: {fields}"
            )

        for row in reader:
            tid = row[id_col].strip()
            if not tid or tid in seen:
                continue
            ids.append(tid)
            seen.add(tid)
            metadata[tid] = {
                "title":  row[title_col].strip()  if title_col  else "",
                "artist": row[artist_col].strip() if artist_col else "",
                "album":  row[album_col].strip()  if album_col  else "",
            }

    return ids, metadata

def sanitize_filename(name: str) -> str:
    """Sanitize a string to be a safe filename."""
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()
