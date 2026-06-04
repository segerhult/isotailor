<template>
  <header class="top">
    <div>
      <h1>isotailor</h1>
      <p class="muted">Upload an ISO and choose what software should be installed.</p>
    </div>
    <div class="right">
      <div class="pill">API: {{ apiBaseLabel }}</div>
      <button class="btn" @click="$emit('refresh')" :disabled="busy">Refresh</button>
    </div>
  </header>
</template>

<script>
export default {
  props: {
    apiBaseLabel: { type: String, required: true },
    busy: { type: Boolean, required: true }
  },
  emits: ["refresh"]
};
</script>

<style scoped>
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

.muted {
  color: #666;
}

.right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pill {
  border: 1px solid #ddd;
  background: #fafafa;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
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
</style>
