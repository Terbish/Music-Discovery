import argparse
import time
import csv
import logging
import re
import requests
from pathlib import Path
from discovery_utils import parse_csv, sanitize_filename

# ── Configuration ─────────────────────────────────────────────────────────────

DEFAULT_INPUT_CSV = "personal/My Music Library.csv"
DEFAULT_OUTPUT_CSV = "personal/music_library_with_genres.csv"

# User-Agent is REQUIRED by MusicBrainz to avoid being blocked.
USER_AGENT = "MusicLibraryEnricher/1.0 (contact@example.com)"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── API Logic ─────────────────────────────────────────────────────────────────

def clean_search_query(text: str) -> str:
    """
    Remove common suffixes like (feat. ...), [Official Video], etc.
    to improve hit probability for search APIs.
    """
    if not text:
        return ""
    # Remove (feat. ...), (with ...), [feat. ...], [with ...]
    text = re.sub(r"[\(\[](feat\.|with|ft\.|featuring).*?[\)\]]", "", text, flags=re.IGNORECASE)
    # Remove [Official ...], (Official ...)
    text = re.sub(r"[\(\[](official|lyrics|video|mv|hd|visual).?[\)\]]", "", text, flags=re.IGNORECASE)
    # Remove common acoustic/live suffixes
    text = re.sub(r"[\(\[]live.*?[\)\]]", "", text, flags=re.IGNORECASE)
    # Clean up whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text

def get_itunes_genres(artist: str, title: str) -> list[str]:
    """
    Search iTunes for a track and return its primary genre.
    """
    try:
        url = "https://itunes.apple.com/search"
        params = {
            "term": f"{artist} {title}",
            "entity": "song",
            "limit": 1
        }
        # iTunes doesn't require a strict User-Agent but it's good practice
        headers = {"User-Agent": USER_AGENT}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        
        # Respect iTunes rate limit (~20 requests/min = 1 every 3 seconds)
        time.sleep(3.0) 
        
        if resp.status_code != 200:
            return []

        data = resp.json()
        if data.get("resultCount", 0) > 0:
            genre = data["results"][0].get("primaryGenreName")
            return [genre] if genre else []
        return []

    except Exception as e:
        log.debug(f"iTunes error for {artist} - {title}: {e}")
        return []

def get_musicbrainz_genres(artist: str, title: str) -> list[str]:
    """
    Search MusicBrainz for a recording and return granular artist tags (genres).
    """
    try:
        # 1. Search for recording
        query = f'recording:"{title}" AND artist:"{artist}"'
        url = "https://musicbrainz.org/ws/2/recording"
        params = {"query": query, "fmt": "json"}
        headers = {"User-Agent": USER_AGENT}

        resp = requests.get(url, params=params, headers=headers, timeout=10)
        time.sleep(1.0)  # Respect 1 request/sec limit
        
        if resp.status_code != 200:
            return []

        data = resp.json()
        recordings = data.get("recordings", [])
        if not recordings:
            return []

        # Get the first recording's artist ID
        artist_credit = recordings[0].get("artist-credit", [])
        if not artist_credit:
            return []
        
        artist_id = artist_credit[0].get("artist", {}).get("id")
        if not artist_id:
            return []

        # 2. Fetch artist tags
        url = f"https://musicbrainz.org/ws/2/artist/{artist_id}"
        params = {"inc": "tags", "fmt": "json"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        time.sleep(1.0)
        
        if resp.status_code != 200:
            return []

        artist_data = resp.json()
        tags = artist_data.get("tags", [])
        # Return tags with a count >= 1, sorted by count
        tags = [t["name"] for t in tags if t.get("count", 0) >= 0]
        return tags[:5]  # Top 5 tags

    except Exception as e:
        log.debug(f"MusicBrainz error for {artist} - {title}: {e}")
        return []

def get_deezer_genres(artist: str, title: str) -> list[str]:
    """
    Search Deezer for a track and return its album genres as a fallback.
    """
    try:
        query = f'artist:"{artist}" track:"{title}"'
        url = "https://api.deezer.com/search"
        resp = requests.get(url, params={"q": query}, timeout=10)
        
        if resp.status_code != 200:
            return []

        data = resp.json()
        tracks = data.get("data", [])
        if not tracks:
            return []

        album_id = tracks[0].get("album", {}).get("id")
        if not album_id:
            return []

        # Fetch album details for genres
        url = f"https://api.deezer.com/album/{album_id}"
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return []

        album_data = resp.json()
        genres = album_data.get("genres", {}).get("data", [])
        return [g["name"] for g in genres]

    except Exception as e:
        log.debug(f"Deezer error for {artist} - {title}: {e}")
        return []

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Enrich music library with genre data.")
    parser.add_argument("--input", default=DEFAULT_INPUT_CSV, help="Input CSV file from export")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_CSV, help="Output CSV file with genres")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        log.error(f"Input file not found: {args.input}")
        return

    ids, metadata = parse_csv(args.input)
    total = len(ids)
    log.info(f"Loaded {total} tracks from {args.input}")

    enriched_data = []

    for i, tid in enumerate(ids, 1):
        track = metadata[tid]
        raw_artist = track["artist"]
        raw_title = track["title"]
        
        # Clean queries for better matching
        artist = clean_search_query(raw_artist)
        title = clean_search_query(raw_title)

        log.info(f"[{i}/{total}] Searching: {raw_artist} - {raw_title}")
        if artist != raw_artist or title != raw_title:
            log.debug(f"  (Cleaned: {artist} - {title})")

        # Try iTunes first (robust international)
        genres = get_itunes_genres(artist, title)
        
        # Fallback to MusicBrainz (granular)
        if not genres:
            log.debug("  iTunes found nothing, trying MusicBrainz...")
            genres = get_musicbrainz_genres(artist, title)

        # Fallback to Deezer (broad)
        if not genres:
            log.debug("  MusicBrainz found nothing, trying Deezer...")
            genres = get_deezer_genres(artist, title)

        genre_str = ", ".join(genres) if genres else "Unknown"
        track["Genres"] = genre_str
        track["Spotify ID"] = tid
        enriched_data.append(track)

        if not genres:
            log.warning(f"  ⚠️ No genres found for {artist} - {title}")
        else:
            log.info(f"  ✨ Found: {genre_str}")

    # Write results
    output_path = Path(args.output)
    if output_path.is_dir():
        input_name = Path(args.input).stem
        output_path = output_path / f"{input_name}_enriched.csv"
        log.info(f"Output is a directory, using default filename: {output_path.name}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ["title", "artist", "Genres", "Spotify ID"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(enriched_data)

    log.info(f"Done! Enriched library saved to {args.output}")

if __name__ == "__main__":
    main()
