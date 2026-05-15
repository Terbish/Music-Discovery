let selectedLibraryPath = null;
let activeView = "dashboard";
let dashboardData = null;
let libraryTracks = [];
let libraryGenreOptions = [];
let downloadTracks = [];
let selectedDownloadTrackId = null;
let selectedDownloadSourceId = null;
let sourceCandidates = [];
let sourceCandidatesByTrack = {};
let selectedSourceByTrack = {};
let manualSourceTrackId = null;
let settingsDirty = false;
let toastTimer = null;

const elements = {
  status: document.querySelector("#status"),
  libraryStatus: document.querySelector("#library-status"),
  tasteStatus: document.querySelector("#taste-status"),
  downloadsStatus: document.querySelector("#downloads-status"),
  settingsStatus: document.querySelector("#settings-status"),
  librarySize: document.querySelector("#library-size"),
  topGenre: document.querySelector("#top-genre"),
  artistCount: document.querySelector("#artist-count"),
  pendingDownloads: document.querySelector("#pending-downloads"),
  genreCount: document.querySelector("#genre-count"),
  artistTotal: document.querySelector("#artist-total"),
  batchCount: document.querySelector("#batch-count"),
  dataDir: document.querySelector("#data-dir"),
  topGenres: document.querySelector("#top-genres"),
  topArtists: document.querySelector("#top-artists"),
  recentActivity: document.querySelector("#recent-activity"),
  discoveryBatches: document.querySelector("#discovery-batches"),
  chooseLibrary: document.querySelector("#choose-library"),
  createDiscovery: document.querySelector("#create-discovery"),
  processLibrary: document.querySelector("#process-library"),
  refreshLibrary: document.querySelector("#refresh-library"),
  processLibraryView: document.querySelector("#process-library-view"),
  librarySearch: document.querySelector("#library-search"),
  libraryGenreFilter: document.querySelector("#library-genre-filter"),
  librarySort: document.querySelector("#library-sort"),
  libraryVisibleCount: document.querySelector("#library-visible-count"),
  libraryTotalCount: document.querySelector("#library-total-count"),
  librarySourcePath: document.querySelector("#library-source-path"),
  libraryTracks: document.querySelector("#library-tracks"),
  refreshTasteProfile: document.querySelector("#refresh-taste-profile"),
  processProfileLibrary: document.querySelector("#process-profile-library"),
  profileTrackCount: document.querySelector("#profile-track-count"),
  profileGenreCount: document.querySelector("#profile-genre-count"),
  profileArtistCount: document.querySelector("#profile-artist-count"),
  profileTopGenre: document.querySelector("#profile-top-genre"),
  profileTopGenreShare: document.querySelector("#profile-top-genre-share"),
  profileSourcePath: document.querySelector("#profile-source-path"),
  profileGenreTotal: document.querySelector("#profile-genre-total"),
  profileArtistTotal: document.querySelector("#profile-artist-total"),
  profileGenres: document.querySelector("#profile-genres"),
  profileArtists: document.querySelector("#profile-artists"),
  profileGenreExplorer: document.querySelector("#profile-genre-explorer"),
  refreshDownloads: document.querySelector("#refresh-downloads"),
  createDiscoveryDownloads: document.querySelector("#create-discovery-downloads"),
  addLibraryQueue: document.querySelector("#add-library-queue"),
  clearDownloadQueue: document.querySelector("#clear-download-queue"),
  searchDownloadSources: document.querySelector("#search-download-sources"),
  downloadBestSources: document.querySelector("#download-best-sources"),
  downloadTrackFilter: document.querySelector("#download-track-filter"),
  downloadSourceMode: document.querySelector("#download-source-mode"),
  avoidLive: document.querySelector("#avoid-live"),
  avoidCovers: document.querySelector("#avoid-covers"),
  avoidRemixes: document.querySelector("#avoid-remixes"),
  allowRadioEdits: document.querySelector("#allow-radio-edits"),
  downloadQueueCount: document.querySelector("#download-queue-count"),
  downloadReadyCount: document.querySelector("#download-ready-count"),
  downloadActiveBatch: document.querySelector("#download-active-batch"),
  downloadTracks: document.querySelector("#download-tracks"),
  selectedDownloadTrack: document.querySelector("#selected-download-track"),
  sourceCandidates: document.querySelector("#source-candidates"),
  markNoSources: document.querySelector("#mark-no-sources"),
  manualSourceForm: document.querySelector("#manual-source-form"),
  manualSourceUrl: document.querySelector("#manual-source-url"),
  addManualSource: document.querySelector("#add-manual-source"),
  downloadSelectedSource: document.querySelector("#download-selected-source"),
  navItems: document.querySelectorAll("[data-view-target]"),
  views: document.querySelectorAll("[data-view]"),
  settingsForm: document.querySelector("#settings-form"),
  saveSettings: document.querySelector("#save-settings"),
  resetSettings: document.querySelector("#reset-settings"),
  libraryPath: document.querySelector("#library-path"),
  outputPath: document.querySelector("#output-path"),
  audioOutputPath: document.querySelector("#audio-output-path"),
  audioFormat: document.querySelector("#audio-format"),
  youtubeCookiesPath: document.querySelector("#youtube-cookies-path"),
  browseYoutubeCookiesPath: document.querySelector("#browse-youtube-cookies-path"),
  testYoutubeCookies: document.querySelector("#test-youtube-cookies"),
  batchSize: document.querySelector("#batch-size"),
  launchAtStartup: document.querySelector("#launch-at-startup"),
  minimizeToTray: document.querySelector("#minimize-to-tray"),
  notificationsEnabled: document.querySelector("#notifications-enabled"),
  useRepoPersonalDir: document.querySelector("#use-repo-personal-dir"),
  browseLibraryPath: document.querySelector("#browse-library-path"),
  browseOutputPath: document.querySelector("#browse-output-path"),
  browseAudioOutputPath: document.querySelector("#browse-audio-output-path"),
  toastRegion: document.querySelector("#toast-region"),
};

window.addEventListener("pywebviewready", initializeApp);
window.addEventListener("backend-progress", (event) => {
  setProgressStatus(event.detail);
});

document.addEventListener("DOMContentLoaded", () => {
  elements.navItems.forEach((item) => {
    item.addEventListener("click", () => navigateTo(item.dataset.viewTarget));
  });
  elements.chooseLibrary.addEventListener("click", chooseLibrary);
  elements.createDiscovery.addEventListener("click", createDailyDiscovery);
  elements.processLibrary.addEventListener("click", processLibrary);
  elements.refreshLibrary.addEventListener("click", loadLibrary);
  elements.processLibraryView.addEventListener("click", processLibrary);
  elements.librarySearch.addEventListener("input", renderLibraryTracks);
  elements.libraryGenreFilter.addEventListener("change", renderLibraryTracks);
  elements.librarySort.addEventListener("change", renderLibraryTracks);
  elements.refreshTasteProfile.addEventListener("click", loadTasteProfile);
  elements.processProfileLibrary.addEventListener("click", processLibrary);
  elements.refreshDownloads.addEventListener("click", loadDownloads);
  elements.createDiscoveryDownloads.addEventListener("click", createDailyDiscovery);
  elements.addLibraryQueue.addEventListener("click", addLibraryToDownloadQueue);
  elements.clearDownloadQueue.addEventListener("click", clearDownloadQueue);
  elements.searchDownloadSources.addEventListener("click", searchDownloadSources);
  elements.downloadBestSources.addEventListener("click", downloadBestSources);
  elements.downloadTrackFilter.addEventListener("change", renderDownloads);
  elements.downloadSourceMode.addEventListener("change", renderSourceCandidates);
  elements.avoidLive.addEventListener("change", renderSourceCandidates);
  elements.avoidCovers.addEventListener("change", renderSourceCandidates);
  elements.avoidRemixes.addEventListener("change", renderSourceCandidates);
  elements.allowRadioEdits.addEventListener("change", renderSourceCandidates);
  elements.markNoSources.addEventListener("click", markNoSources);
  elements.manualSourceForm.addEventListener("submit", addManualSource);
  elements.downloadSelectedSource.addEventListener("click", downloadSelectedSource);
  elements.saveSettings.addEventListener("click", saveSettings);
  elements.resetSettings.addEventListener("click", loadSettings);
  elements.browseYoutubeCookiesPath.addEventListener("click", browseYoutubeCookiesPath);
  elements.testYoutubeCookies.addEventListener("click", testYoutubeCookies);
  elements.settingsForm.addEventListener("submit", (event) => event.preventDefault());
  elements.settingsForm.addEventListener("input", markSettingsDirty);
  elements.browseLibraryPath.addEventListener("click", browseLibraryPath);
  elements.browseOutputPath.addEventListener("click", () => browseDirectory(elements.outputPath));
  elements.browseAudioOutputPath.addEventListener("click", () => browseDirectory(elements.audioOutputPath));

  if (!window.pywebview) {
    setStatus("Open this screen from desktop_app.py to connect the Python API.", "error");
    setLibraryStatus("Open this screen from desktop_app.py to connect the Python API.", "error");
    setTasteStatus("Open this screen from desktop_app.py to connect the Python API.", "error");
    setDownloadsStatus("Open this screen from desktop_app.py to connect the Python API.", "error");
    setSettingsStatus("Open this screen from desktop_app.py to connect the Python API.", "error");
  }
});

async function initializeApp() {
  await loadDashboard();
  await loadSettings();
}

async function navigateTo(viewName) {
  if (!viewName || activeView === viewName) {
    return;
  }

  activeView = viewName;
  elements.views.forEach((view) => {
    view.classList.toggle("active", view.dataset.view === viewName);
  });
  elements.navItems.forEach((item) => {
    item.classList.toggle("active", item.dataset.viewTarget === viewName);
  });

  if (viewName === "dashboard") {
    await loadDashboard();
  }

  if (viewName === "library") {
    await loadLibrary();
  }

  if (viewName === "taste") {
    await loadTasteProfile();
  }

  if (viewName === "downloads") {
    await loadDownloads();
  }

  if (viewName === "settings") {
    await loadSettings();
  }
}

async function loadDashboard() {
  setStatus("Loading dashboard data.");
  const response = await callApi("get_dashboard_data");
  if (!response.ok) {
    setStatus(response.error, "error");
    return;
  }

  dashboardData = response.data;
  renderDashboard(response.data);
  renderLibrary(response.data);
  renderTasteProfile(response.data);
  setStatus(response.data.needs_setup ? "No processed library files found yet." : "Dashboard data loaded.", response.data.needs_setup ? "" : "success");
}

async function chooseLibrary() {
  const response = await callApi("select_file");
  if (!response.ok) {
    setStatus(response.error, "error");
    return;
  }

  selectedLibraryPath = response.data.path;
  if (selectedLibraryPath) {
    setStatus(`Selected ${selectedLibraryPath}`);
  }
}

async function processLibrary() {
  setStatus("Enriching genres and processing library 0/0.");
  setLibraryStatus("Enriching genres and processing library 0/0.");
  setTasteStatus("Enriching genres and processing library 0/0.");
  elements.processLibrary.disabled = true;
  elements.processLibraryView.disabled = true;
  elements.processProfileLibrary.disabled = true;
  const response = await callApi("process_library", selectedLibraryPath);
  elements.processLibrary.disabled = false;
  elements.processLibraryView.disabled = false;
  elements.processProfileLibrary.disabled = false;

  if (!response.ok) {
    setStatus(response.error, "error");
    setLibraryStatus(response.error, "error");
    setTasteStatus(response.error, "error");
    return;
  }

  const enrichedPath = response.data.outputs.enriched_csv;
  setStatus(`Processed ${formatNumber(response.data.total_tracks)} tracks from ${enrichedPath}.`, "success");
  setLibraryStatus(`Processed ${formatNumber(response.data.total_tracks)} tracks.`, "success");
  setTasteStatus(`Processed ${formatNumber(response.data.total_tracks)} tracks.`, "success");
  await loadDashboard();
}

async function createDailyDiscovery() {
  setStatus("Creating daily discovery.");
  setDownloadsStatus("Creating daily discovery.");
  elements.createDiscovery.disabled = true;
  elements.createDiscoveryDownloads.disabled = true;
  const response = await callApi("create_daily_discovery");
  elements.createDiscovery.disabled = false;
  elements.createDiscoveryDownloads.disabled = false;

  if (!response.ok) {
    setStatus(response.error, "error");
    setDownloadsStatus(response.error, "error");
    return;
  }

  setStatus(`Created daily discovery with ${formatNumber(response.data.track_count)} tracks.`, "success");
  setDownloadsStatus("Daily discovery added to the download queue.", "success");
  await loadDashboard();
  await loadDownloads();
}

async function loadLibrary() {
  setLibraryStatus("Loading library.");
  const response = await callApi("get_dashboard_data");
  if (!response.ok) {
    setLibraryStatus(response.error, "error");
    return;
  }

  dashboardData = response.data;
  renderDashboard(response.data);
  renderLibrary(response.data);
  renderTasteProfile(response.data);
}

async function loadTasteProfile() {
  setTasteStatus("Loading taste profile.");
  const response = await callApi("get_dashboard_data");
  if (!response.ok) {
    setTasteStatus(response.error, "error");
    return;
  }

  dashboardData = response.data;
  renderDashboard(response.data);
  renderLibrary(response.data);
  renderTasteProfile(response.data);
}

async function loadDownloads() {
  setDownloadsStatus("Loading download queue.");
  const response = await callApi("get_download_queue");
  if (!response.ok) {
    setDownloadsStatus(response.error, "error");
    return;
  }

  renderDownloadQueue(response.data);
  setDownloadsStatus(response.data.active_batch ? "Download queue loaded." : "No discovery batch found.", response.data.active_batch ? "success" : "");
}

async function loadSettings() {
  setSettingsStatus("Loading settings.");
  const response = await callApi("get_settings");
  if (!response.ok) {
    setSettingsStatus(response.error, "error");
    return;
  }

  renderSettings(response.data);
  settingsDirty = false;
  hideToast();
  setSettingsStatus("Settings loaded.", "success");
}

async function saveSettings() {
  const payload = readSettingsForm();
  if (!payload) {
    return;
  }

  setSettingsStatus("Saving settings.");
  elements.saveSettings.disabled = true;
  const response = await callApi("save_settings", payload);
  elements.saveSettings.disabled = false;

  if (!response.ok) {
    setSettingsStatus(response.error, "error");
    return;
  }

  renderSettings(response.data);
  selectedLibraryPath = response.data.library_path;
  settingsDirty = false;
  hideToast();
  setSettingsStatus("Settings saved.", "success");
}

async function browseLibraryPath() {
  const response = await callApi("select_file");
  if (!response.ok) {
    setSettingsStatus(response.error, "error");
    return;
  }

  if (response.data.path) {
    elements.libraryPath.value = response.data.path;
    markSettingsDirty();
  }
}

async function browseDirectory(input) {
  const response = await callApi("select_directory");
  if (!response.ok) {
    setSettingsStatus(response.error, "error");
    return;
  }

  if (response.data.path) {
    input.value = response.data.path;
    markSettingsDirty();
  }
}

async function browseYoutubeCookiesPath() {
  const response = await callApi("select_file", ["Cookies files (*.txt;*.cookies)", "Text files (*.txt)", "All files (*.*)"]);
  if (!response.ok) {
    setSettingsStatus(response.error, "error");
    return;
  }

  if (response.data.path) {
    elements.youtubeCookiesPath.value = response.data.path;
    markSettingsDirty();
  }
}

function setProgressStatus(detail) {
  const labels = {
    enriching_genres: "Enriching genres",
    processing_library: "Processing library",
    daily_discovery: "Creating daily discovery",
    source_search: "Searching sources",
    best_source_download: "Downloading best sources",
  };
  const label = labels[detail.phase] || detail.message || "Working";
  const current = formatNumber(detail.current);
  const total = formatNumber(detail.total);

  if (detail.total !== undefined && detail.total !== null) {
    setStatus(`${label} ${current}/${total}.`);
    setLibraryStatus(`${label} ${current}/${total}.`);
    setTasteStatus(`${label} ${current}/${total}.`);
    if (["daily_discovery", "source_search", "best_source_download"].includes(detail.phase)) {
      setDownloadsStatus(`${label} ${current}/${total}.`);
    }
    return;
  }

  setStatus(label);
  setLibraryStatus(label);
  setTasteStatus(label);
  if (["daily_discovery", "source_search", "best_source_download"].includes(detail.phase)) {
    setDownloadsStatus(label);
  }
}

function renderDashboard(data) {
  const stats = data.stats;
  elements.librarySize.textContent = formatNumber(stats.library_size);
  elements.topGenre.textContent = stats.top_genre ? stats.top_genre.genre : "Not available";
  elements.artistCount.textContent = formatNumber(stats.artist_count);
  elements.pendingDownloads.textContent = formatNumber(stats.pending_downloads);
  elements.genreCount.textContent = `${formatNumber(stats.genre_count)} genres`;
  elements.artistTotal.textContent = `${formatNumber(stats.artist_count)} artists`;
  elements.batchCount.textContent = `${formatNumber(stats.discovery_batches)} batches`;
  elements.dataDir.textContent = data.paths.data_dir;

  renderBars(elements.topGenres, data.top_genres, "genre");
  renderBars(elements.topArtists, data.top_artists, "artist");
  renderActivity(elements.recentActivity, data.recent_activity);
  renderBatches(elements.discoveryBatches, data.discovery_batches);
}

function renderLibrary(data) {
  const library = data.library || {};
  libraryTracks = library.tracks || [];
  libraryGenreOptions = library.genres || [];

  elements.librarySourcePath.textContent = data.paths.personal_library;
  elements.librarySourcePath.title = data.paths.personal_library;
  elements.libraryTotalCount.textContent = formatNumber(libraryTracks.length);

  renderLibraryGenreOptions();
  renderLibraryTracks();
  setLibraryStatus(data.needs_setup ? "No processed library files found yet." : "Library loaded.", data.needs_setup ? "" : "success");
}

async function addLibraryToDownloadQueue() {
  setDownloadsStatus("Adding library to the download queue.");
  elements.addLibraryQueue.disabled = true;
  const response = await callApi("add_library_to_download_queue");
  elements.addLibraryQueue.disabled = false;

  if (!response.ok) {
    setDownloadsStatus(response.error, "error");
    return;
  }

  selectedDownloadTrackId = null;
  setDownloadsStatus(`Added ${formatNumber(response.data.track_count)} library tracks to the download queue.`, "success");
  await loadDownloads();
  await loadDashboard();
}

async function clearDownloadQueue() {
  setDownloadsStatus("Clearing download queue.");
  elements.clearDownloadQueue.disabled = true;
  elements.searchDownloadSources.disabled = true;
  elements.downloadBestSources.disabled = true;
  const response = await callApi("clear_download_queue");
  elements.clearDownloadQueue.disabled = false;
  elements.searchDownloadSources.disabled = false;
  elements.downloadBestSources.disabled = false;

  if (!response.ok) {
    setDownloadsStatus(response.error, "error");
    return;
  }

  selectedDownloadTrackId = null;
  selectedDownloadSourceId = null;
  sourceCandidates = [];
  sourceCandidatesByTrack = {};
  selectedSourceByTrack = {};
  manualSourceTrackId = null;
  renderDownloadQueue({
    active_batch: null,
    tracks: [],
  });
  setDownloadsStatus(
    `Cleared ${formatNumber(response.data.cleared_tracks)} queued tracks from ${formatNumber(response.data.cleared_batches)} batches.`,
    "success",
  );
  await loadDashboard();
}

function renderTasteProfile(data) {
  const profile = data.taste_profile || {};
  const topGenre = profile.top_genre;
  const topGenres = profile.top_genres || [];
  const topArtists = profile.top_artists || [];
  const explorer = profile.genre_explorer || [];
  const totalTracks = profile.total_tracks || 0;

  elements.profileTrackCount.textContent = formatNumber(totalTracks);
  elements.profileGenreCount.textContent = formatNumber(profile.genre_count);
  elements.profileArtistCount.textContent = formatNumber(profile.artist_count);
  elements.profileTopGenre.textContent = topGenre ? topGenre.genre : "Not available";
  elements.profileTopGenreShare.textContent = topGenre && totalTracks ? `${formatPercent(topGenre.count / totalTracks)}%` : "0%";
  elements.profileSourcePath.textContent = data.paths.taste_profile;
  elements.profileSourcePath.title = data.paths.taste_profile;
  elements.profileGenreTotal.textContent = `${formatNumber(profile.genre_count)} genres`;
  elements.profileArtistTotal.textContent = `${formatNumber(profile.artist_count)} artists`;

  renderProfileBars(elements.profileGenres, topGenres, {
    labelKey: "genre",
    total: totalTracks,
    emptyText: "No genre data found.",
  });
  renderProfileBars(elements.profileArtists, topArtists, {
    labelKey: "artist",
    total: totalTracks,
    emptyText: "No artist data found.",
  });
  renderGenreExplorer(elements.profileGenreExplorer, explorer);

  setTasteStatus(data.needs_setup ? "No processed library files found yet." : "Taste profile loaded.", data.needs_setup ? "" : "success");
}

function renderSettings(settings) {
  elements.libraryPath.value = settings.library_path || "";
  elements.outputPath.value = settings.output_path || "";
  elements.audioOutputPath.value = settings.audio_output_path || "";
  elements.audioFormat.value = settings.audio_format || "mp3";
  elements.youtubeCookiesPath.value = settings.youtube_cookies_path || "";
  elements.batchSize.value = settings.batch_size || 20;
  elements.launchAtStartup.checked = Boolean(settings.launch_at_startup);
  elements.minimizeToTray.checked = Boolean(settings.minimize_to_tray);
  elements.notificationsEnabled.checked = Boolean(settings.notifications_enabled);
  elements.useRepoPersonalDir.checked = Boolean(settings.use_repo_personal_dir);
}

function renderDownloadQueue(data) {
  downloadTracks = data.tracks || [];
  selectedDownloadTrackId = selectedDownloadTrackId || (downloadTracks[0] && downloadTracks[0].id);
  downloadTracks.forEach((track) => {
    if (track.candidates && track.candidates.length) {
      sourceCandidatesByTrack[track.id] = track.candidates;
    }
    if (track.selected_source_id) {
      selectedSourceByTrack[track.id] = track.selected_source_id;
    }
  });
  pruneSourceCache();
  sourceCandidates = getSelectedSourceCandidates();
  selectedDownloadSourceId = selectedSourceByTrack[selectedDownloadTrackId] || null;

  const readyCount = downloadTracks.filter((track) => track.status === "downloaded").length;
  elements.downloadQueueCount.textContent = formatNumber(downloadTracks.length);
  elements.downloadReadyCount.textContent = formatNumber(readyCount);

  if (data.active_batch) {
    elements.downloadActiveBatch.textContent = `${data.active_batch.kind || "Batch"} ${data.active_batch.date} - ${formatNumber(data.active_batch.track_count)} tracks`;
    elements.downloadActiveBatch.title = data.active_batch.path;
  } else {
    elements.downloadActiveBatch.textContent = "No discovery batch found.";
    elements.downloadActiveBatch.title = "";
  }

  renderDownloads();
  renderSourceCandidates();
}

function renderDownloads() {
  const rows = getFilteredDownloadTracks();
  elements.downloadTracks.classList.remove("empty");
  elements.downloadTracks.replaceChildren();

  if (!rows.length) {
    elements.downloadTracks.classList.add("empty");
    elements.downloadTracks.textContent = downloadTracks.length ? "No tracks match the current queue filter." : "No discovery tracks found.";
    elements.selectedDownloadTrack.textContent = "Select a track.";
    selectedDownloadTrackId = null;
    selectedDownloadSourceId = null;
    sourceCandidates = [];
    renderSourceCandidates();
    return;
  }

  if (!rows.some((track) => track.id === selectedDownloadTrackId)) {
    selectedDownloadTrackId = rows[0].id;
    sourceCandidates = getSelectedSourceCandidates();
    selectedDownloadSourceId = selectedSourceByTrack[selectedDownloadTrackId] || null;
  }

  rows.forEach((track) => {
    const item = document.createElement("button");
    item.className = `download-row download-track-row ${track.id === selectedDownloadTrackId ? "selected" : ""}`;
    item.type = "button";
    item.dataset.trackId = track.id;
    item.innerHTML = `
      <span>${String(track.index).padStart(2, "0")}</span>
      <strong title="${escapeAttr(track.title)}">${escapeHtml(track.title)}</strong>
      <span title="${escapeAttr(track.artist)}">${escapeHtml(track.artist)}</span>
      <span>${escapeHtml(formatTrackStatus(track.status))}</span>
    `;
    item.addEventListener("click", () => {
      selectedDownloadTrackId = track.id;
      sourceCandidates = getSelectedSourceCandidates();
      selectedDownloadSourceId = selectedSourceByTrack[selectedDownloadTrackId] || null;
      renderDownloads();
      renderSourceCandidates();
    });
    elements.downloadTracks.append(item);
  });

  const selected = getSelectedDownloadTrack();
  elements.selectedDownloadTrack.textContent = selected ? `${selected.artist} - ${selected.title}` : "Select a track.";
}

async function searchDownloadSources() {
  const tracks = getFilteredDownloadTracks().filter(trackNeedsSourceSearch);
  if (!tracks.length) {
    setDownloadsStatus("No tracks in the current queue filter need source search.", "error");
    return;
  }

  setDownloadsStatus(`Searching sources for ${formatNumber(tracks.length)} tracks that need sources.`);
  elements.searchDownloadSources.disabled = true;
  const response = await callApi("search_download_queue_sources", tracks, 8);
  elements.searchDownloadSources.disabled = false;

  if (!response.ok) {
    setDownloadsStatus(response.error, "error");
    return;
  }

  response.data.results.forEach((result) => {
    const track = downloadTracks.find((row) => row.id === result.track_id);
    if (!track) {
      return;
    }

    if (result.ok) {
      const candidates = result.candidates || [];
      sourceCandidatesByTrack[result.track_id] = candidates;
      selectedSourceByTrack[result.track_id] = candidates[0] && candidates[0].id;
      track.candidates = candidates;
      track.selected_source_id = selectedSourceByTrack[result.track_id];
      track.source_query = result.query || "";
      track.no_sources = {};
      if (track.status !== "downloaded") {
        track.status = candidates.length ? "sources_found" : "source_error";
      }
      return;
    }

    sourceCandidatesByTrack[result.track_id] = [];
    selectedSourceByTrack[result.track_id] = null;
    if (track.status !== "downloaded") {
      track.status = "source_error";
    }
    track.source_error = result.error;
  });

  sourceCandidates = getSelectedSourceCandidates();
  selectedDownloadSourceId = selectedSourceByTrack[selectedDownloadTrackId] || null;
  renderDownloads();
  renderSourceCandidates();
  setDownloadsStatus(
    `Searched ${formatNumber(response.data.searched)} tracks: ${formatNumber(response.data.succeeded)} succeeded, ${formatNumber(response.data.failed)} failed.`,
    response.data.failed ? "" : "success",
  );
}

async function downloadBestSources() {
  const tracks = getFilteredDownloadTracks()
    .filter((track) => track.status !== "downloaded" && track.status !== "no_sources")
    .map((track) => ({
      ...track,
      candidates: sourceCandidatesByTrack[track.id] || track.candidates || [],
      selected_source_id: selectedSourceByTrack[track.id] || track.selected_source_id || "",
    }));
  if (!tracks.length) {
    setDownloadsStatus("No downloadable tracks found in the current queue filter.", "error");
    return;
  }

  setDownloadsStatus(`Downloading best sources for ${formatNumber(tracks.length)} queued tracks.`);
  elements.downloadBestSources.disabled = true;
  elements.searchDownloadSources.disabled = true;
  const response = await callApi("download_best_sources", tracks, 8);
  elements.downloadBestSources.disabled = false;
  elements.searchDownloadSources.disabled = false;

  if (!response.ok) {
    setDownloadsStatus(response.error, "error");
    return;
  }

  response.data.results.forEach((result) => {
    const track = downloadTracks.find((row) => row.id === result.track_id);
    if (!track || !result.ok) {
      return;
    }
    if (result.source) {
      selectedSourceByTrack[track.id] = result.source.id;
      track.selected_source_id = result.source.id;
    }
    if (result.download && !result.download.skipped) {
      track.status = "downloaded";
      track.output_path = result.download.path;
      track.downloaded_source = {
        source_id: result.source && result.source.id,
        source_title: result.source && result.source.title,
        path: result.download.path,
      };
    }
  });

  renderDownloads();
  renderSourceCandidates();
  setDownloadsStatus(
    `Best-source download complete: ${formatNumber(response.data.succeeded)} succeeded, ${formatNumber(response.data.failed)} failed.`,
    response.data.failed ? "" : "success",
  );
}

function renderSourceCandidates() {
  const track = getSelectedDownloadTrack();
  syncManualSourceInput(track);
  sourceCandidates = getSelectedSourceCandidates();
  selectedDownloadSourceId = selectedSourceByTrack[selectedDownloadTrackId] || selectedDownloadSourceId;
  syncSourceControls(track);
  elements.downloadSelectedSource.disabled = !track || !selectedDownloadSourceId;
  elements.sourceCandidates.classList.remove("empty");
  elements.sourceCandidates.replaceChildren();

  if (!track) {
    elements.sourceCandidates.classList.add("empty");
    elements.sourceCandidates.textContent = "Select a track.";
    return;
  }
  if (track.status === "no_sources") {
    elements.sourceCandidates.classList.add("empty");
    elements.sourceCandidates.textContent = "Marked no sources.";
    elements.downloadSelectedSource.disabled = true;
    return;
  }
  const downloadedSourceId = track.downloaded_source && track.downloaded_source.source_id;
  elements.downloadSelectedSource.textContent = track.status === "downloaded" && selectedDownloadSourceId !== downloadedSourceId
    ? "Replace Source"
    : "Download Selected";

  const filtered = sourceCandidates.filter(sourceAllowedByPreferences);
  if (!filtered.length) {
    elements.sourceCandidates.classList.add("empty");
    elements.sourceCandidates.textContent = sourceCandidates.length ? "No candidates match the current source rules." : "Find sources to compare YouTube results before downloading.";
    elements.downloadSelectedSource.disabled = true;
    return;
  }

  if (!filtered.some((source) => source.id === selectedDownloadSourceId)) {
    selectedDownloadSourceId = filtered[0].id;
    selectedSourceByTrack[selectedDownloadTrackId] = selectedDownloadSourceId;
  }

  filtered.forEach((source) => {
    const item = document.createElement("button");
    item.className = `source-row ${source.id === selectedDownloadSourceId ? "selected" : ""}`;
    item.type = "button";
    item.dataset.sourceId = source.id;
    item.innerHTML = `
      <span class="source-score">${formatNumber(source.confidence)}</span>
      <span class="source-main">
        <strong title="${escapeAttr(source.title)}">${escapeHtml(source.title)}</strong>
        <span title="${escapeAttr(source.uploader)}">${escapeHtml(source.uploader || "Unknown channel")}</span>
      </span>
      <span class="source-duration">${escapeHtml(source.duration_text || "-")}</span>
      <span class="source-badges">${renderSourceBadges(source.badges)}</span>
    `;
    item.addEventListener("click", () => {
      selectedDownloadSourceId = source.id;
      selectedSourceByTrack[selectedDownloadTrackId] = source.id;
      renderSourceCandidates();
    });
    elements.sourceCandidates.append(item);
  });

  elements.downloadSelectedSource.disabled = false;
}

async function markNoSources() {
  const track = getSelectedDownloadTrack();
  if (!track) {
    setDownloadsStatus("Select a track before marking it.", "error");
    return;
  }

  setDownloadsStatus(`Marking no sources for ${track.artist} - ${track.title}.`);
  elements.markNoSources.disabled = true;
  const response = await callApi("mark_track_no_sources", track);

  if (!response.ok) {
    syncSourceControls(track);
    setDownloadsStatus(response.error, "error");
    return;
  }

  track.status = "no_sources";
  track.selected_source_id = "";
  track.no_sources = { marked_at: new Date().toISOString() };
  selectedSourceByTrack[track.id] = null;
  selectedDownloadSourceId = null;
  elements.downloadTrackFilter.value = "no_sources";
  renderDownloads();
  renderSourceCandidates();
  setDownloadsStatus(`Marked no sources for ${track.artist} - ${track.title}.`, "success");
}

async function addManualSource(event) {
  event.preventDefault();
  const track = getSelectedDownloadTrack();
  const url = elements.manualSourceUrl.value.trim();
  if (!track) {
    setDownloadsStatus("Select a track before adding a source link.", "error");
    return;
  }
  if (!url) {
    setDownloadsStatus("Enter a manual source link.", "error");
    elements.manualSourceUrl.focus();
    return;
  }

  setDownloadsStatus(`Adding manual source for ${track.artist} - ${track.title}.`);
  elements.addManualSource.disabled = true;
  elements.manualSourceUrl.disabled = true;
  const response = await callApi("add_manual_source", track, url);
  elements.manualSourceUrl.disabled = false;

  if (!response.ok) {
    syncSourceControls(track);
    setDownloadsStatus(response.error, "error");
    return;
  }

  const candidates = response.data.candidates || [];
  sourceCandidatesByTrack[track.id] = candidates;
  selectedSourceByTrack[track.id] = response.data.selected_source_id;
  selectedDownloadSourceId = response.data.selected_source_id;
  track.candidates = candidates;
  track.selected_source_id = response.data.selected_source_id;
  track.source_query = response.data.query || track.source_query || "Manual source link";
  track.no_sources = {};
  if (track.status !== "downloaded") {
    track.status = "sources_found";
  }
  if (!trackMatchesDownloadFilter(track)) {
    elements.downloadTrackFilter.value = track.status === "downloaded" ? "downloaded" : "needs_source";
  }
  elements.manualSourceUrl.value = "";
  renderDownloads();
  renderSourceCandidates();
  setDownloadsStatus(`Added manual source for ${track.artist} - ${track.title}.`, "success");
}

async function downloadSelectedSource() {
  const track = getSelectedDownloadTrack();
  const candidates = getSelectedSourceCandidates();
  const source = candidates.find((candidate) => candidate.id === selectedDownloadSourceId);
  if (!track || !source) {
    setDownloadsStatus("Select a track and source before downloading.", "error");
    return;
  }

  const downloadedSourceId = track.downloaded_source && track.downloaded_source.source_id;
  const replacing = track.status === "downloaded" && selectedDownloadSourceId !== downloadedSourceId;
  setDownloadsStatus(`${replacing ? "Replacing source for" : "Downloading"} ${track.artist} - ${track.title}.`);
  elements.downloadSelectedSource.disabled = true;
  const response = await callApi(replacing ? "replace_downloaded_source" : "download_selected_source", track, source);
  elements.downloadSelectedSource.disabled = false;

  if (!response.ok) {
    setDownloadsStatus(response.error, "error");
    return;
  }

  track.status = "downloaded";
  track.no_sources = {};
  track.output_path = response.data.path;
  if (!response.data.skipped || replacing) {
    track.downloaded_source = {
      source_id: source.id,
      source_title: source.title,
      path: response.data.path,
    };
    selectedSourceByTrack[track.id] = source.id;
  }
  renderDownloads();
  renderSourceCandidates();
  setDownloadsStatus(response.data.message, "success");
}

async function testYoutubeCookies() {
  const payload = readSettingsForm();
  if (!payload) {
    return;
  }

  setSettingsStatus("Testing YouTube cookies.");
  elements.testYoutubeCookies.disabled = true;
  const response = await callApi("test_youtube_cookies", payload);
  elements.testYoutubeCookies.disabled = false;

  if (!response.ok) {
    setSettingsStatus(response.error, "error");
    return;
  }

  const result = response.data;
  if (result.ok) {
    setSettingsStatus(
      `${result.message} ${formatNumber(result.auth_cookie_count)} auth cookies and ${formatNumber(result.youtube_cookie_count)} YouTube cookies found.`,
      "success",
    );
    return;
  }

  setSettingsStatus(result.message, "error");
}

function getSelectedDownloadTrack() {
  return downloadTracks.find((track) => track.id === selectedDownloadTrackId) || null;
}

function getFilteredDownloadTracks() {
  const filter = elements.downloadTrackFilter.value;
  return downloadTracks.filter((track) => trackMatchesDownloadFilter(track, filter));
}

function trackMatchesDownloadFilter(track, filter = elements.downloadTrackFilter.value) {
  if (filter === "all") {
    return true;
  }
  if (filter === "needs_source") {
    return ["needs_source", "sources_found", "source_error"].includes(track.status);
  }
  return track.status === filter;
}

function trackNeedsSourceSearch(track) {
  if (track.status === "downloaded" || track.status === "sources_found" || track.status === "no_sources") {
    return false;
  }
  return !trackHasSources(track);
}

function trackHasSources(track) {
  const candidates = sourceCandidatesByTrack[track.id] || track.candidates || [];
  return candidates.length > 0;
}

function getSelectedSourceCandidates() {
  return sourceCandidatesByTrack[selectedDownloadTrackId] || [];
}

function syncSourceControls(track) {
  const hasTrack = Boolean(track);
  const canEditSources = hasTrack && track.status !== "downloaded";
  elements.markNoSources.disabled = !canEditSources || track.status === "no_sources";
  elements.manualSourceUrl.disabled = !hasTrack;
  elements.addManualSource.disabled = !hasTrack;
}

function syncManualSourceInput(track) {
  const trackId = track && track.id;
  if (manualSourceTrackId === trackId) {
    return;
  }
  manualSourceTrackId = trackId || null;
  elements.manualSourceUrl.value = "";
}

function pruneSourceCache() {
  const trackIds = new Set(downloadTracks.map((track) => track.id));
  Object.keys(sourceCandidatesByTrack).forEach((trackId) => {
    if (!trackIds.has(trackId)) {
      delete sourceCandidatesByTrack[trackId];
      delete selectedSourceByTrack[trackId];
    }
  });
}

function sourceAllowedByPreferences(source) {
  const badges = source.badges || [];
  if (badges.includes("Manual link")) {
    return true;
  }
  if (elements.avoidLive.checked && badges.includes("Live")) {
    return false;
  }
  if (elements.avoidCovers.checked && badges.includes("Cover")) {
    return false;
  }
  if (elements.avoidRemixes.checked && badges.includes("Remix")) {
    return false;
  }
  if (!elements.allowRadioEdits.checked && badges.includes("Radio edit")) {
    return false;
  }
  if (elements.downloadSourceMode.value === "official_audio" && getSelectedSourceCandidates().length > 1) {
    return badges.includes("Official audio") || badges.includes("Topic") || source.confidence >= 80;
  }
  if (elements.downloadSourceMode.value === "music_video") {
    return badges.includes("Official video") || badges.includes("Official audio") || badges.includes("Topic");
  }
  return true;
}

function renderSourceBadges(badges) {
  return (badges || []).map((badge) => `<span>${escapeHtml(badge)}</span>`).join("");
}

function formatTrackStatus(status) {
  const labels = {
    needs_source: "Needs source",
    sources_found: "Sources found",
    source_error: "Source error",
    no_sources: "No sources",
    downloaded: "Downloaded",
  };
  return labels[status] || status || "Needs source";
}

function readSettingsForm() {
  const batchSize = Number.parseInt(elements.batchSize.value, 10);
  if (!Number.isInteger(batchSize) || batchSize < 1 || batchSize > 200) {
    setSettingsStatus("Batch size must be between 1 and 200.", "error");
    elements.batchSize.focus();
    return null;
  }

  return {
    library_path: elements.libraryPath.value.trim(),
    output_path: elements.outputPath.value.trim(),
    audio_output_path: elements.audioOutputPath.value.trim(),
    audio_format: elements.audioFormat.value,
    youtube_cookies_path: elements.youtubeCookiesPath.value.trim(),
    batch_size: batchSize,
    launch_at_startup: elements.launchAtStartup.checked,
    minimize_to_tray: elements.minimizeToTray.checked,
    notifications_enabled: elements.notificationsEnabled.checked,
    use_repo_personal_dir: elements.useRepoPersonalDir.checked,
  };
}

function renderBars(container, rows, labelKey) {
  container.classList.remove("empty");
  container.replaceChildren();

  if (!rows.length) {
    container.classList.add("empty");
    container.textContent = labelKey === "genre" ? "No taste profile found." : "No artist data found.";
    return;
  }

  const max = Math.max(...rows.map((row) => row.count), 1);
  rows.forEach((row) => {
    const item = document.createElement("div");
    item.className = "bar-row";
    item.innerHTML = `
      <span title="${escapeAttr(row[labelKey])}">${escapeHtml(row[labelKey])}</span>
      <strong>${formatNumber(row.count)}</strong>
      <div class="bar-track"><span class="bar-fill" style="width: ${(row.count / max) * 100}%"></span></div>
    `;
    container.append(item);
  });
}

function renderActivity(container, rows) {
  container.classList.remove("empty");
  container.replaceChildren();

  if (!rows.length) {
    container.classList.add("empty");
    container.textContent = "No generated files found.";
    return;
  }

  rows.forEach((row) => {
    const item = document.createElement("div");
    item.className = "activity-row";
    item.innerHTML = `
      <strong>${escapeHtml(row.label)}</strong>
      <span title="${escapeAttr(row.path)}">${escapeHtml(row.when)} - ${escapeHtml(row.path)}</span>
    `;
    container.append(item);
  });
}

function renderBatches(container, rows) {
  container.classList.remove("empty");
  container.replaceChildren();

  if (!rows.length) {
    container.classList.add("empty");
    container.textContent = "No discovery CSV files found.";
    return;
  }

  rows.forEach((row) => {
    const item = document.createElement("div");
    item.className = "activity-row";
    item.innerHTML = `
      <strong>${escapeHtml(row.kind || "Discovery")} ${escapeHtml(row.date)} - ${formatNumber(row.track_count)} tracks</strong>
      <span title="${escapeAttr(row.path)}">${escapeHtml(row.modified_at)} - ${escapeHtml(row.path)}</span>
    `;
    container.append(item);
  });
}

function renderLibraryGenreOptions() {
  const currentValue = elements.libraryGenreFilter.value;
  elements.libraryGenreFilter.replaceChildren();

  const allOption = document.createElement("option");
  allOption.value = "";
  allOption.textContent = "All genres";
  elements.libraryGenreFilter.append(allOption);

  libraryGenreOptions.forEach((row) => {
    const option = document.createElement("option");
    option.value = row.genre;
    option.textContent = `${row.genre} (${formatNumber(row.count)})`;
    elements.libraryGenreFilter.append(option);
  });

  if ([...elements.libraryGenreFilter.options].some((option) => option.value === currentValue)) {
    elements.libraryGenreFilter.value = currentValue;
  }
}

function renderLibraryTracks() {
  const query = elements.librarySearch.value.trim().toLowerCase();
  const genre = elements.libraryGenreFilter.value;
  const sort = elements.librarySort.value;
  let rows = libraryTracks.filter((track) => {
    const matchesQuery = !query || `${track.title} ${track.artist}`.toLowerCase().includes(query);
    const matchesGenre = !genre || (track.genres || []).includes(genre);
    return matchesQuery && matchesGenre;
  });

  rows = [...rows].sort((first, second) => compareLibraryTracks(first, second, sort));
  elements.libraryVisibleCount.textContent = formatNumber(rows.length);
  elements.libraryTracks.classList.remove("empty");
  elements.libraryTracks.replaceChildren();

  if (!rows.length) {
    elements.libraryTracks.classList.add("empty");
    elements.libraryTracks.textContent = libraryTracks.length ? "No tracks match the current filters." : "No processed tracks found.";
    return;
  }

  rows.slice(0, 250).forEach((track) => {
    const item = document.createElement("div");
    item.className = "library-row";
    item.role = "row";
    item.innerHTML = `
      <span role="cell">${String(track.index).padStart(3, "0")}</span>
      <strong role="cell" title="${escapeAttr(track.title)}">${escapeHtml(track.title)}</strong>
      <span role="cell" title="${escapeAttr(track.artist)}">${escapeHtml(track.artist)}</span>
      <span role="cell" title="${escapeAttr(track.genre_text)}">${escapeHtml(track.genre_text || "Not tagged")}</span>
      <span role="cell" title="${escapeAttr(track.added_date)}">${escapeHtml(track.added_date || "Not available")}</span>
      <span role="cell" title="${escapeAttr(track.track_id)}">${escapeHtml(track.track_id)}</span>
    `;
    elements.libraryTracks.append(item);
  });

  if (rows.length > 250) {
    const note = document.createElement("div");
    note.className = "library-row library-limit-row";
    note.textContent = `Showing first 250 of ${formatNumber(rows.length)} matching tracks.`;
    elements.libraryTracks.append(note);
  }
}

function compareLibraryTracks(first, second, sort) {
  if (sort === "title") {
    return compareText(first.title, second.title) || first.index - second.index;
  }
  if (sort === "artist") {
    return compareText(first.artist, second.artist) || compareText(first.title, second.title);
  }
  if (sort === "genre") {
    return compareText(first.genre_text, second.genre_text) || compareText(first.artist, second.artist);
  }
  if (sort === "added_date") {
    return compareDate(second.added_date, first.added_date) || first.index - second.index;
  }
  return first.index - second.index;
}

function renderProfileBars(container, rows, options) {
  container.classList.remove("empty");
  container.replaceChildren();

  if (!rows.length) {
    container.classList.add("empty");
    container.textContent = options.emptyText;
    return;
  }

  const max = Math.max(...rows.map((row) => row.count), 1);
  rows.forEach((row, index) => {
    const label = row[options.labelKey];
    const count = row.count || 0;
    const share = options.total ? formatPercent(count / options.total) : "0";
    const item = document.createElement("div");
    item.className = "profile-bar-row";
    item.innerHTML = `
      <span class="profile-rank">${String(index + 1).padStart(2, "0")}</span>
      <span class="profile-name" title="${escapeAttr(label)}">${escapeHtml(label)}</span>
      <strong>${formatNumber(count)}</strong>
      <span>${share}%</span>
      <div class="bar-track"><span class="bar-fill" style="width: ${(count / max) * 100}%"></span></div>
    `;
    container.append(item);
  });
}

function renderGenreExplorer(container, rows) {
  container.classList.remove("empty");
  container.replaceChildren();

  if (!rows.length) {
    container.classList.add("empty");
    container.textContent = "No genre samples found.";
    return;
  }

  rows.forEach((row, index) => {
    const sampleText = row.sample_tracks && row.sample_tracks.length
      ? row.sample_tracks.map((track) => `${track.title} - ${track.artist}`).join("; ")
      : "No sample tracks found.";
    const item = document.createElement("article");
    item.className = "genre-explorer-row";
    item.innerHTML = `
      <span class="profile-rank">${String(index + 1).padStart(2, "0")}</span>
      <div class="genre-explorer-main">
        <strong>${escapeHtml(row.genre)}</strong>
        <span title="${escapeAttr(sampleText)}">${escapeHtml(sampleText)}</span>
      </div>
      <div class="genre-explorer-stat">
        <strong>${formatNumber(row.count)}</strong>
        <span>tracks</span>
      </div>
      <div class="genre-explorer-stat">
        <strong>${formatPercent((row.percentage || 0) / 100)}%</strong>
        <span>share</span>
      </div>
      <div class="genre-explorer-stat">
        <strong>${formatNumber(row.artist_count)}</strong>
        <span>artists</span>
      </div>
    `;
    container.append(item);
  });
}

async function callApi(method, ...args) {
  try {
    if (!window.pywebview || !window.pywebview.api || !window.pywebview.api[method]) {
      return { ok: false, error: "Python API is not available." };
    }
    return await window.pywebview.api[method](...args);
  } catch (error) {
    return { ok: false, error: error.message || String(error) };
  }
}

function setStatus(message, kind = "") {
  elements.status.textContent = message;
  elements.status.className = `status-line ${kind}`.trim();
}

function setLibraryStatus(message, kind = "") {
  elements.libraryStatus.textContent = message;
  elements.libraryStatus.className = `status-line ${kind}`.trim();
}

function setTasteStatus(message, kind = "") {
  elements.tasteStatus.textContent = message;
  elements.tasteStatus.className = `status-line ${kind}`.trim();
}

function setDownloadsStatus(message, kind = "") {
  elements.downloadsStatus.textContent = message;
  elements.downloadsStatus.className = `status-line ${kind}`.trim();
}

function setSettingsStatus(message, kind = "") {
  elements.settingsStatus.textContent = message;
  elements.settingsStatus.className = `status-line ${kind}`.trim();
}

function markSettingsDirty() {
  settingsDirty = true;
  setSettingsStatus("Settings changed.");
  showToast("Unsaved settings changes", "warning", true);
}

function showToast(message, kind = "", sticky = false) {
  elements.toastRegion.replaceChildren();
  const item = document.createElement("div");
  item.className = `toast ${kind}`.trim();
  item.textContent = message;
  elements.toastRegion.append(item);

  if (toastTimer) {
    window.clearTimeout(toastTimer);
    toastTimer = null;
  }

  if (!sticky) {
    toastTimer = window.setTimeout(hideToast, 4000);
  }
}

function hideToast() {
  if (!settingsDirty) {
    elements.toastRegion.replaceChildren();
  }
  if (toastTimer) {
    window.clearTimeout(toastTimer);
    toastTimer = null;
  }
}

function formatNumber(value) {
  return new Intl.NumberFormat().format(value || 0);
}

function formatPercent(value) {
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 1 }).format((value || 0) * 100);
}

function compareText(first, second) {
  return String(first || "").localeCompare(String(second || ""), undefined, { sensitivity: "base" });
}

function compareDate(first, second) {
  const firstTime = Date.parse(first || "");
  const secondTime = Date.parse(second || "");
  if (Number.isNaN(firstTime) && Number.isNaN(secondTime)) {
    return compareText(first, second);
  }
  if (Number.isNaN(firstTime)) {
    return 1;
  }
  if (Number.isNaN(secondTime)) {
    return -1;
  }
  return firstTime - secondTime;
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll("`", "&#096;");
}
