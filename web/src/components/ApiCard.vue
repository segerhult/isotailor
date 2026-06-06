<template>
  <div class="card">
    <h2>API</h2>
    <div class="actions" style="margin-top: 0;">
      <button class="btn" @click="$emit('load')" :disabled="busy">Load routes</button>
    </div>
    <div v-if="error" class="error">{{ error }}</div>
    <pre class="pre">{{ routesText }}</pre>
  </div>
</template>

<script>
export default {
  props: {
    busy: { type: Boolean, required: true },
    routes: { type: Object, required: false, default: null },
    error: { type: String, required: true }
  },
  emits: ["load"],
  computed: {
    routesText() {
      return this.routes ? JSON.stringify(this.routes, null, 2) : "{\n  \"routes\": null\n}";
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

.error {
  margin-top: 10px;
  color: #b00020;
  font-size: 13px;
}

.pre {
  border: 1px solid #eee;
  border-radius: 12px;
  padding: 12px;
  background: #fafafa;
  overflow: auto;
  min-height: 240px;
  font-size: 12px;
}
</style>
