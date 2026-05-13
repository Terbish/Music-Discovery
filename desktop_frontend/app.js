let selectedLibraryPath = null;
let activeView = "dashboard";
let dashboardData = null;
let libraryTracks = [];
let libraryGenreOptions = [];

const elements = {
  status: document.querySelector("#status"),
  libraryStatus: document.querySelector("#library-status"),
  tasteStatus: document.querySelector("#taste-status"),
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
  navItems: document.querySelectorAll("[data-view-target]"),
  views: document.querySelectorAll("[data-view]"),
  settingsForm: document.querySelector("#settings-form"),
  saveSettings: document.querySelector("#save-settings"),
  resetSettings: document.querySelector("#reset-settings"),
  libraryPath: document.querySelector("#library-path"),
  outputPath: document.querySelector("#output-path"),
  audioOutputPath: document.querySelector("#audio-output-path"),
  audioFormat: document.querySelector("#audio-format"),
  batchSize: document.querySelector("#batch-size"),
  launchAtStartup: document.querySelector("#launch-at-startup"),
  minimizeToTray: document.querySelector("#minimize-to-tray"),
  notificationsEnabled: document.querySelector("#notifications-enabled"),
  useRepoPersonalDir: document.querySelector("#use-repo-personal-dir"),
  browseLibraryPath: document.querySelector("#browse-library-path"),
  browseOutputPath: document.querySelector("#browse-output-path"),
  browseAudioOutputPath: document.querySelector("#browse-audio-output-path"),
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
  elements.processLibrary.addEventListener("click", processLibrary);
  elements.refreshLibrary.addEventListener("click", loadLibrary);
  elements.processLibraryView.addEventListener("click", processLibrary);
  elements.librarySearch.addEventListener("input", renderLibraryTracks);
  elements.libraryGenreFilter.addEventListener("change", renderLibraryTracks);
  elements.librarySort.addEventListener("change", renderLibraryTracks);
  elements.refreshTasteProfile.addEventListener("click", loadTasteProfile);
  elements.processProfileLibrary.addEventListener("click", processLibrary);
  elements.saveSettings.addEventListener("click", saveSettings);
  elements.resetSettings.addEventListener("click", loadSettings);
  elements.settingsForm.addEventListener("submit", (event) => event.preventDefault());
  elements.settingsForm.addEventListener("input", () => setSettingsStatus("Settings changed."));
  elements.browseLibraryPath.addEventListener("click", browseLibraryPath);
  elements.browseOutputPath.addEventListener("click", () => browseDirectory(elements.outputPath));
  elements.browseAudioOutputPath.addEventListener("click", () => browseDirectory(elements.audioOutputPath));

  if (!window.pywebview) {
    setStatus("Open this screen from desktop_app.py to connect the Python API.", "error");
    setLibraryStatus("Open this screen from desktop_app.py to connect the Python API.", "error");
    setTasteStatus("Open this screen from desktop_app.py to connect the Python API.", "error");
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

async function loadSettings() {
  setSettingsStatus("Loading settings.");
  const response = await callApi("get_settings");
  if (!response.ok) {
    setSettingsStatus(response.error, "error");
    return;
  }

  renderSettings(response.data);
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
    setSettingsStatus("Settings changed.");
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
    setSettingsStatus("Settings changed.");
  }
}

function setProgressStatus(detail) {
  const labels = {
    enriching_genres: "Enriching genres",
    processing_library: "Processing library",
  };
  const label = labels[detail.phase] || detail.message || "Working";
  const current = formatNumber(detail.current);
  const total = formatNumber(detail.total);

  if (detail.total !== undefined && detail.total !== null) {
    setStatus(`${label} ${current}/${total}.`);
    setLibraryStatus(`${label} ${current}/${total}.`);
    setTasteStatus(`${label} ${current}/${total}.`);
    return;
  }

  setStatus(label);
  setLibraryStatus(label);
  setTasteStatus(label);
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
  elements.batchSize.value = settings.batch_size || 20;
  elements.launchAtStartup.checked = Boolean(settings.launch_at_startup);
  elements.minimizeToTray.checked = Boolean(settings.minimize_to_tray);
  elements.notificationsEnabled.checked = Boolean(settings.notifications_enabled);
  elements.useRepoPersonalDir.checked = Boolean(settings.use_repo_personal_dir);
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
      <strong>${escapeHtml(row.date)} - ${formatNumber(row.track_count)} tracks</strong>
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

function setSettingsStatus(message, kind = "") {
  elements.settingsStatus.textContent = message;
  elements.settingsStatus.className = `status-line ${kind}`.trim();
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
