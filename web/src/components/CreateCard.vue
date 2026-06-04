<template>
  <div class="card">
    <h2>Create</h2>
    <form @submit.prevent="submit">
      <label class="label">ISO file</label>
      <input class="input" type="file" accept=".iso" required @change="onFileChange" />

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
        <button class="btn primary" type="submit" :disabled="busy || !file">Upload</button>
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
    error: { type: String, required: true },
    resetKey: { type: Number, required: true }
  },
  emits: ["create"],
  data() {
    return {
      file: null,
      software: [],
      customSoftware: ""
    };
  },
  watch: {
    resetKey() {
      this.file = null;
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
      if (!this.file) return;
      this.$emit("create", { file: this.file, software: this.software, customSoftware: this.customSoftware });
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
