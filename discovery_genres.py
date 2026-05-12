import argparse
import logging

from music_discovery_app.genre_service import GenreEnrichmentError, enrich_library


DEFAULT_INPUT_CSV = "personal/My Music Library.csv"
DEFAULT_OUTPUT_CSV = "personal/music_library_with_genres.csv"
USER_AGENT = "MusicLibraryEnricher/1.0 (contact@example.com)"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Enrich music library with genre data.")
    parser.add_argument("--input", default=DEFAULT_INPUT_CSV, help="Input CSV file from export")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_CSV, help="Output CSV file with genres")
    args = parser.parse_args()

    def log_progress(event):
        if event["event"] == "started":
            log.info("Loaded %s tracks from %s", event["total"], args.input)
        elif event["event"] == "progress":
            log.info("[%s/%s] %s", event["current"], event["total"], event["message"])

    try:
        result = enrich_library(args.input, args.output, USER_AGENT, log_progress)
    except GenreEnrichmentError as exc:
        log.error(str(exc))
        return

    log.info("Done! Enriched library saved to %s", result["output_csv"])
    if result["unknown_genres"]:
        log.warning("%s tracks were saved with Unknown genre", result["unknown_genres"])


if __name__ == "__main__":
    main()

