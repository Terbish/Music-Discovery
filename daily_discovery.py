import argparse
import json
import logging
import random
import requests
import csv
from datetime import datetime
from pathlib import Path
from audio_utils import download_audio
from discovery_utils import sanitize_filename


# ── Configuration ─────────────────────────────────────────────────────────────

DEFAULT_TASTE_PROFILE = "personal/taste_profile.json"
DEFAULT_PERSONAL_LIBRARY = "personal/personal_library.json"
DEFAULT_OUTPUT_DIR = "personal/discovery"
DEFAULT_USER_AGENT = "MusicDiscoveryBot/1.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Discovery Logic ───────────────────────────────────────────────────────────

def get_deezer_tracks_by_genre(genre_name: str, user_agent: str, limit: int = 50) -> list:
    """Search Deezer for tracks in a specific genre."""
    try:
        url = "https://api.deezer.com/search"
        # Using genre tag in query
        params = {"q": f'genre:"{genre_name}"', "limit": limit}
        resp = requests.get(url, params=params, headers={"User-Agent": user_agent}, timeout=10)
        
        if resp.status_code != 200:
            return []
            
        data = resp.json()
        return data.get("data", [])
    except Exception as e:
        log.error(f"Error fetching tracks for genre {genre_name}: {e}")
        return []

def run_discovery(taste_profile, personal_library, output_dir, user_agent, limit=20):
    # 1. Load context
    taste_path = Path(taste_profile)
    lib_path = Path(personal_library)
    
    if not taste_path.exists() or not lib_path.exists():
        log.error("Taste profile or personal library missing. Run process_library.py first.")
        return

    with open(taste_path, "r", encoding="utf-8") as f:
        taste = json.load(f)
    
    with open(lib_path, "r", encoding="utf-8") as f:
        library = json.load(f)

    # Build a set of existing titles + artists for fast filtering
    existing_tracks = {
        (t["title"].lower(), t["artist"].lower()) 
        for t in library["all_tracks"]
    }
    
    log.info(f"Loaded library with {len(existing_tracks)} unique track-artist pairs.")

    # 2. Select genres for discovery
    # We'll pick top genres, but shuffle them slightly or pick from top 10
    top_genres_metadata = taste.get("top_genres", [])
    if not top_genres_metadata:
        log.warning("No genres found in taste profile.")
        return

    # Use genres that have at least some representation
    eligible_genres = [g["genre"] for g in top_genres_metadata if g["count"] > 0]
    
    selected_tracks = []
    seen_ids = set()

    # Iterate until we have our limit tracks or exhaust genres
    # To mimic "Daily Mix", we shuffle the eligible genres to get different focus each day
    random.shuffle(eligible_genres)
    
    log.info(f"Starting discovery across genres: {', '.join(eligible_genres[:5])}...")

    for genre in eligible_genres:
        if len(selected_tracks) >= limit:
            break
            
        log.info(f"  Searching '{genre}'...")
        tracks = get_deezer_tracks_by_genre(genre, user_agent)
        random.shuffle(tracks) # Randomize results within the genre

        for t in tracks:
            if len(selected_tracks) >= limit:
                break
                
            title = t.get("title", "")
            artist = t.get("artist", {}).get("name", "")
            deezer_id = t.get("id")
            
            # Check if already in library
            if (title.lower(), artist.lower()) in existing_tracks:
                continue
            
            # Check if already picked for this session
            if deezer_id in seen_ids:
                continue
                
            track_entry = {
                "title": title,
                "artist": artist,
                "Genre (Source)": genre,
                "Deezer ID": deezer_id,
                "Preview URL": t.get("preview")
            }
            
            selected_tracks.append(track_entry)
            seen_ids.add(deezer_id)

    # 3. Save CSV results
    if not selected_tracks:
        log.warning("No new tracks found matching your taste profile today.")
        return

    out_path = Path(output_dir)
    out_path.mkdir(exist_ok=True, parents=True)
    today = datetime.now().strftime("%Y-%m-%d")
    output_file = out_path / f"discovery_{today}.csv"

    fieldnames = ["title", "artist", "Genre (Source)", "Deezer ID", "Preview URL"]
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(selected_tracks)

    log.info(f"💾 Discovery list saved to {output_file}")

    # 4. Download audio for each selected track
    date_folder = out_path / today
    date_folder.mkdir(parents=True, exist_ok=True)
    
    log.info(f"Starting downloads into {date_folder}...")
    
    success_count = 0
    for i, track in enumerate(selected_tracks, 1):
        artist = track["artist"]
        title = track["title"]
        
        query = f"{artist} - {title} official audio"
        safe_filename = sanitize_filename(f"{artist} - {title}")
        output_path = date_folder / f"{safe_filename}.mp3"
        
        log.info(f"[{i}/{limit}] Downloading: {artist} - {title}")
        
        if output_path.exists():
            log.info(f"  ⏭  Already exists, skipping: {output_path.name}")
            success_count += 1
            continue
            
        ok = download_audio(query, output_path, quiet=True)
        if ok:
            success_count += 1
            log.info(f"  ✅  Saved: {output_path.name}")
        else:
            log.warning(f"  ❌  Failed to download: {artist} - {title}")

    log.info(f"✅ Discovery complete! {success_count}/{len(selected_tracks)} tracks downloaded.")

def main():
    parser = argparse.ArgumentParser(description="Find and download new music based on your taste profile.")
    parser.add_argument("--taste", default=DEFAULT_TASTE_PROFILE, help="Path to taste_profile.json")
    parser.add_argument("--library", default=DEFAULT_PERSONAL_LIBRARY, help="Path to personal_library.json")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_DIR, help="Directory to save discovery results")
    parser.add_argument("--agent", default=DEFAULT_USER_AGENT, help="User-Agent for API requests")
    parser.add_argument("--limit", type=int, default=20, help="Number of tracks to discover")
    args = parser.parse_args()

    run_discovery(args.taste, args.library, args.output, args.agent, args.limit)

if __name__ == "__main__":
    main()
