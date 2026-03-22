# Stage Transition Rules

## Общие правила перехода

Переход на следующий этап допускается только если:

- создан обязательный артефакт текущего этапа;
- нет незакрытых `BLOCKING`-замечаний;
- `status.md` обновлен;
- пользователь подтвердил текущий крупный этап.

## Переходы

### Analysis -> TZ Review

- нужен `technical_specification.md`;
- блокирующие вопросы отсутствуют или закрыты.

### TZ Review -> Architecture

- `tz_review.md` не содержит нерешенных `BLOCKING`-замечаний;
- ТЗ доработано при необходимости.

### Architecture -> Architecture Review

- создан `architecture.md`;
- блокирующие вопросы отсутствуют или закрыты.

### Architecture Review -> Planning

- `architecture_review.md` не содержит нерешенных `BLOCKING`-замечаний.

### Planning -> Plan Review

- создан `plan.md`;
- есть task-файлы в `current-run/tasks/`.

### Plan Review -> Development

- `plan_review.md` не содержит нерешенных `BLOCKING`-замечаний.

### Development -> Code Review

- есть измененный код;
- есть тестовый отчет в `current-run/reports/`.

### Code Review -> Next Task Or Finish

- нет нерешенных критичных замечаний;
- задача подтверждена пользователем или возвращена в разработку по правилам
  review-итераций.
