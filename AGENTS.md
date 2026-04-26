---
description: 
alwaysApply: true
---

# AGENTS.md

## Cursor Cloud specific instructions

### Repository overview

This is a personal automation workspace with three sub-projects sharing one repo:

| Sub-project | Location | Runtime |
|---|---|---|
| **n8n** (workflow automation) | `docker-compose.yml` + `nginx/` | Docker container (`n8nio/n8n:latest`) on port 5678 |
| **Transcription pipeline** | `transcription/` | Python 3.10+ venv (`transcription/.venv/`) |
| **MAS** (Multi-Agent System) | `multi-agent-system/` | Prompt/methodology framework — no runtime |

### Starting n8n

```bash
# Docker daemon must be running first:
sudo dockerd &>/tmp/dockerd.log &
# Then wait a few seconds and:
docker compose up -d          # from repo root
# n8n is at http://localhost:5678
```

The `.env` file is gitignored. For local dev, create a minimal one:

```bash
cat > .env << 'EOF'
N8N_HOST=localhost
N8N_PROTOCOL=http
N8N_PORT=5678
WEBHOOK_URL=http://localhost:5678/
N8N_PROXY_HOPS=0
GENERIC_TIMEZONE=Europe/Moscow
EOF
```

### Running transcription scripts

All Python scripts live in `transcription/`. Activate the venv first:

```bash
source transcription/.venv/bin/activate
```

Key commands (see `transcription/README.md` for full usage):

- `python transcribe_to_obsidian.py --help` — Phase A transcription
- `phase-b-process` skill — Phase B text processing (Kimi in Cursor, project-only)
- `python transcription_limit_dispatcher.py --help` — batching under free transcription limits
- `python check_coverage.py --help` — check which mp3s lack transcripts

**Caveats:**
- Phase A (`transcribe_to_obsidian.py`) requires `faster-whisper` and downloads the large-v3 model (~3 GB) on first real run. The `--help` flag does not trigger the download.
- Phase A requires a GPU with 6+ GB VRAM for `--device cuda`; use `--device cpu` in environments without a GPU (much slower).
- Phase B in this repo is fixed to the local skill `.cursor/skills/user-mas-phase-b-process/SKILL.md` and should not fall back to Ollama/LM Studio scripts.

### Project-bound skills

- Skills in `.cursor/skills/` are scoped to this repository (`C:\Users\sa\N8N-projects`) and should not be reused in other projects by default.
- Current transcription skills:
  - `.cursor/skills/user-mas-phase-b-process/SKILL.md` — **the only allowed Phase B path** (model: Kimi).
  - `.cursor/skills/user-mb-init/SKILL.md` — memory-bank bootstrap/update helper.
  - `.cursor/skills/user-mb-activity-report/SKILL.md` — activity reporting for this workspace.

### No linting or automated tests

This repo has no configured linter, type checker, or test framework. The closest to automated testing is the PowerShell smoke test (`transcription/run-smoke-test.ps1`) which verifies `--help` output.

### Docker in Cloud Agent VMs

Docker requires `fuse-overlayfs` storage driver and `iptables-legacy` in this environment. The daemon config at `/etc/docker/daemon.json` must specify `"storage-driver": "fuse-overlayfs"`. Start dockerd with `sudo dockerd &>/tmp/dockerd.log &` and ensure the socket is accessible (`sudo chmod 666 /var/run/docker.sock`).
