#!/usr/bin/env bash
set -euo pipefail

RUNNER_REPO_URL="${RUNNER_REPO_URL:-}"
RUNNER_TOKEN="${RUNNER_TOKEN:-}"
RUNNER_NAME="${RUNNER_NAME:-$(hostname)}"
RUNNER_LABELS="${RUNNER_LABELS:-self-hosted,linux,x64}"
RUNNER_WORKDIR="${RUNNER_WORKDIR:-_work}"
RUNNER_EPHEMERAL="${RUNNER_EPHEMERAL:-0}"
RUNNER_HEALTH_SERVER="${RUNNER_HEALTH_SERVER:-1}"
RUNNER_HEALTH_PORT="${RUNNER_HEALTH_PORT:-${PORT:-8080}}"

if [[ -z "${RUNNER_REPO_URL}" ]]; then
  echo "RUNNER_REPO_URL is required (e.g. https://github.com/OWNER/REPO or https://github.com/ORG)"
  exit 1
fi

if [[ -z "${RUNNER_TOKEN}" ]]; then
  echo "RUNNER_TOKEN is required (registration token from GitHub)"
  exit 1
fi

cd /actions-runner

if [[ "${RUNNER_HEALTH_SERVER}" == "1" || "${RUNNER_HEALTH_SERVER}" == "true" || "${RUNNER_HEALTH_SERVER}" == "yes" ]]; then
  python3 -m http.server "${RUNNER_HEALTH_PORT}" --bind 0.0.0.0 >/dev/null 2>&1 &
fi

cleanup() {
  if [[ -f .runner ]]; then
    ./config.sh remove --unattended --token "${RUNNER_TOKEN}" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

ephemeral_flag=()
if [[ "${RUNNER_EPHEMERAL}" == "1" || "${RUNNER_EPHEMERAL}" == "true" || "${RUNNER_EPHEMERAL}" == "yes" ]]; then
  ephemeral_flag=(--ephemeral)
fi

./config.sh \
  --unattended \
  --url "${RUNNER_REPO_URL}" \
  --token "${RUNNER_TOKEN}" \
  --name "${RUNNER_NAME}" \
  --work "${RUNNER_WORKDIR}" \
  --labels "${RUNNER_LABELS}" \
  "${ephemeral_flag[@]}"

exec ./run.sh
