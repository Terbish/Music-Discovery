import argparse
import csv
import json
import logging
from collections import Counter
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

DEFAULT_INPUT_CSV = "personal/music_library_with_genres.csv"
DEFAULT_TASTE_PROFILE = "personal/taste_profile.json"
DEFAULT_PERSONAL_LIBRARY = "personal/personal_library.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Processing Logic ──────────────────────────────────────────────────────────

def process_library(input_csv, taste_profile_json, personal_library_json):
    input_path = Path(input_csv)
    if not input_path.exists():
        log.error(f"Input file not found: {input_csv}")
        return

    log.info(f"Processing genres from {input_csv}...")

    all_tracks = []
    genre_counts = Counter()
    artist_counts = Counter()
    genre_to_tracks = {}

    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row["title"].strip()
            artist = row["artist"].strip()
            genre_str = row["Genres"].strip()
            service_id = row["Spotify ID"].strip() # User requested keeping column name the same

            # Handle multiple genres (comma-separated)
            genres = [g.strip() for g in genre_str.split(",")] if genre_str and genre_str != "Unknown" else []
            
            track_info = {
                "title": title,
                "artist": artist,
                "genres": genres,
                "track_id": service_id
            }
            all_tracks.append(track_info)

            for g in genres:
                genre_counts[g] += 1
                if g not in genre_to_tracks:
                    genre_to_tracks[g] = []
                genre_to_tracks[g].append(track_info)
            
            artist_counts[artist] += 1

    # ... (Create Taste Profile and Personal Library sections remain the same)
    # 1. Create Taste Profile
    # Sort genres by frequency, keep top 20
    top_genres = [
        {"genre": g, "count": count} 
        for g, count in genre_counts.most_common(20)
    ]
    
    # Sort artists by frequency, keep top 50
    top_artists = [
        {"artist": a, "count": count}
        for a, count in artist_counts.most_common(50)
    ]
    
    taste_profile = {
        "total_tracks": len(all_tracks),
        "top_genres": top_genres,
        "genre_counts": dict(genre_counts),
        "top_artists": top_artists,
        "artist_counts": dict(artist_counts)
    }

    taste_path = Path(taste_profile_json)
    taste_path.parent.mkdir(parents=True, exist_ok=True)
    with open(taste_path, "w", encoding="utf-8") as f:
        json.dump(taste_profile, f, indent=4, ensure_ascii=False)
    log.info(f"✨ Taste profile saved to {taste_profile_json}")

    # 2. Create Personal Library (Categorized)
    personal_library = {
        "genres": genre_to_tracks,
        "all_tracks": all_tracks
    }

    lib_path = Path(personal_library_json)
    lib_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lib_path, "w", encoding="utf-8") as f:
        json.dump(personal_library, f, indent=4, ensure_ascii=False)
    log.info(f"✨ Personal library categories saved to {personal_library_json}")

def main():
    parser = argparse.ArgumentParser(description="Process music library CSV and create taste profile.")
    parser.add_argument("--input", default=DEFAULT_INPUT_CSV, help="Input CSV file with genres")
    parser.add_argument("--taste", default=DEFAULT_TASTE_PROFILE, help="Output taste profile JSON")
    parser.add_argument("--library", default=DEFAULT_PERSONAL_LIBRARY, help="Output personal library JSON")
    args = parser.parse_args()

    process_library(args.input, args.taste, args.library)

if __name__ == "__main__":
    main()
