# ==============================================================================
# Ephemeral Self-Hosted GitHub Actions Runner
# ==============================================================================
FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    RUNNER_VERSION=2.321.0

# Install dependencies and Docker CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    jq \
    git \
    tar \
    docker.io \
    docker-compose-v2 \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated runner user
RUN useradd -m -s /bin/bash runner && \
    usermod -aG docker runner

WORKDIR /home/runner

# Download and extract GitHub Actions runner binary
RUN curl -o actions-runner-linux.tar.gz -L \
    "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" && \
    tar xzf actions-runner-linux.tar.gz && \
    rm actions-runner-linux.tar.gz && \
    ./bin/installdependencies.sh

COPY entrypoint.sh /home/runner/entrypoint.sh
RUN chmod +x /home/runner/entrypoint.sh && \
    chown -R runner:runner /home/runner

USER runner

ENTRYPOINT ["/home/runner/entrypoint.sh"]
