# Alfanumrik Mastery Update Engine (Deterministic v1)

This document defines deterministic update logic for the core learning unit:

**`student_id + concept_id`**

The objective is stable, auditable mastery progression that improves retrieval precision and routing decisions.

## 1) Inputs

For each attempt (or guided interaction), compute update signals from:
- `outcome_score` (0-100)
- `used_hint` (boolean)
- `response_time_seconds`
- `expected_time_seconds`
- `error_severity` (0-10 scale)
- optional `confidence_self_reported` (0-100)

Current state comes from `student_mastery`.

## 2) Derived signals

- `speed_score`: normalized from expected-vs-actual time
- `mastery_signal`: outcome penalized for hint dependence and severe errors
- `confidence_signal`: self-report (if present) else outcome+speed blend
- `retention_signal`: weighted blend of outcome and confidence
- `struggle_signal`: inverse mastery plus penalties

## 3) Update formula

Use EMA (exponential moving average):

```text
new_value = alpha * signal + (1 - alpha) * previous_value
```

Recommended alphas in v1:
- mastery: `0.32`
- confidence: `0.28`
- retention: `0.18`
- struggle: `0.30`

All values are clamped to `[0, 100]`.

## 4) State label policy

- `mastered`: mastery >= 80 and struggle <= 30
- `learning`: mastery >= 60 and struggle <= 45
- `struggling`: mastery < 40 or struggle >= 70
- `needs_revision`: otherwise

## 5) Next review scheduling

Spaced-review schedule from current state:
- 14 days: mastery >= 85 and struggle < 25
- 7 days: mastery >= 70 and struggle < 40
- 3 days: mastery >= 50
- 1 day: otherwise

## 6) Why this works for MVP

- deterministic and explainable
- easy to tune by board/grade/cohort
- robust against noisy one-off attempts
- aligns with retrieval (same concept-linked unit)

## 7) Implementation in repository

The current deterministic engine lives in:
- `apps/api/app/mastery.py`

With tests in:
- `apps/api/tests/test_mastery.py`

This module returns:
- updated mastery snapshot
- `state_label`
- `next_review_at`

for each concept-level attempt signal.
