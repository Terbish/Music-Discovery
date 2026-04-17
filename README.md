# 🎵 Daily Discovery Album Tools

A powerful suite of Python scripts designed to bridge the gap between your online music library and local music discovery. This project allows you to enrich your exported library with granular genre metadata, analyze your unique "Taste Profile," and automatically discover and download new tracks that match your preferences.

## 🚀 Key Features

-   **Genre Enrichment**: Automatically fetches high-quality genre tags using MusicBrainz and Deezer APIs.
-   **Taste Profiling**: Analyzes your library to identify top genres and artists, creating a data-driven profile of your musical identity.
-   **Automated Discovery**: Generates daily batches of new track recommendations based on your profile, avoiding songs you already own.
-   **Audio Integration**: Searches YouTube and downloads high-quality audio (MP3/FLAC) with **automated metadata tagging** (Artist, Album, Title).
-   **Open Source Optimized**: No hardcoded paths, full CLI parameter support, and clear separation of personal data.
-   **Universal Compatibility**: Compatible with Python 3.9+ and robust binary resolution for macOS.

---

## 🛠 Prerequisites

-   **Python 3.9+** (Legacy support included)
-   **[uv](https://github.com/astral-sh/uv)**: A fast Python package installer and resolver.
-   **[ffmpeg](https://ffmpeg.org/)**: Required for audio extraction and metadata tagging (e.g., `brew install ffmpeg` on macOS).

---

## 📥 Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-repo/daily-discovery-tools.git
    cd daily-discovery-tools
    ```

2.  Install dependencies using `uv` (or `pip`):
    ```bash
    uv sync
    # OR
    python3 -m pip install -r requirements.txt
    ```

---

## 🔄 The Discovery Workflow

All personal data stays in the `personal/` directory, which is ignored by git.

### 1. Export & Enrich
Place your music library CSV export in the `personal/` folder.
```bash
uv run discovery_genres.py --input "personal/My Music Library.csv"
```
*Default Output: `personal/music_library_with_genres.csv`*

### 2. Analyze Taste
Process the enriched library to generate your personal taste profile:
```bash
uv run process_library.py
```
*Default Outputs: `personal/taste_profile.json` and `personal/personal_library.json`*

### 3. Automated Discovery
Generate and download your daily discovery batch (now with automatic metadata tagging):
```bash
uv run daily_discovery.py
```
*Default Outputs: `personal/discovery/discovery_YYYY-MM-DD.csv` and audio in `personal/discovery/YYYY-MM-DD/`*

---

## 📖 Script Reference

### `discovery_to_audio.py`
A standalone tool to download specific tracks or entire CSV lists with automatic metadata tagging.
-   **Usage**: `uv run discovery_to_audio.py [TRACK_IDS...]`
-   **Key Arguments**:
    -   `-c, --csv`: Path to a library CSV (default: `personal/music_library_with_genres.csv`).
    -   `-o, --output`: Target directory (default: `personal/audio_output`).
    -   `-f, --format`: Output format (mp3, flac, wav, etc.).

### `discovery_genres.py`
Enriches CSV metadata using MusicBrainz and Deezer.
-   **Arguments**:
    -   `--input`: Path to your exported music CSV.
    -   `--output`: Path to save the enriched CSV.

### `process_library.py`
Generates your "Taste Profile" from the enriched music CSV.
-   **Arguments**:
    -   `--input`: Enriched CSV path.
    -   `--taste`: Output path for `taste_profile.json`.
    -   `--library`: Output path for `personal_library.json`.

### `daily_discovery.py`
The daily automation script for finding new music.
-   **Arguments**:
    -   `--limit`: Number of tracks to discover (default: 20).
    -   `--output`: Directory for results (default: `personal/discovery`).

---

## 📂 Project Structure

-   `personal/`: **Git-ignored** directory for all your music data and preferences.
-   `audio_utils.py`: Shared logic for yt-dlp and ffmpeg integration.
-   `discovery_utils.py`: CSV parsing and filename sanitization.

---

> [!NOTE]
> This project does **not** require any private API Key. It uses public metadata endpoints and web scraping fallback logic.
