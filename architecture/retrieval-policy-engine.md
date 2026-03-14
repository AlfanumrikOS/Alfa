# Alfanumrik Retrieval Policy Engine

This policy layer chooses **how retrieval packets are used** for each request.
It sits between learner state and response composition.

## Inputs

- `task_type`
- learner state: `mastery_score`, `retention_score`, `struggle_score`, repeated misconception flag
- prior mistake signals

## Output

- `recommended_response_mode`

## Core policies

- `teacher_report` -> `analytics_summary_with_intervention_actions`
- low mastery / high struggle / repeated misconception -> `prerequisite_recap_then_bridge_example_then_guided_hint`
- high mastery + high retention + low struggle -> `concise_explanation_then_challenge_check`
- low retention -> `revision_recall_then_targeted_example`
- fallback -> `simple_explanation_then_guided_question`

## Why this exists

It keeps retrieval behavior deterministic and auditable:
- same state -> same retrieval mode
- easy to tune by board/grade/product surface
- avoids ad-hoc prompt behavior

## Implementation

Current implementation lives in `apps/api/app/retrieval_policy.py` and is used by `apps/api/app/retrieval.py` when building the retrieval packet.
