const rawBase = import.meta.env.VITE_API_BASE || "";
const base = rawBase.replace(/\/$/, "");

export function apiUrl(path) {
  if (!path.startsWith("/")) {
    throw new Error("API path must start with /");
  }
  return `${base}${path}`;
}

export async function fetchJson(path, init) {
  const res = await fetch(apiUrl(path), init);
  const contentType = res.headers.get("content-type") || "";
  const isJson = contentType.includes("application/json");
  const body = isJson ? await res.json() : await res.text();
  if (!res.ok) {
    const message = typeof body === "object" && body && "error" in body ? String(body.error) : String(body);
    throw new Error(message || `HTTP ${res.status}`);
  }
  return body;
}

export function isoDownloadUrl(uploadId) {
  return apiUrl(`/api/uploads/${uploadId}/iso`);
}

export async function getHealth() {
  return fetchJson("/api/health");
}

export async function getDefaultSoftware() {
  return fetchJson("/api/default-software");
}

export async function listRoutes() {
  return fetchJson("/api/routes");
}

export async function listUploads() {
  return fetchJson("/api/uploads");
}

export async function searchUploads({ q, software, limit }) {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (limit) params.set("limit", String(limit));
  if (software && software.length) {
    for (const s of software) {
      params.append("software", s);
    }
  }
  const qs = params.toString();
  return fetchJson(`/api/uploads/search${qs ? `?${qs}` : ""}`);
}

export async function getUpload(uploadId) {
  return fetchJson(`/api/uploads/${uploadId}`);
}

export async function getInstallManifest(uploadId) {
  return fetchJson(`/api/uploads/${uploadId}/manifest`);
}

export async function uploadIso({ file, software, customSoftware }) {
  const form = new FormData();
  form.append("iso", file);
  for (const s of software) {
    form.append("software", s);
  }
  if (customSoftware) {
    form.append("custom_software", customSoftware);
  }
  return fetchJson("/api/uploads", { method: "POST", body: form });
}

export async function updateSoftware(uploadId, { software, customSoftware }) {
  return fetchJson(`/api/uploads/${uploadId}/software`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      software,
      custom_software: customSoftware || ""
    })
  });
}

export async function deleteUpload(uploadId) {
  return fetchJson(`/api/uploads/${uploadId}`, { method: "DELETE" });
}
