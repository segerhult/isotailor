<template>
  <div class="card">
    <h2>Search</h2>
    <form @submit.prevent="submit">
      <label class="label">Query</label>
      <input class="textInput" type="text" v-model="q" placeholder="Search by filename, id, software…" />

      <label class="label">Filter software (must include)</label>
      <div class="checks" v-if="defaultSoftware.length">
        <label v-for="name in defaultSoftware" :key="name" class="check">
          <input type="checkbox" :value="name" v-model="software" />
          <span>{{ name }}</span>
        </label>
      </div>
      <div class="muted" v-else>Loading…</div>

      <label class="label">Limit</label>
      <select class="select" v-model.number="limit">
        <option :value="10">10</option>
        <option :value="20">20</option>
        <option :value="50">50</option>
        <option :value="100">100</option>
      </select>

      <div class="actions">
        <button class="btn primary" type="submit" :disabled="busy">Search</button>
        <button class="btn" type="button" @click="clear" :disabled="busy">Clear</button>
      </div>
      <div v-if="error" class="error">{{ error }}</div>
    </form>

    <div style="margin-top: 12px;">
      <div class="muted">Results: {{ count }}</div>
      <ul class="list" v-if="results.length">
        <li v-for="u in results" :key="u.id" class="item">
          <button class="link" @click="$emit('select', u.id)">
            {{ u.original_filename || u.id }}
          </button>
          <div class="meta">id: <code>{{ u.id }}</code></div>
        </li>
      </ul>
      <div v-else class="muted" style="margin-top: 8px;">No results</div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    busy: { type: Boolean, required: true },
    defaultSoftware: { type: Array, required: true },
    results: { type: Array, required: true },
    count: { type: Number, required: true },
    error: { type: String, required: true },
    resetKey: { type: Number, required: true }
  },
  emits: ["search", "clear", "select"],
  data() {
    return {
      q: "",
      software: [],
      limit: 20
    };
  },
  watch: {
    resetKey() {
      this.q = "";
      this.software = [];
      this.limit = 20;
    }
  },
  methods: {
    submit() {
      this.$emit("search", { q: this.q, software: this.software, limit: this.limit });
    },
    clear() {
      this.q = "";
      this.software = [];
      this.limit = 20;
      this.$emit("clear");
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

.muted {
  color: #666;
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

.error {
  margin-top: 10px;
  color: #b00020;
  font-size: 13px;
}

.list {
  list-style: none;
  padding: 0;
  margin:  8px 0 0;
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
</style>
