import { api, upload } from "./api.js";
import { el, time, message } from "./ui.js";

const $ = selector => document.querySelector(selector);
const page = document.body.dataset.page;
const params = new URLSearchParams(location.search);
const path = "/api/documents/" + encodeURIComponent(params.get("id"));
const states = ["Received", "Validating", "Validated", "Processed", "Failed"];
let previous = "";
let requestNumber = 0;

function badge(value) {
  const node = el("span", value);
  node.className = "badge";
  node.dataset.state = value;
  return node;
}

function renderCounts(stats) {
  $("#total").textContent = Object.values(stats).reduce((sum, n) => sum + n, 0);
  $("#counts").replaceChildren(...states.map(state => {
    const link = el("a");
    link.className = "stage";
    link.href = "/documents.html?status=" + state;
    link.append(badge(state), el("strong", stats[state] ?? 0));
    return link;
  }));
}

function renderList(rows) {
  const list = $("#list");
  list.setAttribute("aria-busy", "false");
  if (!rows.length) {
    list.replaceChildren(el("p", page === "index" ? "Your uploads will appear here." : "No documents match these filters."));
    return;
  }
  const table = el("table");
  table.setAttribute("aria-label", page === "index" ? "Recent documents" : "Document library");
  const heading = table.createTHead().insertRow();
  for (const title of ["Document", "Status", "Uploaded"]) {
    const th = el("th", title);
    th.scope = "col";
    heading.append(th);
  }
  const body = table.createTBody();
  for (const doc of rows) {
    const row = body.insertRow();
    const link = el("a");
    link.className = "file-link";
    link.href = "/document.html?id=" + encodeURIComponent(doc.file_id);
    const icon = el("span", "PDF");
    icon.className = "file-symbol";
    icon.setAttribute("aria-hidden", "true");
    link.append(icon, el("span", doc.original_filename));
    row.insertCell().append(link);
    row.insertCell().append(badge(doc.status));
    row.insertCell().textContent = time(doc.uploaded_at);
  }
  list.replaceChildren(table);
}

function renderDetail(doc, history) {
  $("#name").textContent = doc.original_filename;
  $("#current").replaceChildren(badge(doc.status));
  $("#reprocess").hidden = doc.status !== "Failed";
  $("#delete").disabled = !["Failed", "Processed"].includes(doc.status);
  const labels = {
    failure_reason: "Failure reason", error_code: "Error code", page_count: "Pages",
    size_bytes: "Size (bytes)", pdf_version: "PDF version", processing_duration_ms: "Processing time (ms)",
    content_duplicate: "Duplicate content", content_duplicate_of: "Matches document",
    attempt_count: "Attempts", current_attempt_id: "Current attempt", sha256: "SHA-256",
    uploaded_at: "Uploaded", updated_at: "Last updated", file_id: "Document ID",
    content_type: "Content type", warnings: "Warning flags", generation: "Object generation",
    storage_key: "Storage key", owner_id: "Owner"
  };
  const entries = Object.entries(labels).filter(([k]) => doc[k] !== undefined && doc[k] !== null);
  $("#details").replaceChildren(...entries.map(([key, label]) => {
    const value = doc[key];
    const display = key.endsWith("_at") ? time(value) : Array.isArray(value) ? value.join(", ") || "None" :
      typeof value === "boolean" ? (value ? "Yes" : "No") : String(value);
    const line = el("div");
    line.append(el("dt", label), el("dd", display));
    return line;
  }));
  $("#history").replaceChildren(...history.map(event => {
    const line = el("li");
    line.append(badge(event.stage), el("small", time(event.timestamp)));
    const note = [event.outcome !== event.stage && event.outcome, event.error_code,
      event.trigger === "manual-reprocess" && "Manual reprocess"].filter(Boolean);
    if (note.length) line.append(el("small", note.join(" · ")));
    return line;
  }));
}

async function refresh() {
  const number = ++requestNumber;
  let data;
  if (page === "document") {
    data = await Promise.all([api(path), api(path + "/history")]);
  } else if (page === "index") {
    data = await Promise.all([api("/api/documents?limit=5"), api("/api/stats")]);
  } else {
    const query = new URLSearchParams({
      q: $("#query").value, status: $("#status").value, sort: $("#sort").value.toLowerCase()
    });
    data = [await api("/api/documents?" + query)];
  }
  if (number !== requestNumber) return;
  const next = JSON.stringify(data);
  if (previous === next) return;
  previous = next;
  if (page === "document") renderDetail(...data);
  else {
    renderList(data[0]);
    if (page === "index") renderCounts(data[1]);
  }
}

function enableUpload() {
  const drop = $("#drop");
  async function run(files) {
    for (const file of Array.from(files)) {
      const item = el("li");
      const progress = el("progress");
      progress.max = 1;
      progress.value = 0;
      progress.setAttribute("aria-label", "Upload progress for " + file.name);
      item.append(el("strong", file.name), progress);
      $("#results").append(item);
      try {
        const result = await upload(file, progress);
        const link = el("a", "View document");
        link.href = "/document.html?id=" + encodeURIComponent(result.file_id);
        item.append(link);
        message("Upload received");
      } catch (err) {
        item.append(el("span", err.message));
        message("Upload failed");
      }
    }
  }
  drop.onsubmit = async event => {
    event.preventDefault();
    const button = drop.querySelector("button");
    button.disabled = true;
    try { await run(drop.querySelector("input").files); }
    finally { button.disabled = false; }
  };
  drop.ondragover = event => { event.preventDefault(); drop.classList.add("dragover"); };
  drop.ondragleave = () => drop.classList.remove("dragover");
  drop.ondrop = event => {
    event.preventDefault();
    drop.classList.remove("dragover");
    run(event.dataTransfer.files);
  };
}

async function showServices() {
  const items = await api("/api/integrations");
  $("#services").replaceChildren(...items.map(service => {
    const card = el("article");
    card.append(badge(service.status), el("h2", service.service), el("p", service.limitations));
    for (const path of service.evidence_links) {
      const link = el("a", "Download verification evidence");
      link.href = "/api/" + path;
      card.append(link);
    }
    card.append(el("small", "Verified " + service.last_verified_at));
    return card;
  }));
  $("#services").setAttribute("aria-busy", "false");
}

async function start() {
  const session = await api("/api/auth/me");
  if (page === "login") {
    $("form").onsubmit = async event => {
      event.preventDefault();
      try {
        await api("/api/auth/login", "POST", Object.fromEntries(new FormData(event.target)));
        location.assign("/");
      } catch (err) { message(err.message); }
    };
    return;
  }
  if (!session.authenticated) { location.replace("/login.html"); return; }
  $("#logout").onclick = async () => { await api("/api/auth/logout", "POST"); location.replace("/login.html"); };
  if (page === "upload") { enableUpload(); return; }
  if (page === "integrations") { await showServices(); return; }
  if (page === "documents") {
    if (states.includes(params.get("status"))) $("#status").value = params.get("status");
    document.querySelectorAll("input, select").forEach(input => { input.oninput = refresh; });
  }
  if (page === "document") {
    $("#download").onclick = () => location.assign(path + "/download");
    $("#delete").onclick = async () => {
      if (confirm("Delete this document and its history?")) {
        await api(path, "DELETE"); location.assign("/documents.html");
      }
    };
    $("#reprocess").onclick = async () => { await api(path + "/reprocess", "POST"); await refresh(); };
  }
  await refresh();
  const timer = setInterval(() => { if (!document.hidden) refresh().catch(error => message(error.message)); }, 2500);
  window.addEventListener("pagehide", () => clearInterval(timer));
}

window.addEventListener("unhandledrejection", event => message(event.reason.message));
start().catch(error => message(error.message));
