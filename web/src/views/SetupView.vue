<template>
  <main class="wrap">
    <header class="top">
      <div>
        <h1>Setup</h1>
        <p class="muted">Local and deployment setup snippets.</p>
      </div>
    </header>

    <section class="grid">
      <div class="card">
        <h2>Backend</h2>
        <pre class="pre">{{ backendText }}</pre>
      </div>

      <div class="card">
        <h2>Web</h2>
        <pre class="pre">{{ webText }}</pre>
      </div>
    </section>

    <section class="grid" style="margin-top: 16px;">
      <div class="card">
        <h2>Runner env</h2>
        <pre class="pre">{{ runnerEnvText }}</pre>
      </div>

      <div class="card">
        <h2>Runner docker</h2>
        <pre class="pre">{{ runnerDockerText }}</pre>
      </div>
    </section>
  </main>
</template>

<script>
export default {
  computed: {
    backendText() {
      return [
        "python3 server.py --host 127.0.0.1 --port 8080",
        "",
        "API: http://127.0.0.1:8080/api/health"
      ].join("\n");
    },
    webText() {
      return [
        "VITE_API_BASE=http://127.0.0.1:8080 npm --prefix web run dev",
        "",
        "npm --prefix web run build"
      ].join("\n");
    },
    runnerEnvText() {
      return [
        "RUNNER_REPO_URL=https://github.com/OWNER/REPO",
        "RUNNER_TOKEN=REPLACE_WITH_GITHUB_RUNNER_REGISTRATION_TOKEN",
        "RUNNER_NAME=isotailor-runner-1",
        "RUNNER_LABELS=self-hosted,linux,x64,isotailor",
        "RUNNER_WORKDIR=_work",
        "RUNNER_EPHEMERAL=1",
        "RUNNER_HEALTH_SERVER=1",
        "RUNNER_HEALTH_PORT=8080"
      ].join("\n");
    },
    runnerDockerText() {
      return [
        "docker build -t isotailor-actions-runner ./actions-runner",
        "",
        "docker run --rm --env-file .env isotailor-actions-runner"
      ].join("\n");
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

.muted {
  color: #666;
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
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

.pre {
  border: 1px solid #eee;
  border-radius: 12px;
  padding: 12px;
  background: #fafafa;
  overflow: auto;
  min-height: 180px;
  font-size: 12px;
}
</style>
