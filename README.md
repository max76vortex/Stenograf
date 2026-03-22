# N8N-projects

Конфигурация n8n для домена **n8n.maxvortex.ru**.

**Статус:** развёрнуто на сервере. Доступ: https://n8n.maxvortex.ru

---

## Локально (разработка)

```bash
cd N8N-projects
docker compose up -d
```

n8n будет доступен на http://localhost:5678

---

## На сервере (n8n.maxvortex.ru)

### 1. Скопировать проект на сервер

```bash
scp -r N8N-projects user@your-server:/home/user/
```

### 2. Установить Docker (если нет)

```bash
curl -fsSL https://get.docker.com | sh
```

### 3. Запустить n8n

```bash
cd /home/user/N8N-projects
bash server-setup.sh
# или вручную:
docker compose up -d
```

### 4. Настроить reverse proxy (Nginx)

Конфиг уже в `/etc/nginx/vhosts/max/n8n.maxvortex.ru.conf` (прокси на 127.0.0.1:5678).
SSL — wildcard `*.maxvortex.ru`. После изменений: `nginx -t && systemctl reload nginx`

### 5. DNS

A-запись: `n8n.maxvortex.ru` → IP вашего сервера.

---

## Структура

```
N8N-projects/
├── docker-compose.yml    # Контейнер n8n
├── .env                  # Переменные (домен, протокол)
├── nginx/                # Конфиг Nginx для reverse proxy
├── multi-agent-system/   # MAS: оркестрация, промпты ролей (agents/), артефакты, runbook'и
├── server-setup.sh       # Скрипт установки на сервере
└── README.md
```

---

## Журнал активности и отчёты по времени

- Журнал: `memory-bank/activity-journal.md` (ISO-время, источник: Manual / GitCommit / Scheduled).
- Дописать строку: `pwsh -NoLogo -File "scripts/append-activity-journal.ps1" -Message "..."`.
- Сводка в консоль: `pwsh -NoLogo -File "scripts/Get-ActivityReport.ps1"`.
- После каждого коммита (опционально): `git config core.hooksPath .githooks` — см. `scripts/README.md`.
- Скилл агента: **workspace-activity-report** (отчёт по запросу из журнала + git).

## Мультиагентная система (MAS)

**MAS** — сокращение для каталога **`multi-agent-system/`** (Multi-Agent System).

В проект добавлен комплект для локальной мультиагентной разработки варианта B:

- `multi-agent-system/agents/` — промпты оркестратора и всех специализированных ролей
- `multi-agent-system/` — рабочая зона артефактов, шаблоны и инструкции (включая папку `agents/`)
- Завершённый прогон **обязательно** архивируется (workspace + копия в Obsidian) — см. `multi-agent-system/runbooks/mas-archive-policy.md`

Точка входа:

- `multi-agent-system/runbooks/how-to-run-project-through-multi-agent-system.md`
- `multi-agent-system/runbooks/operator-guide.md`
- `multi-agent-system/runbooks/orchestrator-start-prompt.md`
- `multi-agent-system/runbooks/prerequisites.md`
