import json
from dataclasses import asdict
from pathlib import Path
from shutil import copyfile
from typing import Any

from music_discovery_app.dashboard import read_dashboard_data
from music_discovery_app.genre_service import GenreEnrichmentError, enrich_library, is_enriched_csv
from music_discovery_app.library_service import LibraryProcessingError, process_library
from music_discovery_app.settings import load_settings, resolve_data_dir, save_settings


class DesktopApi:
    def get_dashboard_data(self) -> dict[str, Any]:
        return _ok(read_dashboard_data())

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
