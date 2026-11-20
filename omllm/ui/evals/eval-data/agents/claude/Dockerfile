ARG TASK_IMAGE
FROM node:22-bookworm-slim AS node
FROM ${TASK_IMAGE}

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends libatomic1 libstdc++6 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=node /usr/local/ /usr/local/

ARG AGENT_VERSION=2.1.319
RUN npm install --global --no-audit --no-fund "@anthropic-ai/claude-code@${AGENT_VERSION}" \
    && npm cache clean --force

USER agent
WORKDIR /work
