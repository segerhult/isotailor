<template>
  <div class="card">
    <h2>Uploads</h2>
    <div class="muted" v-if="busy && uploads.length === 0">Loading…</div>
    <ul class="list" v-else>
      <li v-if="uploads.length === 0" class="muted">No uploads yet</li>
      <li v-for="u in uploads" :key="u.id" class="item">
        <button class="link" @click="$emit('select', u.id)">
          {{ u.original_filename || u.id }}
        </button>
        <div class="meta">id: <code>{{ u.id }}</code></div>
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  props: {
    busy: { type: Boolean, required: true },
    uploads: { type: Array, required: true }
  },
  emits: ["select"]
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

.muted {
  color: #666;
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
</style>
