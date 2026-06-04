<template>
  <section class="card">
    <header class="detailTop">
      <div>
        <h2>Upload</h2>
        <div class="muted">
          <div><strong>ISO:</strong> {{ upload.original_filename }}</div>
          <div><strong>ID:</strong> <code>{{ upload.id }}</code></div>
        </div>
      </div>
      <div class="right">
        <a class="btn" :href="isoHref" target="_blank" rel="noreferrer">Download ISO</a>
        <button class="btn danger" @click="$emit('delete')" :disabled="busy">Delete</button>
      </div>
    </header>

    <div class="row">
      <div>
        <h3>Software</h3>
        <div class="checks" v-if="defaultSoftware.length">
          <label v-for="name in defaultSoftware" :key="name" class="check">
            <input type="checkbox" :value="name" v-model="software" />
            <span>{{ name }}</span>
          </label>
        </div>

        <label class="label">Custom software (one per line)</label>
        <textarea class="textarea" v-model="customSoftware"></textarea>

        <div class="actions">
          <button class="btn primary" @click="save" :disabled="busy">Save</button>
          <button class="btn" @click="$emit('load-manifest')" :disabled="busy">Get install manifest</button>
        </div>
        <div v-if="error" class="error">{{ error }}</div>
      </div>

      <div>
        <h3>Install manifest</h3>
        <pre class="pre">{{ manifestText }}</pre>
      </div>
    </div>
  </section>
</template>

<script>
import { isoDownloadUrl } from "../api.js";

function normalizeLines(text) {
  return String(text || "")
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);
}

function softwareToCustomText(defaults, selected) {
  const setDefaults = new Set(defaults);
  return selected.filter((s) => !setDefaults.has(s)).join("\n");
}

function extractDefaultSelections(defaults, selected) {
  const setDefaults = new Set(defaults);
  return selected.filter((s) => setDefaults.has(s));
}

export default {
  props: {
    busy: { type: Boolean, required: true },
    defaultSoftware: { type: Array, required: true },
    upload: { type: Object, required: true },
    manifest: { type: Object, required: false, default: null },
    error: { type: String, required: true }
  },
  emits: ["save-software", "load-manifest", "delete"],
  data() {
    return {
      software: [],
      customSoftware: ""
    };
  },
  computed: {
    isoHref() {
      return isoDownloadUrl(this.upload.id);
    },
    manifestText() {
      return this.manifest ? JSON.stringify(this.manifest, null, 2) : "{\n  \"install\": null\n}";
    }
  },
  watch: {
    upload: {
      immediate: true,
      handler() {
        const selectedSoftware = Array.isArray(this.upload.software) ? this.upload.software : [];
        this.software = extractDefaultSelections(this.defaultSoftware, selectedSoftware);
        this.customSoftware = softwareToCustomText(this.defaultSoftware, selectedSoftware);
      }
    },
    defaultSoftware() {
      const selectedSoftware = Array.isArray(this.upload.software) ? this.upload.software : [];
      this.software = extractDefaultSelections(this.defaultSoftware, selectedSoftware);
      this.customSoftware = softwareToCustomText(this.defaultSoftware, selectedSoftware);
    }
  },
  methods: {
    save() {
      const custom = normalizeLines(this.customSoftware).join("\n");
      this.$emit("save-software", { software: this.software, customSoftware: custom });
    }
  }
};
</script>

<style scoped>
.card {
  border: 1px solid #ddd;
  border-radius: 12px;
  padding: 14px;
  background: #fff;
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

.detailTop {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.right {
  display: flex;
  align-items: center;
  gap: 10px;
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

.label {
  display: block;
  font-size: 12px;
  color: #444;
  margin: 12px 0 6px;
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

code {
  background: #f4f4f4;
  padding: 2px 6px;
  border-radius: 8px;
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
