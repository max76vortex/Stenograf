# Agents

**Расположение в репозитории:** `multi-agent-system/agents/` (вместе с оркестратором и `current-run/`).

Локальный комплект промптов для мультиагентной разработки по схеме `rdudov/agents`,
адаптированный под этот workspace и работу через Cursor CLI.

## Роли

- `01_orchestrator.md` — оркестратор процесса.
- `02_analyst_prompt.md` — аналитик.
- `03_tz_reviewer_prompt.md` — ревьюер ТЗ.
- `04_architect_prompt.md` — архитектор.
- `05_architecture_reviewer_prompt.md` — ревьюер архитектуры.
- `06_agent_planner.md` — планировщик.
- `07_agent_plan_reviewer.md` — ревьюер плана.
- `08_agent_developer.md` — разработчик.
- `09_agent_code_reviewer.md` — ревьюер кода.

## Базовая модель маршрутизации

- Аналитик, архитектор, планировщик: более сильная модель.
- Ревьюеры и разработчик: быстрая рабочая модель.

Конкретное имя модели можно:
- задавать вручную при запуске;
- или запускать автономно по профилю из `multi-agent-system/config/model-profiles.json`.

### Профиль по умолчанию для нового автономного run

`default-quality`:

```yaml
orchestrator: gpt-5.5-high
analyst: gemini-3.1-pro
tz_reviewer: grok-4-20-thinking
architect: gpt-5.5-xhigh
architecture_reviewer: grok-4-20-thinking
planner: gemini-3.1-pro
plan_reviewer: gpt-5.5-high
developer: gpt-5.3-codex-high
code_reviewer: gpt-5.3-codex-xhigh
```

## Где лежат артефакты

Все активные артефакты задачи хранятся в `multi-agent-system/current-run/`.

Ключевые файлы:

- `multi-agent-system/status.md`
- `multi-agent-system/current-run/technical_specification.md`
- `multi-agent-system/current-run/tz_review.md`
- `multi-agent-system/current-run/architecture.md`
- `multi-agent-system/current-run/architecture_review.md`
- `multi-agent-system/current-run/plan.md`
- `multi-agent-system/current-run/plan_review.md`
- `multi-agent-system/current-run/open_questions.md`
- `multi-agent-system/current-run/tasks/`
- `multi-agent-system/current-run/reviews/`
- `multi-agent-system/current-run/reports/`

## Общий принцип

1. Оркестратор получает постановку задачи.
2. Оркестратор запускает следующего нужного агента через Cursor CLI.
3. Каждый агент пишет или обновляет только свои артефакты.
4. После каждого этапа оркестратор обновляет `multi-agent-system/status.md`.
5. При блокирующих вопросах процесс останавливается до ответа пользователя.
