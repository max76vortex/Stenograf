# Technical Specification

## Title

Dry Run: Service status surface for multi-agent process

## Objective

Implement a lightweight service page or command that displays:
- current system status;
- presence of open blocking questions;
- latest generated artifacts of the active run.

The solution must validate the dry-run process end-to-end without introducing heavy infrastructure.

## Scope

### In Scope

- Read and show data from:
  - `multi-agent-system/status.md`
  - `multi-agent-system/current-run/open_questions.md`
  - `multi-agent-system/current-run/` (artifacts list)
- Provide one user-facing entry point:
  - either a dedicated service page in the existing project context, or
  - a lightweight command/script for terminal usage.
- Keep output readable and stable for dry-run validation.

### Out of Scope

- New external services or databases.
- Major refactoring of existing `n8n`-related infrastructure.
- Heavy orchestration platform changes outside current dry-run boundaries.

## Inputs and Source of Truth

- Task brief: `multi-agent-system/current-run/task_brief.md`
- Project context: `multi-agent-system/current-run/project_context.md`
- Global process status: `multi-agent-system/status.md`
- Run-level questions and artifacts: `multi-agent-system/current-run/`

## Functional Requirements

1. Status view must include:
   - global process status (`IN_PROGRESS`, `BLOCKED`, etc.);
   - current stage and iteration;
   - next expected step;
   - user-confirmed stages list.
2. Blocking questions view must clearly show:
   - whether blockers exist;
   - blocker list (if present) from `open_questions.md`.
3. Artifacts view must show latest created artifacts for active run:
   - at minimum: key files from current run and recent task/review/report artifacts.
4. Output must remain usable even if some optional files are missing.

## Non-Functional Requirements

- No breaking changes for current `n8n` setup.
- Minimal dependencies (prefer built-in tools/stack already in repo).
- Fast local execution and easy manual verification.
- Implementation stays inside current repository boundaries, preferably under `multi-agent-system/`.

## Constraints

- Do not break existing infrastructure.
- Do not introduce heavy new infrastructure.
- Reuse existing contour under `multi-agent-system/`.
- Assume Cursor CLI binaries are unavailable in `PATH` unless explicitly provided.

## Acceptance Criteria

- User can run one command or open one page and get:
  - current process status;
  - blocker presence/details;
  - list of latest active-run artifacts.
- Data is sourced from current markdown artifacts, not hardcoded.
- Existing workflows continue to work unchanged.
- Output is understandable enough to support stage confirmation flow in dry run.

## Risks and Mitigations

- Risk: inconsistent markdown formats in source files.
  - Mitigation: implement tolerant parsing with safe fallbacks.
- Risk: ambiguity in "latest artifacts" definition.
  - Mitigation: in planning phase, define deterministic selection rule (e.g., by file modified time or explicit sections).

## Open Questions

- No blocking questions identified at analysis stage.

## Handover to TZ Review

Reviewer should validate:
- completeness of requirements against task brief;
- consistency with project constraints;
- feasibility of minimal implementation approach for dry run.
