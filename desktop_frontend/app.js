let selectedLibraryPath = null;

const elements = {
  status: document.querySelector("#status"),
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
};

window.addEventListener("pywebviewready", loadDashboard);
window.addEventListener("backend-progress", (event) => {
  setProgressStatus(event.detail);
});

document.addEventListener("DOMContentLoaded", () => {
  elements.chooseLibrary.addEventListener("click", chooseLibrary);
  elements.processLibrary.addEventListener("click", processLibrary);

  if (!window.pywebview) {
    setStatus("Open this screen from desktop_app.py to connect the Python API.", "error");
  }
});

async function loadDashboard() {
  setStatus("Loading dashboard data.");
  const response = await callApi("get_dashboard_data");
  if (!response.ok) {
    setStatus(response.error, "error");
    return;
  }

  renderDashboard(response.data);
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
  elements.processLibrary.disabled = true;
  const response = await callApi("process_library", selectedLibraryPath);
  elements.processLibrary.disabled = false;

  if (!response.ok) {
    setStatus(response.error, "error");
    return;
  }

  const enrichedPath = response.data.outputs.enriched_csv;
  setStatus(`Processed ${formatNumber(response.data.total_tracks)} tracks from ${enrichedPath}.`, "success");
  await loadDashboard();
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
    return;
  }

  setStatus(label);
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

function formatNumber(value) {
  return new Intl.NumberFormat().format(value || 0);
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
