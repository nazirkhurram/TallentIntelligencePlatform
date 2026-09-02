#!/bin/bash
set -e

if [ -z "${GITHUB_REPO_URL}" ] || [ -z "${RUNNER_TOKEN}" ]; then
    echo "ERROR: GITHUB_REPO_URL and RUNNER_TOKEN environment variables are required."
    exit 1
fi

RUNNER_NAME="${RUNNER_NAME:-onprem-runner-$(hostname)-$$}"
RUNNER_LABELS="${RUNNER_LABELS:-self-hosted,on-prem,linux,x64}"

echo "==> Configuring ephemeral GitHub Actions Runner: ${RUNNER_NAME}"
./config.sh \
    --url "${GITHUB_REPO_URL}" \
    --token "${RUNNER_TOKEN}" \
    --name "${RUNNER_NAME}" \
    --labels "${RUNNER_LABELS}" \
    --work "_work" \
    --ephemeral \
    --unattended \
    --replace

echo "==> Starting runner listening for 1 job..."
exec ./run.sh
