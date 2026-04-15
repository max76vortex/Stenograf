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
- `python phase_b_processor.py --help` — Phase B LLM processing
- `python check_coverage.py --help` — check which mp3s lack transcripts

**Caveats:**
- Phase A (`transcribe_to_obsidian.py`) requires `faster-whisper` and downloads the large-v3 model (~3 GB) on first real run. The `--help` flag does not trigger the download.
- Phase A requires a GPU with 6+ GB VRAM for `--device cuda`; use `--device cpu` in environments without a GPU (much slower).
- Phase B (`phase_b_processor.py`) requires a running Ollama (port 11434) or LM Studio (port 1234) instance. These are external services not included in the repo.

### No linting or automated tests

This repo has no configured linter, type checker, or test framework. The closest to automated testing is the PowerShell smoke test (`transcription/run-smoke-test.ps1`) which verifies `--help` output.

### Docker in Cloud Agent VMs

Docker requires `fuse-overlayfs` storage driver and `iptables-legacy` in this environment. The daemon config at `/etc/docker/daemon.json` must specify `"storage-driver": "fuse-overlayfs"`. Start dockerd with `sudo dockerd &>/tmp/dockerd.log &` and ensure the socket is accessible (`sudo chmod 666 /var/run/docker.sock`).
