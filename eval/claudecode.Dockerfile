FROM node:20-slim
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv curl git && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 10001 agent
COPY claude-code /opt/claude-code
RUN chmod +x /opt/claude-code/bin/claude.exe
USER agent
WORKDIR /workspace
