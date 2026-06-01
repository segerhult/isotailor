<template>
  <main class="wrap">
    <header class="top">
      <div>
        <h1>isotailor</h1>
        <p class="muted">Upload an ISO and choose what software should be installed.</p>
      </div>
      <div class="right">
        <div class="pill">API: {{ apiBaseLabel }}</div>
        <button class="btn" @click="refreshAll" :disabled="busy">Refresh</button>
      </div>
    </header>

    <section class="grid">
      <div class="card">
        <h2>Create</h2>
        <form @submit.prevent="onCreate">
          <label class="label">ISO file</label>
          <input class="input" type="file" accept=".iso" required @change="onFileChange" />

          <div class="row">
            <div>
              <label class="label">Default software</label>
              <div class="checks" v-if="defaultSoftware.length">
                <label v-for="name in defaultSoftware" :key="name" class="check">
                  <input type="checkbox" :value="name" v-model="create.software" />
                  <span>{{ name }}</span>
                </label>
              </div>
              <div class="muted" v-else>Loading…</div>
            </div>
            <div>
              <label class="label">Custom software (one per line)</label>
              <textarea class="textarea" v-model="create.customSoftware" placeholder="e.g.&#10;docker&#10;kubectl"></textarea>
            </div>
          </div>

          <div class="actions">
            <button class="btn primary" type="submit" :disabled="busy || !create.file">Upload</button>
          </div>
          <div v-if="create.error" class="error">{{ create.error }}</div>
        </form>
      </div>

      <div class="card">
        <h2>Uploads</h2>
        <div class="muted" v-if="busy && uploads.length === 0">Loading…</div>
        <ul class="list" v-else>
          <li v-if="uploads.length === 0" class="muted">No uploads yet</li>
          <li v-for="u in uploads" :key="u.id" class="item">
            <button class="link" @click="selectUpload(u.id)">
              {{ u.original_filename || u.id }}
            </button>
            <div class="meta">id: <code>{{ u.id }}</code></div>
          </li>
        </ul>
      </div>
    </section>

    <section class="grid" style="margin-top: 16px;">
      <div class="card">
        <h2>Search</h2>
        <form @submit.prevent="runSearch">
          <label class="label">Query</label>
          <input class="textInput" type="text" v-model="search.q" placeholder="Search by filename, id, software…" />

          <label class="label">Filter software (must include)</label>
          <div class="checks" v-if="defaultSoftware.length">
            <label v-for="name in defaultSoftware" :key="name" class="check">
              <input type="checkbox" :value="name" v-model="search.software" />
              <span>{{ name }}</span>
            </label>
          </div>
          <div class="muted" v-else>Loading…</div>

          <label class="label">Limit</label>
          <select class="select" v-model.number="search.limit">
            <option :value="10">10</option>
            <option :value="20">20</option>
            <option :value="50">50</option>
            <option :value="100">100</option>
          </select>

          <div class="actions">
            <button class="btn primary" type="submit" :disabled="busy">Search</button>
            <button class="btn" type="button" @click="clearSearch" :disabled="busy">Clear</button>
          </div>
          <div v-if="search.error" class="error">{{ search.error }}</div>
        </form>

        <div style="margin-top: 12px;">
          <div class="muted">Results: {{ search.count }}</div>
          <ul class="list" v-if="search.results.length">
            <li v-for="u in search.results" :key="u.id" class="item">
              <button class="link" @click="selectUpload(u.id)">
                {{ u.original_filename || u.id }}
              </button>
              <div class="meta">id: <code>{{ u.id }}</code></div>
            </li>
          </ul>
          <div v-else class="muted" style="margin-top: 8px;">No results</div>
        </div>
      </div>

      <div class="card">
        <h2>API</h2>
        <div class="actions" style="margin-top: 0;">
          <button class="btn" @click="loadRoutes" :disabled="busy">Load routes</button>
        </div>
        <pre class="pre" style="min-height: 240px;">{{ routesText }}</pre>
      </div>
    </section>

    <section v-if="selected" class="card detail">
      <header class="detailTop">
        <div>
          <h2>Upload</h2>
          <div class="muted">
            <div><strong>ISO:</strong> {{ selected.original_filename }}</div>
            <div><strong>ID:</strong> <code>{{ selected.id }}</code></div>
          </div>
        </div>
        <div class="right">
          <a class="btn" :href="isoDownloadHref" target="_blank" rel="noreferrer">Download ISO</a>
          <button class="btn danger" @click="onDelete" :disabled="busy">Delete</button>
        </div>
      </header>

      <div class="row">
        <div>
          <h3>Software</h3>
          <div class="checks" v-if="defaultSoftware.length">
            <label v-for="name in defaultSoftware" :key="name" class="check">
              <input type="checkbox" :value="name" v-model="edit.software" />
              <span>{{ name }}</span>
            </label>
          </div>

          <label class="label">Custom software (one per line)</label>
          <textarea class="textarea" v-model="edit.customSoftware"></textarea>

          <div class="actions">
            <button class="btn primary" @click="onSaveSoftware" :disabled="busy">Save</button>
            <button class="btn" @click="loadManifest" :disabled="busy">Get install manifest</button>
          </div>
          <div v-if="edit.error" class="error">{{ edit.error }}</div>
        </div>

        <div>
          <h3>Install manifest</h3>
          <pre class="pre">{{ manifestText }}</pre>
        </div>
      </div>
    </section>
  </main>
</template>

<script>
import {
  deleteUpload,
  getDefaultSoftware,
  getInstallManifest,
  getUpload,
  isoDownloadUrl,
  listRoutes,
  listUploads,
  searchUploads,
  updateSoftware,
  uploadIso
} from "./api.js";

function softwareToCustomText(defaults, selected) {
  const setDefaults = new Set(defaults);
  return selected.filter((s) => !setDefaults.has(s)).join("\n");
}

function extractDefaultSelections(defaults, selected) {
  const setDefaults = new Set(defaults);
  return selected.filter((s) => setDefaults.has(s));
}

export default {
  data() {
    return {
      busy: false,
      defaultSoftware: [],
      uploads: [],
      routes: null,
      selectedId: null,
      selected: null,
      manifest: null,
      search: {
        q: "",
        software: [],
        limit: 20,
        results: [],
        count: 0,
        error: ""
      },
      create: {
        file: null,
        software: [],
        customSoftware: "",
        error: ""
      },
      edit: {
        software: [],
        customSoftware: "",
        error: ""
      }
    };
  },
  computed: {
    apiBaseLabel() {
      return import.meta.env.VITE_API_BASE || "(same origin)";
    },
    isoDownloadHref() {
      if (!this.selected) return "#";
      return isoDownloadUrl(this.selected.id);
    },
    manifestText() {
      return this.manifest ? JSON.stringify(this.manifest, null, 2) : "{\n  \"install\": null\n}";
    },
    routesText() {
      return this.routes ? JSON.stringify(this.routes, null, 2) : "{\n  \"routes\": null\n}";
    }
  },
  async mounted() {
    await this.refreshAll();
  },
  methods: {
    async refreshAll() {
      this.busy = true;
      this.create.error = "";
      try {
        const [defaults, uploads, routes] = await Promise.all([getDefaultSoftware(), listUploads(), listRoutes()]);
        this.defaultSoftware = defaults.default_software || [];
        this.uploads = uploads.uploads || [];
        this.routes = routes;
        if (this.selectedId) {
          await this.selectUpload(this.selectedId);
        }
      } catch (e) {
        this.create.error = String(e.message || e);
      } finally {
        this.busy = false;
      }
    },
    async loadRoutes() {
      this.busy = true;
      this.create.error = "";
      try {
        this.routes = await listRoutes();
      } catch (e) {
        this.create.error = String(e.message || e);
      } finally {
        this.busy = false;
      }
    },
    clearSearch() {
      this.search.q = "";
      this.search.software = [];
      this.search.limit = 20;
      this.search.results = [];
      this.search.count = 0;
      this.search.error = "";
    },
    async runSearch() {
      this.busy = true;
      this.search.error = "";
      try {
        const resp = await searchUploads({
          q: this.search.q,
          software: this.search.software,
          limit: this.search.limit
        });
        this.search.results = resp.uploads || [];
        this.search.count = resp.count || 0;
      } catch (e) {
        this.search.error = String(e.message || e);
      } finally {
        this.busy = false;
      }
    },
    onFileChange(e) {
      const file = e.target.files && e.target.files[0] ? e.target.files[0] : null;
      this.create.file = file;
    },
    async onCreate() {
      this.busy = true;
      this.create.error = "";
      try {
        const resp = await uploadIso({
          file: this.create.file,
          software: this.create.software,
          customSoftware: this.create.customSoftware
        });
        const upload = resp.upload;
        this.create.file = null;
        this.create.customSoftware = "";
        this.create.software = [];
        await this.refreshAll();
        if (upload && upload.id) {
          await this.selectUpload(upload.id);
        }
      } catch (e) {
        this.create.error = String(e.message || e);
      } finally {
        this.busy = false;
      }
    },
    async selectUpload(id) {
      this.busy = true;
      this.edit.error = "";
      try {
        this.selectedId = id;
        const resp = await getUpload(id);
        this.selected = resp.upload;
        const selectedSoftware = Array.isArray(this.selected.software) ? this.selected.software : [];
        this.edit.software = extractDefaultSelections(this.defaultSoftware, selectedSoftware);
        this.edit.customSoftware = softwareToCustomText(this.defaultSoftware, selectedSoftware);
        this.manifest = null;
      } catch (e) {
        this.edit.error = String(e.message || e);
      } finally {
        this.busy = false;
      }
    },
    async onSaveSoftware() {
      if (!this.selected) return;
      this.busy = true;
      this.edit.error = "";
      try {
        const resp = await updateSoftware(this.selected.id, {
          software: this.edit.software,
          customSoftware: this.edit.customSoftware
        });
        this.selected = resp.upload;
        await this.refreshAll();
      } catch (e) {
        this.edit.error = String(e.message || e);
      } finally {
        this.busy = false;
      }
    },
    async loadManifest() {
      if (!this.selected) return;
      this.busy = true;
      this.edit.error = "";
      try {
        const resp = await getInstallManifest(this.selected.id);
        this.manifest = resp.install;
      } catch (e) {
        this.edit.error = String(e.message || e);
      } finally {
        this.busy = false;
      }
    },
    async onDelete() {
      if (!this.selected) return;
      this.busy = true;
      this.edit.error = "";
      try {
        await deleteUpload(this.selected.id);
        this.selected = null;
        this.selectedId = null;
        this.manifest = null;
        await this.refreshAll();
      } catch (e) {
        this.edit.error = String(e.message || e);
      } finally {
        this.busy = false;
      }
    }
  }
};
</script>

<style scoped>
.wrap {
  max-width: 1100px;
  margin: 24px auto;
  padding: 0 16px;
  font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  color: #111;
}

.top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 18px;
}

h1 {
  margin: 0;
  font-size: 28px;
}

h2 {
  margin: 0 0 12px;
  font-size: 18px;
}

h3 {
  margin: 0 0 10px;
  font-size: 16px;
}

.muted {
  color: #666;
}

.pill {
  border: 1px solid #ddd;
  background: #fafafa;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
}

.right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.grid {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 16px;
  align-items: start;
}

@media (max-width: 900px) {
  .grid {
    grid-template-columns: 1fr;
  }
}

.card {
  border: 1px solid #ddd;
  border-radius: 12px;
  padding: 14px;
  background: #fff;
}

.label {
  display: block;
  font-size: 12px;
  color: #444;
  margin: 12px 0 6px;
}

.input {
  width: 100%;
}

.textInput {
  width: 100%;
  padding: 10px 10px;
  border: 1px solid #ddd;
  border-radius: 10px;
  font-size: 13px;
}

.select {
  width: 100%;
  padding: 10px 10px;
  border: 1px solid #ddd;
  border-radius: 10px;
  background: #fff;
  font-size: 13px;
}

.textarea {
  width: 100%;
  min-height: 110px;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 10px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 12px;
}

.checks {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px 12px;
  border: 1px solid #eee;
  border-radius: 10px;
  padding: 10px;
  background: #fafafa;
}

.check {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #222;
}

.actions {
  display: flex;
  gap: 10px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.btn {
  border: 1px solid #333;
  border-radius: 10px;
  padding: 10px 12px;
  background: #fff;
  color: #111;
  cursor: pointer;
  text-decoration: none;
  font-size: 13px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn.primary {
  background: #111;
  color: #fff;
}

.btn.danger {
  border-color: #b00020;
  color: #b00020;
}

.error {
  margin-top: 10px;
  color: #b00020;
  font-size: 13px;
}

.list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.item {
  border-top: 1px solid #eee;
  padding: 10px 0;
}

.item:first-child {
  border-top: 0;
  padding-top: 0;
}

.link {
  border: 0;
  background: transparent;
  padding: 0;
  cursor: pointer;
  color: #0a58ca;
  font-size: 13px;
  text-align: left;
}

.link:hover {
  text-decoration: underline;
}

.meta {
  margin-top: 4px;
  font-size: 12px;
  color: #666;
}

code {
  background: #f4f4f4;
  padding: 2px 6px;
  border-radius: 8px;
}

.detail {
  margin-top: 16px;
}

.detailTop {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  align-items: start;
}

@media (max-width: 900px) {
  .row {
    grid-template-columns: 1fr;
  }
}

.pre {
  border: 1px solid #eee;
  border-radius: 12px;
  padding: 12px;
  background: #fafafa;
  overflow: auto;
  min-height: 200px;
  font-size: 12px;
}
</style>
