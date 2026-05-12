import argparse
import logging

from music_discovery_app.library_service import LibraryProcessingError, process_library as process_library_service


DEFAULT_INPUT_CSV = "personal/music_library_with_genres.csv"
DEFAULT_TASTE_PROFILE = "personal/taste_profile.json"
DEFAULT_PERSONAL_LIBRARY = "personal/personal_library.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def process_library(input_csv, taste_profile_json, personal_library_json):
    """Process an enriched CSV and return a structured summary."""
    return process_library_service(input_csv, taste_profile_json, personal_library_json)


def main():
    parser = argparse.ArgumentParser(description="Process music library CSV and create taste profile.")
    parser.add_argument("--input", default=DEFAULT_INPUT_CSV, help="Input CSV file with genres")
    parser.add_argument("--taste", default=DEFAULT_TASTE_PROFILE, help="Output taste profile JSON")
    parser.add_argument("--library", default=DEFAULT_PERSONAL_LIBRARY, help="Output personal library JSON")
    args = parser.parse_args()

    try:
        result = process_library(args.input, args.taste, args.library)
    except LibraryProcessingError as exc:
        log.error(str(exc))
        return

    log.info("Taste profile saved to %s", result["outputs"]["taste_profile"])
    log.info("Personal library saved to %s", result["outputs"]["personal_library"])
    log.info("Processed %s tracks", result["total_tracks"])


if __name__ == "__main__":
    main()

