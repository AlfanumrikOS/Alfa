# Alfanumrik Mastery Update Engine (Rule-Based v1)

The core unit is **`student_id + concept_id`**.

This engine updates:
- mastery
- confidence
- retention
- struggle
- attempts/correct counts
- evidence and streak counters
- state labels
- next review schedule

## 1) Deterministic state functions

Implemented in `apps/api/app/mastery.py`:
- `derive_state_label(...)`
- `compute_next_review(...)`
- component scorers:
  - `score_correctness`
  - `score_hints`
  - `score_speed`
  - `score_misconception`
  - `score_confidence_alignment`
  - `score_difficulty`
  - `score_recency`
- `learning_rate(...)`
- `update_mastery(...)`
- `apply_daily_decay(...)`
- `apply_teacher_override(...)`

## 2) Update design

Per concept outcome, compute weighted deltas:

```text
mastery_delta =
  0.45 * correctness
+ 0.20 * difficulty
+ 0.15 * misconception
+ 0.10 * speed
+ 0.10 * recency

confidence_delta =
  0.35 * correctness
+ 0.25 * hints
+ 0.20 * speed
+ 0.20 * confidence_alignment

retention_delta =
  0.50 * recency
+ 0.30 * correctness
+ 0.20 * misconception
```

Struggle uses a separate friction model and decays slowly after successful evidence.

## 3) Learning-rate policy

- New concepts: higher LR
- Learning-zone concepts: medium LR
- High-mastery concepts: lower LR
- Formal tests amplify LR
- Heavy-hint tutor flows reduce LR

## 4) State labels (max 10)

- `unknown`
- `introduced`
- `learning`
- `improving`
- `functional`
- `mastered`
- `fragile_mastery`
- `struggling`
- `needs_revision`
- `forgotten`

## 5) Decay policy

Decay after grace periods:
- mastery < 50: no decay (already unstable)
- mastery 50-79: grace 10 days
- mastery >= 80: grace 14 days

After grace:
- retention: `-0.4/day`
- confidence: `-0.2/day`
- mastery: `-0.1/day` only if retention < 50

## 6) Teacher override policy

Bounded override events are supported:
- `needs_revision`
- `improved_with_support`
- `suppress_over_penalization`

These are controlled nudges, not unrestricted score edits.

## 7) API contracts to stabilize

Use a multi-concept input envelope (`concept_outcomes[]`) and concept-level updates in output. Keep this interface stable even if future ML weighting is introduced behind it.
