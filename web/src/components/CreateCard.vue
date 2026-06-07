<template>
  <div class="card">
    <h2>Create</h2>
    <form @submit.prevent="submit">
      <label class="label">ISO source</label>
      <select class="select" v-model="source">
        <option value="upload">Upload .iso</option>
        <option value="distribution">Pick distribution</option>
      </select>

      <div v-if="source === 'upload'">
        <label class="label">ISO file</label>
        <input class="input" type="file" accept=".iso" required @change="onFileChange" />
      </div>

      <div v-else>
        <label class="label">Distribution</label>
        <select class="select" v-model="distributionId" :disabled="!distributions.length">
          <option value="" disabled>Select a distribution…</option>
          <option v-for="d in distributions" :key="d.id" :value="d.id">
            {{ d.name }} {{ d.version }} ({{ d.arch }})
          </option>
        </select>
        <div class="muted" v-if="selectedDistribution && selectedDistribution.iso_url">
          Downloads: {{ selectedDistribution.iso_url }}
        </div>
        <div class="muted" v-else-if="!distributions.length">Loading…</div>
      </div>

      <div class="row">
        <div>
          <label class="label">Default software</label>
          <div class="checks" v-if="defaultSoftware.length">
            <label v-for="name in defaultSoftware" :key="name" class="check">
              <input type="checkbox" :value="name" v-model="software" />
              <span>{{ name }}</span>
            </label>
          </div>
          <div class="muted" v-else>Loading…</div>
        </div>
        <div>
          <label class="label">Custom software (one per line)</label>
          <textarea
            class="textarea"
            v-model="customSoftware"
            placeholder="e.g.&#10;docker&#10;kubectl"
          ></textarea>
        </div>
      </div>

      <div class="actions">
        <button class="btn primary" type="submit" :disabled="submitDisabled">
          {{ source === "upload" ? "Upload" : "Download + Create" }}
        </button>
      </div>
      <div v-if="error" class="error">{{ error }}</div>
    </form>
  </div>
</template>

<script>
export default {
  props: {
    busy: { type: Boolean, required: true },
    defaultSoftware: { type: Array, required: true },
    distributions: { type: Array, required: true },
    error: { type: String, required: true },
    resetKey: { type: Number, required: true }
  },
  emits: ["create"],
  data() {
    return {
      source: "upload",
      file: null,
      distributionId: "",
      software: [],
      customSoftware: ""
    };
  },
  computed: {
    selectedDistribution() {
      return this.distributions.find((d) => d.id === this.distributionId) || null;
    },
    submitDisabled() {
      if (this.busy) return true;
      if (this.source === "upload") return !this.file;
      return !this.distributionId;
    }
  },
  watch: {
    resetKey() {
      this.source = "upload";
      this.file = null;
      this.distributionId = "";
      this.software = [];
      this.customSoftware = "";
    }
  },
  methods: {
    onFileChange(e) {
      const next = e.target.files && e.target.files[0] ? e.target.files[0] : null;
      this.file = next;
    },
    submit() {
      if (this.source === "upload") {
        if (!this.file) return;
        this.$emit("create", {
          mode: "upload",
          file: this.file,
          software: this.software,
          customSoftware: this.customSoftware
        });
        return;
      }

      if (!this.distributionId) return;
      this.$emit("create", {
        mode: "distribution",
        distributionId: this.distributionId,
        software: this.software,
        customSoftware: this.customSoftware
      });
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

.label {
  display: block;
  font-size: 12px;
  color: #444;
  margin: 12px 0 6px;
}

.input {
  width: 100%;
}

.select {
  width: 100%;
  padding: 10px 10px;
  border: 1px solid #ddd;
  border-radius: 10px;
  background: #fff;
  font-size: 13px;
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

.muted {
  color: #666;
}

.error {
  margin-top: 10px;
  color: #b00020;
  font-size: 13px;
}
</style>
