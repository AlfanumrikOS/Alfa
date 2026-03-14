-- Alfanumrik: Retrieval + Learning Graph + Learner State schema
-- PostgreSQL + pgvector

CREATE EXTENSION IF NOT EXISTS vector;

-- 1) Curriculum hierarchy
CREATE TABLE boards (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    country_code VARCHAR(10) DEFAULT 'IN',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE grades (
    id BIGSERIAL PRIMARY KEY,
    board_id BIGINT NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    ordinal SMALLINT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(board_id, code)
);

CREATE TABLE subjects (
    id BIGSERIAL PRIMARY KEY,
    board_id BIGINT NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(board_id, code)
);

CREATE TABLE chapters (
    id BIGSERIAL PRIMARY KEY,
    board_id BIGINT NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
    grade_id BIGINT NOT NULL REFERENCES grades(id) ON DELETE CASCADE,
    subject_id BIGINT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    code VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    sequence_no INT NOT NULL,
    difficulty_band VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(board_id, grade_id, subject_id, code)
);

-- 2) Learning graph
CREATE TABLE concepts (
    id BIGSERIAL PRIMARY KEY,
    chapter_id BIGINT NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    code VARCHAR(120) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    pedagogical_goal TEXT,
    difficulty_band VARCHAR(50),
    estimated_learning_minutes INT,
    is_core BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(chapter_id, code)
);

CREATE TABLE concept_edges (
    id BIGSERIAL PRIMARY KEY,
    from_concept_id BIGINT NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    to_concept_id BIGINT NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    edge_type VARCHAR(50) NOT NULL,
    weight NUMERIC(5,2) DEFAULT 1.00,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CHECK (from_concept_id <> to_concept_id)
);

CREATE INDEX idx_concept_edges_from ON concept_edges(from_concept_id);
CREATE INDEX idx_concept_edges_to ON concept_edges(to_concept_id);
CREATE INDEX idx_concept_edges_type ON concept_edges(edge_type);

CREATE TABLE misconceptions (
    id BIGSERIAL PRIMARY KEY,
    concept_id BIGINT NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    code VARCHAR(120) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    remediation_hint TEXT,
    severity_weight NUMERIC(5,2) DEFAULT 1.00,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(concept_id, code)
);

CREATE TABLE concept_misconception_map (
    concept_id BIGINT NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    misconception_id BIGINT NOT NULL REFERENCES misconceptions(id) ON DELETE CASCADE,
    relevance_weight NUMERIC(5,2) DEFAULT 1.00,
    PRIMARY KEY (concept_id, misconception_id)
);

-- 3) Content + retrieval indexing
CREATE TABLE content_assets (
    id BIGSERIAL PRIMARY KEY,
    board_id BIGINT NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
    grade_id BIGINT NOT NULL REFERENCES grades(id) ON DELETE CASCADE,
    subject_id BIGINT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    chapter_id BIGINT REFERENCES chapters(id) ON DELETE SET NULL,
    asset_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    language_code VARCHAR(20) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    source_ref TEXT,
    quality_score NUMERIC(5,2) DEFAULT 0,
    published BOOLEAN DEFAULT FALSE,
    version_no INT DEFAULT 1,
    created_by BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE content_chunks (
    id BIGSERIAL PRIMARY KEY,
    asset_id BIGINT NOT NULL REFERENCES content_assets(id) ON DELETE CASCADE,
    concept_id BIGINT REFERENCES concepts(id) ON DELETE SET NULL,
    misconception_id BIGINT REFERENCES misconceptions(id) ON DELETE SET NULL,
    pedagogical_role VARCHAR(50) NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_summary TEXT,
    difficulty_level VARCHAR(50),
    reading_level VARCHAR(50),
    language_code VARCHAR(20) NOT NULL,
    token_count INT,
    embedding VECTOR(1536),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_content_chunks_concept_id ON content_chunks(concept_id);
CREATE INDEX idx_content_chunks_misconception_id ON content_chunks(misconception_id);
CREATE INDEX idx_content_chunks_role ON content_chunks(pedagogical_role);
CREATE INDEX idx_content_chunks_language ON content_chunks(language_code);

CREATE INDEX idx_content_chunks_embedding
ON content_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE TABLE content_chunk_tags (
    chunk_id BIGINT NOT NULL REFERENCES content_chunks(id) ON DELETE CASCADE,
    tag_key VARCHAR(100) NOT NULL,
    tag_value VARCHAR(255) NOT NULL,
    PRIMARY KEY (chunk_id, tag_key, tag_value)
);

-- 4) Learner state
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(30),
    role VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE student_profiles (
    user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    board_id BIGINT NOT NULL REFERENCES boards(id),
    grade_id BIGINT NOT NULL REFERENCES grades(id),
    preferred_language_code VARCHAR(20) DEFAULT 'en',
    school_id BIGINT,
    current_academic_year VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE learner_preferences (
    student_id BIGINT PRIMARY KEY REFERENCES student_profiles(user_id) ON DELETE CASCADE,
    preferred_explanation_style VARCHAR(50),
    preferred_difficulty VARCHAR(50),
    preferred_response_language VARCHAR(20),
    prefers_bilingual BOOLEAN DEFAULT FALSE,
    hint_tolerance_level VARCHAR(50),
    pace_preference VARCHAR(50),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE student_mastery (
    student_id BIGINT NOT NULL REFERENCES student_profiles(user_id) ON DELETE CASCADE,
    concept_id BIGINT NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    mastery_score NUMERIC(5,2) NOT NULL DEFAULT 0.00,
    confidence_score NUMERIC(5,2) DEFAULT 0.00,
    retention_score NUMERIC(5,2) DEFAULT 0.00,
    struggle_score NUMERIC(5,2) DEFAULT 0.00,
    attempts_count INT DEFAULT 0,
    correct_attempts_count INT DEFAULT 0,
    last_attempt_at TIMESTAMPTZ,
    last_mastered_at TIMESTAMPTZ,
    next_review_at TIMESTAMPTZ,
    state_label VARCHAR(50) DEFAULT 'unknown',
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (student_id, concept_id)
);

CREATE INDEX idx_student_mastery_state_label ON student_mastery(state_label);
CREATE INDEX idx_student_mastery_next_review ON student_mastery(next_review_at);
CREATE INDEX idx_student_mastery_student ON student_mastery(student_id);

CREATE TABLE error_patterns (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES student_profiles(user_id) ON DELETE CASCADE,
    concept_id BIGINT NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    misconception_id BIGINT REFERENCES misconceptions(id) ON DELETE SET NULL,
    error_type VARCHAR(100) NOT NULL,
    description TEXT,
    frequency INT DEFAULT 1,
    severity_score NUMERIC(5,2) DEFAULT 1.00,
    first_observed_at TIMESTAMPTZ DEFAULT NOW(),
    last_observed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_error_patterns_student_concept ON error_patterns(student_id, concept_id);
CREATE INDEX idx_error_patterns_misconception ON error_patterns(misconception_id);

CREATE TABLE learning_events (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES student_profiles(user_id) ON DELETE CASCADE,
    concept_id BIGINT REFERENCES concepts(id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL,
    source_type VARCHAR(50),
    source_ref_id BIGINT,
    event_payload JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_learning_events_student_time ON learning_events(student_id, created_at DESC);

-- 5) Assessment-linked evidence
CREATE TABLE questions (
    id BIGSERIAL PRIMARY KEY,
    board_id BIGINT NOT NULL REFERENCES boards(id),
    grade_id BIGINT NOT NULL REFERENCES grades(id),
    subject_id BIGINT NOT NULL REFERENCES subjects(id),
    chapter_id BIGINT REFERENCES chapters(id),
    question_type VARCHAR(50) NOT NULL,
    difficulty_level VARCHAR(50),
    stem_text TEXT NOT NULL,
    solution_text TEXT,
    language_code VARCHAR(20) DEFAULT 'en',
    quality_score NUMERIC(5,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE question_concept_map (
    question_id BIGINT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    concept_id BIGINT NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    weight NUMERIC(5,2) DEFAULT 1.00,
    PRIMARY KEY (question_id, concept_id)
);

CREATE TABLE student_attempts (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES student_profiles(user_id) ON DELETE CASCADE,
    question_id BIGINT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    assessment_id BIGINT,
    answered_correctly BOOLEAN,
    score_awarded NUMERIC(6,2),
    max_score NUMERIC(6,2),
    response_text TEXT,
    response_payload JSONB DEFAULT '{}'::JSONB,
    attempt_duration_seconds INT,
    confidence_self_reported NUMERIC(5,2),
    attempted_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_student_attempts_student_time ON student_attempts(student_id, attempted_at DESC);

CREATE TABLE attempt_concept_outcomes (
    attempt_id BIGINT NOT NULL REFERENCES student_attempts(id) ON DELETE CASCADE,
    concept_id BIGINT NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    outcome_score NUMERIC(5,2) NOT NULL,
    error_type VARCHAR(100),
    misconception_id BIGINT REFERENCES misconceptions(id) ON DELETE SET NULL,
    PRIMARY KEY (attempt_id, concept_id)
);

-- 6) Retrieval logs and evaluation
CREATE TABLE retrieval_requests (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT REFERENCES student_profiles(user_id) ON DELETE SET NULL,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    task_type VARCHAR(50) NOT NULL,
    query_text TEXT NOT NULL,
    resolved_concept_id BIGINT REFERENCES concepts(id) ON DELETE SET NULL,
    language_code VARCHAR(20),
    request_context JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE retrieval_results (
    id BIGSERIAL PRIMARY KEY,
    retrieval_request_id BIGINT NOT NULL REFERENCES retrieval_requests(id) ON DELETE CASCADE,
    chunk_id BIGINT NOT NULL REFERENCES content_chunks(id) ON DELETE CASCADE,
    rank_position INT NOT NULL,
    semantic_score NUMERIC(8,4),
    graph_score NUMERIC(8,4),
    learner_fit_score NUMERIC(8,4),
    final_score NUMERIC(8,4),
    selected_for_context BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE retrieval_feedback (
    id BIGSERIAL PRIMARY KEY,
    retrieval_request_id BIGINT NOT NULL REFERENCES retrieval_requests(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    usefulness_score NUMERIC(5,2),
    confusion_after_response BOOLEAN,
    followup_needed BOOLEAN,
    teacher_accepted BOOLEAN,
    feedback_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7) Optimization layer
CREATE MATERIALIZED VIEW mv_student_concept_context AS
SELECT
    sm.student_id,
    sm.concept_id,
    sm.mastery_score,
    sm.confidence_score,
    sm.retention_score,
    sm.struggle_score,
    sm.state_label,
    ep.error_type,
    ep.frequency,
    ep.severity_score,
    lp.preferred_response_language,
    lp.preferred_explanation_style,
    lp.prefers_bilingual
FROM student_mastery sm
LEFT JOIN learner_preferences lp
    ON lp.student_id = sm.student_id
LEFT JOIN error_patterns ep
    ON ep.student_id = sm.student_id
   AND ep.concept_id = sm.concept_id;
