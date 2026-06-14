---
name: project-evolution
description: >-
  Guides iterative evolution of myAlgo2: read and update TASKS.md, advance PRD
  milestones, coordinate strategy and broker work, and keep AGENTS.md workflow
  consistent. Use when the user asks to plan next steps, update tasks, evolve
  the project, track milestones, or prioritize work.
---

# Project Evolution Skill — myAlgo2

## Session start checklist

1. Read [AGENTS.md](../../AGENTS.md)
2. Read [TASKS.md](../../TASKS.md) — focus on **Next** section
3. Identify task ID (e.g. `M2-3`) before coding
4. Load domain skill: `algo-strategy` or `futu-order-execution` as needed

## After completing work

```
- [ ] make check passes
- [ ] TASKS.md updated (⬜ → ✅, date in Changelog)
- [ ] PRD milestone checkbox if major deliverable
- [ ] README updated only if user-facing behavior changed
```

## Task lifecycle

| State | Meaning | Action |
|-------|---------|--------|
| ⬜ | Todo | Pick from **Next** when user ready |
| 🔄 | In progress | One agent session per task ID |
| ✅ | Done | Changelog entry |
| ⏸ | Blocked | Note blocker in TASKS.md |

## Milestone order

Do not skip: **M2 → M3 → M4 → M5** before Phase 2 (M6/M7).

## Adding features

1. Add row to TASKS.md with new ID
2. If architectural, add to PRD.md section 3
3. Implement with minimal scope
4. Add tests (ci-cd skill)
5. Update TASKS + Changelog

## Simulation vs CI

| Activity | Where |
|----------|-------|
| Unit tests | CI + local `make test` |
| OpenD simulation | Local only, user starts OpenD |
| Real trading | Local only, `--confirm` required |

## Prioritization rules

1. Unblock **Next** tasks first
2. Fix CI failures before new features
3. Strategy requests → algo-strategy skill, not broker
4. Broker bugs → futu-order-execution skill, not strategy

## Changelog format

In TASKS.md:

```markdown
| 2026-06-14 | M2-3: run_paper --once connects to OpenD |
```
