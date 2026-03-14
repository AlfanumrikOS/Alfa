# Alfanumrik Database Schema Breakdown (MVP -> Scale)

This schema guide defines table ownership, primary relations, and indexing strategy.
For MVP, keep a **single PostgreSQL cluster** with clear service ownership boundaries.

## 1) Global design rules

- PostgreSQL is transactional source of truth.
- `pgvector` is used for semantic retrieval in same database.
- Every table has `id`, `created_at`, `updated_at`, and optional `deleted_at` for soft-delete where needed.
- Use UUID PKs for cross-service merge safety.
- Use explicit foreign keys for transactional integrity.

---

## 2) Identity & Access module

### `organizations`
- `id`, `name`, `type`, `plan_tier`, `status`

### `users`
- `id`, `organization_id`, `email`, `phone`, `password_hash`, `status`

### `user_roles`
- `id`, `user_id`, `role` (`student|teacher|parent|admin`), `scope_json`

### `student_guardians`
- `id`, `student_user_id`, `guardian_user_id`, `relation_type`

### `teacher_sections`
- `id`, `teacher_user_id`, `grade_id`, `subject_id`, `section_code`

### `subscriptions`
- `id`, `organization_id`, `plan_name`, `premium_quota`, `renewal_at`

**Indexes**
- `users(email)` unique
- `users(organization_id)`
- `user_roles(user_id, role)`

---

## 3) Learning Core module

### Curriculum spine
- `boards(id, code, name)`
- `grades(id, board_id, name, sort_order)`
- `subjects(id, grade_id, name)`
- `chapters(id, subject_id, name, sequence_no)`
- `concepts(id, chapter_id, name, difficulty_band)`
- `concept_edges(id, from_concept_id, to_concept_id, edge_type)`
- `misconceptions(id, concept_id, code, description)`

### Learner state
- `learner_profiles(id, student_user_id, language_pref, pace_band, confidence_band)`
- `learner_preferences(id, learner_profile_id, ui_mode, hint_mode, session_minutes)`
- `student_mastery(id, student_user_id, concept_id, mastery_score, last_evaluated_at)`
- `concept_attempt_stats(id, student_user_id, concept_id, attempts, accuracy_pct, avg_time_sec)`
- `error_patterns(id, student_user_id, concept_id, pattern, frequency)`
- `engagement_metrics(id, student_user_id, period_start, period_end, active_days, total_minutes)`

**Indexes**
- `concepts(chapter_id)`
- `concept_edges(from_concept_id)`, `concept_edges(to_concept_id)`
- `student_mastery(student_user_id, concept_id)` unique
- `concept_attempt_stats(student_user_id, concept_id)` unique

---

## 4) Content module

### `content_assets`
- `id`, `organization_id`, `content_type`, `title`, `board_id`, `grade_id`, `subject_id`, `chapter_id`, `status`

### `content_versions`
- `id`, `content_asset_id`, `version_no`, `body_markdown`, `quality_score`, `published_at`

### `content_concept_map`
- `id`, `content_asset_id`, `concept_id`, `relevance_weight`

### `content_language_variants`
- `id`, `content_asset_id`, `language_code`, `translated_version_id`

### `content_review_flags`
- `id`, `content_asset_id`, `flag_type`, `severity`, `status`, `reviewed_by`

**Indexes**
- `content_assets(board_id, grade_id, subject_id, chapter_id)`
- `content_concept_map(concept_id, content_asset_id)`
- `content_language_variants(content_asset_id, language_code)` unique

---

## 5) Assessment core module

### `assessments`
- `id`, `organization_id`, `assessment_type`, `title`, `grade_id`, `subject_id`, `assigned_by`, `scheduled_at`

### `assessment_items`
- `id`, `assessment_id`, `question_id`, `sort_order`, `marks`

### `question_bank`
- `id`, `source_type`, `question_type`, `difficulty_band`, `body`, `answer_key`

### `question_options`
- `id`, `question_id`, `option_text`, `is_correct`

### `student_attempts`
- `id`, `assessment_id`, `student_user_id`, `started_at`, `submitted_at`, `score`, `max_score`

### `attempt_answers`
- `id`, `attempt_id`, `question_id`, `answer_payload`, `is_correct`, `awarded_marks`, `time_spent_sec`

### `rubric_scores`
- `id`, `attempt_answer_id`, `criterion`, `score`, `feedback`

### `assessment_reports`
- `id`, `attempt_id`, `summary_json`, `weak_concepts_json`

**Indexes**
- `assessment_items(assessment_id, sort_order)`
- `student_attempts(student_user_id, assessment_id)`
- `attempt_answers(attempt_id, question_id)` unique

---

## 6) Retrieval + AI orchestration module

### Retrieval embeddings (pgvector)

### `retrieval_chunks`
- `id`, `content_asset_id`, `concept_id`, `language_code`, `chunk_text`, `embedding vector`, `metadata_json`

### AI control-plane
- `ai_requests(id, user_id, task_type, prompt_tokens, completion_tokens, status)`
- `ai_route_decisions(id, ai_request_id, lane, reason, policy_version)`
- `prompt_templates(id, template_key, template_body, version_no, active)`
- `model_usage_logs(id, ai_request_id, provider, model, latency_ms, cost_micro_usd)`
- `response_quality_flags(id, ai_request_id, flag_type, severity, resolved)`

**Indexes**
- `retrieval_chunks USING ivfflat (embedding vector_cosine_ops)`
- `retrieval_chunks(concept_id, language_code)`
- `ai_requests(user_id, created_at)`
- `ai_route_decisions(ai_request_id)` unique

---

## 7) Platform ops module

### Notifications
- `notification_events(id, user_id, channel, template_key, payload_json, status, scheduled_at, sent_at)`

### Files
- `file_assets(id, owner_user_id, org_id, storage_key, mime_type, size_bytes, checksum, visibility)`

### Background jobs
- `job_runs(id, job_type, status, started_at, finished_at, metrics_json, error_text)`

### Audit & observability
- `audit_logs(id, actor_user_id, action, resource_type, resource_id, ip, user_agent, payload_json)`
- `service_request_logs(id, trace_id, service_name, endpoint, status_code, latency_ms)`

**Indexes**
- `notification_events(user_id, status, scheduled_at)`
- `file_assets(owner_user_id, created_at)`
- `audit_logs(actor_user_id, created_at)`
- `service_request_logs(trace_id)`

---

## 8) High-value relationships (must enforce)

- `users.organization_id -> organizations.id`
- `grades.board_id -> boards.id`
- `subjects.grade_id -> grades.id`
- `chapters.subject_id -> subjects.id`
- `concepts.chapter_id -> chapters.id`
- `student_mastery.student_user_id -> users.id`
- `student_mastery.concept_id -> concepts.id`
- `content_concept_map.content_asset_id -> content_assets.id`
- `content_concept_map.concept_id -> concepts.id`
- `student_attempts.assessment_id -> assessments.id`
- `attempt_answers.attempt_id -> student_attempts.id`
- `ai_route_decisions.ai_request_id -> ai_requests.id`

---

## 9) Partitioning and scaling triggers

- Partition `service_request_logs`, `audit_logs`, `model_usage_logs` by month when >50M rows.
- Partition `attempt_answers` by academic year when write throughput grows.
- Move analytics-heavy workloads to warehouse only after query pressure justifies it.

---

## 10) MVP migration strategy

1. Keep one Postgres DB with schema namespaces per module (e.g., `auth`, `learning`, `assessment`, `ai`, `ops`).
2. Enforce ownership by code boundaries before splitting infra.
3. Introduce read replicas for analytics/reporting before moving to separate stores.
4. Keep retrieval in pgvector until latency/scale clearly justify dedicated vector infrastructure.


## 11) Executable reference schema

Use `architecture/retrieval-learning-graph-learner-schema.sql` as the concrete DDL baseline for Retrieval + Learning Graph + Learner State integration.
