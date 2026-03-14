# Alfanumrik Retrieval Architecture

Retrieval in Alfanumrik is the quality-and-cost control layer between user requests and model routing.
Its job is to return the **smallest trusted context packet** grounded in curriculum, learning graph, learner state, and assessment history.

## Retrieval mission

For each learning request, retrieval must answer:
- What exact concept is being asked?
- What prerequisites and misconceptions apply?
- What does this learner already know or get wrong?
- Which board/grade/language variant is valid?
- What top 3-5 assets best support this task?

## Pipeline

```text
User request
  -> Query parser
  -> Concept resolver (learning graph grounded)
  -> Metadata filters (board/grade/subject/chapter/language/role)
  -> Semantic candidate retrieval (pgvector)
  -> Rule-based reranking
  -> Structured context packet builder
  -> AI Router or deterministic response engine
```

## Retrieval principles

1. Filter first, vector search second.
2. Retrieve pedagogical units, not arbitrary token windows.
3. Prefer 3-5 high-quality assets, never context dumping.
4. Keep retrieval and routing separate: retrieval fetches truth, router chooses cost lane.

## Chunking policy

Use chunk units such as:
- one concept explanation
- one worked example
- one misconception note
- one formula-with-usage card
- one question+solution pair

Avoid:
- page OCR blobs
- mixed-topic mega chunks
- entire textbook sections

## Reranking factors (MVP rule-based)

```text
Score =
0.35 semantic_similarity
+ 0.20 concept_match
+ 0.15 learner_fit
+ 0.10 language_match
+ 0.10 quality_score
+ 0.10 misconception_relevance
```

## Context packet schema (contract)

```json
{
  "task_type": "tutor_hint",
  "concept": "math_ratio_word_problems",
  "prerequisites": ["math_foundation", "math_ratio"],
  "learner_level": "basic",
  "recent_errors": ["unit comparison confusion"],
  "metadata_filters": {
    "board": "CBSE",
    "grade": "6",
    "subject": "Math",
    "chapter": "Ratio",
    "language": "en_hi"
  },
  "retrieved_assets": [
    {"type": "explanation", "id": "exp_...", "summary": "..."},
    {"type": "worked_example", "id": "wk_...", "summary": "..."}
  ],
  "recommended_response_mode": "one_hint_then_check_understanding"
}
```

## Retrieval modes

- Student doubt: concept + weak-pattern weighted explanation/example retrieval
- Hint generation: prerequisite-aware minimal next-step assets
- Practice generation: concept+difficulty constrained retrieval with seen-question suppression
- Teacher insight: class weakness clusters + intervention assets
- Parent report: learner trend summaries + plain-language support templates

## Data sources

Retrieval composes from four sources:
- curriculum/content repository
- learning graph relationships
- learner state profiles
- assessment evidence

## KPIs

- concept match rate
- top-1 and top-3 relevance
- follow-up confusion rate
- hint usefulness score
- time-to-correct-answer after hint
- retrieval-to-premium escalation rate

## Cost controls

- cache frequent concept packets
- precompute embeddings offline
- avoid retrieving more than needed
- instrument retrieval logs and monitor packet size

## Implementation status in this repository

Current orchestration pipeline includes:
- query parsing
- concept grounding
- metadata filters
- rule-based candidate ranking
- structured retrieval packet return in orchestration response

See `apps/api/app/retrieval.py` and `apps/api/app/services.py`.
