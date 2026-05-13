import json
from dataclasses import asdict
from pathlib import Path
from shutil import copyfile
from typing import Any

from music_discovery_app.dashboard import read_dashboard_data
from music_discovery_app.discovery_service import DiscoveryServiceError, create_daily_discovery
from music_discovery_app.download_service import (
    DownloadServiceError,
    create_library_download_queue,
    download_best_sources,
    download_selected_source,
    read_download_queue,
    search_queue_sources,
    search_youtube_sources,
)
from music_discovery_app.genre_service import GenreEnrichmentError, enrich_library, is_enriched_csv
from music_discovery_app.library_service import LibraryProcessingError, process_library
from music_discovery_app.settings import load_settings, resolve_data_dir, save_settings


class DesktopApi:
    def get_dashboard_data(self) -> dict[str, Any]:
        return _ok(read_dashboard_data())

    def get_download_queue(self) -> dict[str, Any]:
        return _ok(read_download_queue())

    def create_daily_discovery(self) -> dict[str, Any]:
        try:
            result = create_daily_discovery(
                progress_callback=lambda event: self._emit_progress("daily_discovery", event),
            )
            return _ok(result)
        except DiscoveryServiceError as exc:
            return _error(str(exc))

    def add_library_to_download_queue(self) -> dict[str, Any]:
        try:
            return _ok(create_library_download_queue())
        except DownloadServiceError as exc:
            return _error(str(exc))

    def search_download_sources(self, track: dict[str, Any], limit: int = 8) -> dict[str, Any]:
        try:
            return _ok(search_youtube_sources(track, limit))
        except DownloadServiceError as exc:
            return _error(str(exc))

    def search_download_queue_sources(self, tracks: list[dict[str, Any]], limit: int = 8) -> dict[str, Any]:
        try:
            return _ok(
                search_queue_sources(
                    tracks,
                    limit,
                    progress_callback=lambda event: self._emit_progress("source_search", event),
                )
            )
        except DownloadServiceError as exc:
            return _error(str(exc))

    def download_best_sources(self, tracks: list[dict[str, Any]], limit: int = 8) -> dict[str, Any]:
        try:
            return _ok(
                download_best_sources(
                    tracks,
                    limit,
                    progress_callback=lambda event: self._emit_progress("best_source_download", event),
                )
            )
        except DownloadServiceError as exc:
            return _error(str(exc))

    def replace_downloaded_source(self, track: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
        try:
            return _ok(download_selected_source(track, source, replace_existing=True))
        except DownloadServiceError as exc:
            return _error(str(exc))

    def download_selected_source(self, track: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
        try:
            return _ok(download_selected_source(track, source))
        except DownloadServiceError as exc:
            return _error(str(exc))

    def get_settings(self) -> dict[str, Any]:
        return _ok(asdict(load_settings()))

    def save_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        settings = save_settings(payload)
        return _ok(asdict(settings))

    def select_file(self, file_types: tuple[str, ...] | None = None) -> dict[str, Any]:
        import webview

        window = webview.active_window()
        selected = window.create_file_dialog(webview.OPEN_DIALOG, file_types=file_types or ("CSV files (*.csv)", "All files (*.*)"))
        return _ok({"path": selected[0] if selected else None})

    def select_directory(self) -> dict[str, Any]:
        import webview

        window = webview.active_window()
        selected = window.create_file_dialog(webview.FOLDER_DIALOG)
        return _ok({"path": selected[0] if selected else None})

    def process_library(self, input_csv: str | None = None) -> dict[str, Any]:
        settings = load_settings()
        source = Path(input_csv or settings.library_path)
        data_dir = resolve_data_dir(settings)
        enriched_csv = data_dir / "music_library_with_genres.csv"
        taste_profile = data_dir / "taste_profile.json"
        personal_library = data_dir / "personal_library.json"

        try:
            if is_enriched_csv(source):
                if source.resolve() != enriched_csv.resolve():
                    enriched_csv.parent.mkdir(parents=True, exist_ok=True)
                    copyfile(source, enriched_csv)
                enrichment_result = {
                    "input_csv": str(source),
                    "output_csv": str(enriched_csv),
                    "skipped": True,
                }
            else:
                enrichment_result = enrich_library(
                    source,
                    enriched_csv,
                    progress_callback=lambda event: self._emit_progress("enriching_genres", event),
                )

            library_result = process_library(
                enriched_csv,
                taste_profile,
                personal_library,
                progress_callback=lambda event: self._emit_progress("processing_library", event),
            )
        except (GenreEnrichmentError, LibraryProcessingError) as exc:
            return _error(str(exc))

        return _ok(
            {
                "enrichment": enrichment_result,
                "library": library_result,
                "total_tracks": library_result["total_tracks"],
                "outputs": {
                    "enriched_csv": str(enriched_csv),
                    "taste_profile": str(taste_profile),
                    "personal_library": str(personal_library),
                },
            }
        )

    def _emit_progress(self, phase: str, event: dict[str, Any]) -> None:
        payload = json.dumps({"phase": phase, **event})
        script = f"window.dispatchEvent(new CustomEvent('backend-progress', {{ detail: {payload} }}));"

        try:
            import webview

            windows = getattr(webview, "windows", [])
            if windows:
                windows[0].evaluate_js(script)
        except Exception:
            pass


def _ok(data: Any) -> dict[str, Any]:
    return {"ok": True, "data": data}


def _error(message: str) -> dict[str, Any]:
    return {"ok": False, "error": message}
