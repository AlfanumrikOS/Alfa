# Alfanumrik Service-by-Service Breakdown

This document defines what each logical service owns, stores, and exposes.
The key principle is **clear ownership with minimal coupling**: services can share a codebase in MVP, but contracts and data boundaries should remain explicit.

## 1) API Gateway / Backend Entry Layer

**Responsibilities**
- Accept web/mobile requests
- Validate session/auth context
- Apply rate limits and request tracing
- Route to internal modules
- Return unified response envelopes

**Owns**
- API contracts, DTO validation, request correlation IDs

**Inputs**
- Client payload + auth token

**Outputs**
- Structured JSON responses
- Internal service calls/events

---

## 2) Auth & User Service

**Responsibilities**
- Identity, sessions, role-based access
- Organization tenancy mapping
- Student-teacher-parent-admin relationship mapping
- Plan/subscription checks

**Owns tables**
- `users`, `organizations`, `user_roles`, `student_guardians`, `teacher_sections`, `subscriptions`

---

## 3) Learning Graph Service

**Responsibilities**
- Maintain board->grade->subject->chapter->concept graph
- Dependency edges and prerequisite reasoning
- Mastery state and weak-node detection
- Next-best-step recommendations

**Owns tables**
- `boards`, `grades`, `subjects`, `chapters`, `concepts`, `concept_edges`, `misconceptions`, `student_mastery`, `concept_attempt_stats`

**Design rule**
- Graph and progression logic stays deterministic; LLM may enrich metadata but is not source of truth.

---

## 4) Curriculum & Content Service

**Responsibilities**
- Structured syllabus-aligned content lifecycle
- Versioning, review, language variants, publishing status
- Mapping assets to concept nodes

**Owns tables**
- `content_assets`, `content_versions`, `content_concept_map`, `content_language_variants`, `content_review_flags`

---

## 5) Assessment Service

**Responsibilities**
- Assessment assignment/execution lifecycle
- Objective scoring + rubric support
- Attempt telemetry (accuracy, time, consistency)
- Mastery feedback to Learning Graph

**Owns tables**
- `assessments`, `assessment_items`, `question_bank`, `question_options`, `student_attempts`, `attempt_answers`, `rubric_scores`, `assessment_reports`

---

## 6) Question Bank & Practice Generation Service

**Responsibilities**
- Question inventory + concept/difficulty taxonomy
- Balanced adaptive practice set generation
- Reuse-quality tracking

**Owns tables**
- `questions`, `question_tags`, `question_concept_map`, `question_difficulty_profiles`, `practice_set_history`

---

## 7) Retrieval Service

**Responsibilities**
- Build minimal context packets for the AI layer
- Semantic + metadata retrieval across content/question history
- Fetch learner-specific error traces

**Storage pattern**
- Vector index in `pgvector`
- Metadata filters from PostgreSQL tables

**Internal modules**
- Query parser
- Concept resolver
- Candidate fetcher
- Ranker
- Context builder
- Retrieval logger

**Must retrieve**
- Relevant concept fragment
- One or few targeted examples
- Latest error patterns
- Learner level + board/language context

---

## 8) AI Orchestrator / Model Router

**Responsibilities**
- Task classification + policy-driven route decision
- Lane selection (`no_model`, `cheap`, `premium`)
- Prompt/context assembly, token caps, output validation
- Usage and quality logging

**Owns tables**
- `ai_requests`, `ai_route_decisions`, `prompt_templates`, `model_usage_logs`, `response_quality_flags`

**Internal components**
- Task classifier
- Policy engine
- Prompt builder
- Model adapters
- Output validator + fallback logic

---

## 9) Rules Engine

**Responsibilities**
- Deterministic business and pedagogy rules
- Escalation policy and guardrails before model invocation

**Example policies**
- mastery < 40% -> remedial path
- repeated errors in concept cluster -> teacher alert
- free plan -> premium lane cap

---

## 10) Student State / Learner Profile Service

**Responsibilities**
- Dynamic learner profile and progression state
- Preferences, velocity, confidence, fatigue, engagement

**Owns tables**
- `learner_profiles`, `learner_preferences`, `learner_state_snapshots`, `error_patterns`, `engagement_metrics`

---

## 11) Teacher Copilot Service

**Responsibilities**
- Worksheet generation, class weakness summaries
- Intervention grouping, lesson emphasis suggestions
- Parent communication drafts

---

## 12) Parent Insight Service

**Responsibilities**
- Parent-facing progress narratives and suggestions
- Clear, simplified communication of strengths/weaknesses

---

## 13) Analytics & Reporting Service

**Responsibilities**
- Dashboards for student/teacher/admin views
- Cohort/institution KPIs and intervention outcomes
- AI cost-efficiency analytics

**Storage**
- Postgres aggregates/materialized views initially
- Move to analytical store only when scale demands

---

## 14) Notification Service

**Responsibilities**
- Event-driven reminders/alerts over email/SMS/WhatsApp/push

**Guideline**
- Centralized sender service; other services emit events instead of sending directly.

---

## 15) Background Workers / Job Service

**Responsibilities**
- Nightly reports, indexing, embeddings, translations, batch generation

**Tools (MVP choices)**
- Celery/Dramatiq/BullMQ + Redis queue

---

## 16) Search & Indexing Service

**Responsibilities**
- Hybrid search (semantic + keyword + strict filters)
- Reindex workflows on content updates

---

## 17) File / Asset Service

**Responsibilities**
- Upload/store/access files and generated exports
- Signed URLs, metadata, versioning

**Storage**
- S3/Cloudflare R2

---

## 18) Observability & Audit Service

**Responsibilities**
- Request tracing, latency and error monitoring
- Model cost and route telemetry
- Security and admin audit trails

---

## Recommended ownership map

### Core transactional
- Auth & User
- Learning Graph
- Curriculum & Content
- Assessment
- Learner Profile

### Intelligence
- Retrieval
- Rules Engine
- AI Orchestrator
- Teacher Copilot
- Parent Insight

### Operational
- Analytics & Reporting
- Notification
- Background Jobs
- File/Asset
- Observability & Audit

---

## MVP deployment grouping (3-5 modules, not microservice theater)

1. **Identity & Access**: Auth + roles + organization
2. **Learning Core**: curriculum + content + learning graph + learner profile
3. **Assessment Core**: question bank + assessments + attempts + scoring
4. **Intelligence Layer**: retrieval + rules + AI router + teacher/parent insights
5. **Platform Ops**: analytics + notifications + files + background jobs + audit

---

## Critical interaction flows

### Student doubt flow
1. API receives request
2. Auth validates actor/tenant
3. Learner profile fetched
4. Learning graph resolves concept node and prerequisites
5. Retrieval gathers compact context
6. Rules engine checks deterministic/retrieval-only path
7. Orchestrator chooses lane
8. Response returned
9. Learner state + analytics updated

### Teacher worksheet flow
1. API receives request
2. Teacher scope validated
3. Assessment/class stats fetched
4. Learning graph identifies weak concept clusters
5. Question bank selects/drafts balanced set
6. Orchestrator improves language if needed
7. File service exports worksheet
8. Notification service sends completion event
