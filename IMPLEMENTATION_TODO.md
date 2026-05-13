# Cross-Platform Desktop App Implementation Todo

This plan turns `ui-mock.html` into a Windows/macOS desktop app while preserving the existing Python music discovery workflow.

## 1. Define App Scope

- [ ] Confirm the first desktop release targets Windows and macOS.
- [ ] Confirm the desktop shell choice: `pywebview` recommended for this repo.
- [ ] Decide whether Linux support is out of scope for v1.
- [ ] Define the app name, bundle identifier, version, and icon requirements.
- [ ] Define which workflows must work offline after setup.
- [ ] Document external runtime requirements, especially `ffmpeg`.

Acceptance:

- [ ] A short product scope exists for v1.
- [ ] Required platforms, packaging formats, and core workflows are agreed.

## 2. Refactor Python Scripts Into Services

- [x] Keep existing CLI scripts working.
- [x] Move reusable logic from `discovery_genres.py` into a callable genre enrichment service.
- [x] Move reusable logic from `process_library.py` into a callable library processing service.
- [x] Move reusable logic from `daily_discovery.py` into a callable discovery service.
- [x] Move reusable logic from `discovery_to_audio.py` into a callable download service.
- [ ] Standardize return values as structured dictionaries/lists instead of printed output.
- [ ] Standardize error handling with clear exception types or error result objects.
- [ ] Add progress callbacks for long-running tasks.

Acceptance:

- [ ] The app can call import, enrichment, profile generation, discovery, and download workflows from Python functions.
- [ ] Existing CLI commands still run successfully.

## 3. Add App Data And Settings Layer

- [x] Create a settings model for library path, output path, audio format, batch size, startup behavior, tray behavior, and notifications.
- [x] Store settings in the OS-appropriate user config directory.
- [ ] Store user-generated music data in an OS-appropriate user data directory by default.
- [x] Keep support for the current repo-local `personal/` directory during development.
- [ ] Add migration or fallback behavior for existing `personal/` files.
- [ ] Add helper functions for resolving `ffmpeg`, `yt-dlp`, and writable output folders.

Acceptance:

- [x] Settings persist across app launches.
- [ ] The app can locate existing local data and create missing directories.

## 4. Build Desktop Bridge

- [x] Add `pywebview` as the desktop shell dependency.
- [x] Create a desktop entry point, for example `desktop_app.py`.
- [x] Expose a Python API object to the frontend.
- [x] Add API methods for reading dashboard data.
- [x] Add API methods for selecting files and directories through native dialogs.
- [ ] Add API methods for import, enrich, process, discover, and download actions.
- [x] Add API methods for reading the download queue, searching source candidates, and downloading a selected source.
- [x] Add API methods for reading and saving settings.
- [ ] Add API methods for opening output folders.

Acceptance:

- [ ] A desktop window opens locally.
- [ ] JavaScript can call Python methods and receive JSON results.
- [ ] Native file and folder picker dialogs work on Windows and macOS.

## 5. Convert Mockup Into Frontend App

- [ ] Create a frontend project using React, TypeScript, and Vite.
- [ ] Convert `ui-mock.html` styles into maintainable CSS modules or app-level CSS.
- [ ] Split the UI into reusable components: title bar, sidebar, page header, cards, tables, toggles, buttons, progress bars.
- [x] Implement the Dashboard view.
- [x] Implement the Library view.
- [x] Implement the Taste Profile view.
- [ ] Implement the Daily Discovery view.
- [x] Implement the Downloads view.
- [x] Implement the Settings view.
- [x] Replace hardcoded mock data with API-backed data.
- [ ] Preserve the current visual direction unless intentionally changed.

Acceptance:

- [ ] All major views from `ui-mock.html` exist in the frontend app.
- [ ] Navigation works without page reloads.
- [ ] The UI renders correctly inside the desktop window.

## 6. Implement Background Jobs

- [ ] Add a job manager for long-running operations.
- [ ] Run genre enrichment in the background.
- [ ] Run library processing in the background.
- [ ] Run discovery generation in the background.
- [ ] Run downloads in the background.
- [ ] Track job states: queued, running, succeeded, failed, cancelled.
- [ ] Stream progress updates to the frontend.
- [ ] Allow cancellation for downloads and batch operations where feasible.
- [ ] Prevent duplicate conflicting jobs from running at the same time.

Acceptance:

- [ ] Long-running tasks do not freeze the desktop UI.
- [ ] Progress bars and status messages reflect real backend progress.
- [ ] Errors are visible and actionable in the UI.

## 7. Implement Core User Workflows

- [x] Import a music library CSV.
- [x] Enrich imported tracks with genre metadata.
- [x] Generate a taste profile from the enriched library.
- [ ] Display top genres, artists, library counts, and recent activity.
- [x] Generate a daily discovery batch.
- [ ] Mark tracks as new, skipped, already in library, or downloaded.
- [x] Download one recommended track.
- [ ] Download an entire discovery batch.
- [ ] Write metadata tags to downloaded audio files.
- [ ] Open the download output folder from the app.

Acceptance:

- [ ] A new user can go from CSV import to downloaded discovery tracks without using the command line.
- [ ] The app clearly shows what succeeded, failed, and still needs attention.

## 8. Add Validation And Error Handling

- [ ] Validate CSV paths and expected columns before processing.
- [ ] Validate output directory permissions.
- [ ] Detect missing `ffmpeg`.
- [ ] Detect missing or broken `yt-dlp`.
- [ ] Handle API/network failures from metadata providers.
- [ ] Handle unavailable YouTube search/download results.
- [ ] Handle duplicate tracks and existing files.
- [ ] Add retry behavior where appropriate.
- [ ] Add user-readable error messages for all expected failure modes.

Acceptance:

- [ ] Common setup and runtime failures produce clear messages.
- [ ] Failed operations do not corrupt existing library or discovery files.

## 9. Add Tests

- [ ] Add unit tests for refactored Python services.
- [ ] Add tests for settings load/save behavior.
- [ ] Add tests for path resolution on Windows-style and macOS-style paths.
- [ ] Add tests for CSV parsing and invalid CSV handling.
- [ ] Add tests for discovery duplicate filtering.
- [ ] Add frontend component tests for key views.
- [ ] Add integration tests for Python API methods where practical.

Acceptance:

- [ ] Core backend behavior is covered by repeatable tests.
- [ ] Packaging-sensitive path logic has explicit test coverage.

## 10. Package For Windows And macOS

- [ ] Choose packaging tool: PyInstaller or Briefcase.
- [ ] Create Windows build configuration.
- [ ] Create macOS build configuration.
- [ ] Include frontend build assets in the desktop package.
- [ ] Include or locate `ffmpeg` reliably.
- [ ] Include required Python dependencies.
- [ ] Add app icon and metadata.
- [ ] Build unsigned local packages first.
- [ ] Document signing/notarization requirements for macOS distribution.
- [ ] Document code-signing requirements for Windows distribution.

Acceptance:

- [ ] A clean Windows machine can run the packaged app.
- [ ] A clean macOS machine can run the packaged app.
- [ ] App data and settings are written outside the install directory.

## 11. Add Release Automation

- [ ] Add scripts for building frontend assets.
- [ ] Add scripts for running backend tests.
- [ ] Add scripts for building desktop packages.
- [ ] Add a release checklist.
- [ ] Add GitHub Actions or another CI workflow for tests.
- [ ] Add CI packaging jobs if signing secrets are available.

Acceptance:

- [ ] A release can be reproduced from documented commands.
- [ ] CI catches basic backend and frontend regressions.

## 12. Polish Desktop Behavior

- [ ] Add native menu items for About, Settings, Quit, and Help.
- [ ] Add tray behavior if retained in v1 scope.
- [ ] Add startup launch behavior if retained in v1 scope.
- [ ] Add desktop notifications if retained in v1 scope.
- [ ] Add keyboard shortcuts for common actions.
- [ ] Add empty states for first-run screens.
- [ ] Add loading states for all API-backed screens.
- [ ] Add confirmation before destructive actions.

Acceptance:

- [ ] The app feels like a desktop app rather than a browser tab.
- [ ] First-run, loading, empty, success, and failure states are handled.

## Suggested First Milestone

- [x] Refactor one backend workflow into a callable service.
- [x] Add a minimal `pywebview` window.
- [x] Load a frontend screen inside the window.
- [x] Call one Python method from JavaScript.
- [x] Display real library/profile data in the Dashboard view.

Milestone acceptance:

- [ ] The app launches as a desktop window and shows real data from the existing project files.
