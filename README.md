# Alfanumrik Cost-Optimized AI Learning OS

Alfanumrik is designed as an **AI operating system for learning**, not a single chatbot.
The core strategy is strict cost discipline:

1. Deterministic logic first
2. Retrieval second
3. Cheap model third
4. Premium model last (fallback only)

## Architecture at a glance

- Workflow-first product experience (student, teacher, parent, institution)
- Learning graph + mastery state as moat
- Rules engine + router for no-model / cheap-model / premium-model decisions
- PostgreSQL as source of truth, pgvector for semantic retrieval, Redis for cache/queue

Detailed architecture docs are in:

- `architecture/alfanumrik-blueprint.md`
- `architecture/service-breakdown.md`
- `architecture/database-schema-breakdown.md`
- `architecture/retrieval-architecture.md`
- `architecture/retrieval-learning-graph-learner-schema.sql`
- `architecture/mastery-update-engine.md`
- `architecture/retrieval-policy-engine.md`

## Repository layout

```text
apps/
  api/
    app/
      main.py           # request entrypoints
      schemas.py        # request/response models
      router_policy.py  # task policy + lane mapping
      services.py       # rules + retrieval context + route decision
    tests/
      test_orchestrator.py
  web/
    README.md
```

## API module quick usage

```bash
cd apps/api
pytest -q
```

## What this starter enforces

- Small, structured context payloads
- Policy-driven routing decisions with reasons
- Token budget controls by lane
- Telemetry fields to monitor premium usage and routing behavior


## Recommended module boundaries (MVP deployables)

- Identity & Access
- Learning Core
- Assessment Core
- Intelligence Layer
- Platform Ops
