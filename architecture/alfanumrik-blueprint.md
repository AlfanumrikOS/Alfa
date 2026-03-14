# Alfanumrik Architecture Blueprint (Cost-Disciplined Learning OS)

## 1) System diagram

```mermaid
flowchart TD
    U[Frontend Apps\nStudent / Teacher / Parent / Admin\nNext.js web first, mobile later]
    CF[Cloudflare\nCDN + DNS + SSL + Security]
    API[API Gateway / Backend]

    subgraph CORE[Core Services]
      AUTH[Auth & User Service]
      LG[Learning Graph Service]
      ASM[Assessment Service]
      RET[Retrieval Service]
      ORCH[AI Orchestrator / Model Router]
      AN[Analytics Service]
      NOTIF[Notification Service]
      RULES[Rules Engine]
      WORK[Background Workers]
    end

    subgraph DATA[Data Layer]
      PG[(PostgreSQL)]
      VEC[(pgvector)]
      REDIS[(Redis cache + queue)]
      OBJ[(S3 / Cloudflare R2)]
    end

    U --> CF --> API
    API --> AUTH
    API --> LG
    API --> ASM
    API --> RET
    API --> ORCH
    API --> AN
    API --> NOTIF
    API --> RULES
    API --> WORK

    AUTH --> PG
    LG --> PG
    ASM --> PG
    RET --> PG
    RET --> VEC
    ORCH --> REDIS
    AN --> PG
    NOTIF --> REDIS
    WORK --> REDIS
    WORK --> OBJ
    API --> OBJ
```

## 2) Block responsibilities

- **Frontend Apps**: workflow-first UX for doubt solving, practice, reporting, and interventions (not generic chat).
- **Cloudflare**: edge security, TLS termination, caching, WAF/bot controls.
- **API Gateway/Backend**: request entrypoint, auth boundary, orchestration hub.
- **Auth & User**: users, institutions, roles, permissions.
- **Learning Graph**: concept DAG, dependencies, mastery state, weak-node detection.
- **Assessment**: attempt lifecycle, scoring, rubric logic, question performance.
- **Retrieval**: fetch minimal relevant concept/rubric/example slices.
- **AI Orchestrator**: chooses no/cheap/premium lane and enforces token budgets.
- **Analytics**: cohort and institution KPIs.
- **Notification**: reminders and intervention nudges.
- **Rules Engine**: deterministic gate to prevent unnecessary LLM calls.
- **Workers**: nightly/offline generation and heavy background tasks.

## 3) Execution policy (hard rule)

Every request follows this order:

1. **Can deterministic code solve it?**
2. **Can retrieval + templates solve it?**
3. **Can cheap model solve it?**
4. **Use premium model only as fallback.**

## 4) Three execution lanes

- **No-model lane**: scoring, mastery %, threshold recommendations, scheduling, dashboards.
- **Cheap-model lane**: translation, summarization, MCQ drafts, short explanations, tagging.
- **Premium lane**: hard reasoning, deep tutoring, content QA, complex doubt adjudication.

## 5) Learning request flow diagram (next critical operational diagram)

```mermaid
flowchart TD
    A[User action\nDoubt / Practice / Report] --> B[API request received]
    B --> C[Rules Engine\nuser-role + board/class/chapter + task policy]
    C --> D{Deterministic possible?}
    D -- Yes --> E[Execute deterministic logic]
    D -- No --> F[Retrieval Service\nconcept node + mastery + prior mistakes]
    F --> G{Retrieval/template enough?}
    G -- Yes --> H[Compose retrieval-backed response]
    G -- No --> I[Router chooses model lane]

    I --> J{Lane}
    J -->|Cheap| K[Cheap model inference]
    J -->|Premium fallback| L[Premium model inference]

    K --> M[Response Composer\nlength caps + safe schema]
    L --> M
    E --> N[Mastery + attempt state update]
    H --> N
    M --> N
    N --> O[Persist analytics + next action]
    O --> P[Return response to frontend]
```

## 6) Cost controls to enforce in code

- Context minimization: send only concept node + student state + active task.
- Prompt caching for stable system blocks and rubric templates.
- Strict response schemas and output caps per task.
- Nightly batch generation for reusable assets (reports, hints, summaries).
- Route telemetry: track premium-lane percentage and set alert thresholds.


## 7) Reference docs

- Service ownership and responsibilities: `architecture/service-breakdown.md`
- Database ownership and schema design: `architecture/database-schema-breakdown.md`
- Retrieval design and context-packet contract: `architecture/retrieval-architecture.md`
- Mastery update formulas and scheduling policy: `architecture/mastery-update-engine.md`
- Executable SQL schema for retrieval+graph+learner state: `architecture/retrieval-learning-graph-learner-schema.sql`
