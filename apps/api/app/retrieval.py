from dataclasses import asdict

from app.schemas import (
    OrchestrationRequest,
    RetrievalAsset,
    RetrievalCandidate,
    RetrievalPacket,
    TaskType,
)


CONTENT_TYPE_BY_TASK = {
    TaskType.TUTOR_HINT: {"worked_example", "misconception_note", "hint"},
    TaskType.CONCEPT_EXPLANATION: {"explanation", "worked_example"},
    TaskType.QUESTION_DRAFT: {"worked_example", "question_template"},
    TaskType.SUMMARIZATION: {"summary", "explanation"},
    TaskType.TRANSLATION: {"explanation", "summary"},
    TaskType.TEACHER_REPORT: {"analytics_note", "remediation_hint"},
    TaskType.HARD_REASONING: {"explanation", "worked_example", "misconception_note"},
    TaskType.LESSON_PLANNING: {"lesson_outline", "worked_example", "remediation_hint"},
}


def parse_query(request: OrchestrationRequest) -> dict:
    return {
        "task_type": request.task_type.value,
        "subject": request.subject,
        "chapter": request.chapter,
        "concept": request.concept,
        "language": request.language,
        "difficulty": request.student_level,
        "user_role": request.user_type.value,
    }


def resolve_concept_graph(request: OrchestrationRequest) -> dict:
    concept_slug = request.concept.lower().replace(" ", "_")
    return {
        "concept_id": f"{request.subject.lower()}_{concept_slug}",
        "prerequisites": [
            f"{request.subject.lower()}_foundation",
            f"{request.subject.lower()}_{request.chapter.lower().replace(' ', '_')}",
        ],
        "misconceptions": request.prior_mistakes[:2],
    }


def metadata_filter(request: OrchestrationRequest) -> dict:
    allowed_types = sorted(CONTENT_TYPE_BY_TASK.get(request.task_type, {"explanation"}))
    return {
        "board": request.board,
        "grade": request.grade,
        "subject": request.subject,
        "chapter": request.chapter,
        "language": request.language,
        "content_types": allowed_types,
    }


def fetch_candidates(request: OrchestrationRequest, graph_context: dict, filters: dict) -> list[RetrievalCandidate]:
    concept_id = graph_context["concept_id"]
    assets = [
        RetrievalCandidate(
            asset_id=f"exp_{concept_id}",
            asset_type="explanation",
            summary=f"Core explanation for {request.concept} aligned to {request.board} grade {request.grade}.",
            semantic_similarity=0.91,
            concept_match=1.0,
            learner_fit=0.82,
            language_match=1.0,
            quality_score=0.88,
            misconception_relevance=0.75,
        ),
        RetrievalCandidate(
            asset_id=f"wk_{concept_id}",
            asset_type="worked_example",
            summary=f"Step-by-step worked example for {request.concept} with {request.student_level} scaffolding.",
            semantic_similarity=0.87,
            concept_match=0.95,
            learner_fit=0.90,
            language_match=1.0,
            quality_score=0.85,
            misconception_relevance=0.86,
        ),
        RetrievalCandidate(
            asset_id=f"mis_{concept_id}",
            asset_type="misconception_note",
            summary=(
                "Misconception guardrail: "
                + (request.prior_mistakes[0] if request.prior_mistakes else "common conceptual confusion")
            ),
            semantic_similarity=0.84,
            concept_match=0.92,
            learner_fit=0.83,
            language_match=1.0,
            quality_score=0.81,
            misconception_relevance=0.97,
        ),
    ]
    return [asset for asset in assets if asset.asset_type in filters["content_types"] or asset.asset_type == "explanation"]


def rank_candidates(candidates: list[RetrievalCandidate]) -> list[RetrievalCandidate]:
    def score(candidate: RetrievalCandidate) -> float:
        return (
            0.35 * candidate.semantic_similarity
            + 0.20 * candidate.concept_match
            + 0.15 * candidate.learner_fit
            + 0.10 * candidate.language_match
            + 0.10 * candidate.quality_score
            + 0.10 * candidate.misconception_relevance
        )

    return sorted(candidates, key=score, reverse=True)


def build_context_packet(request: OrchestrationRequest) -> RetrievalPacket:
    parsed = parse_query(request)
    graph_context = resolve_concept_graph(request)
    filters = metadata_filter(request)
    ranked = rank_candidates(fetch_candidates(request, graph_context, filters))
    top_assets = ranked[:3]

    response_mode = "simple_explanation_then_guided_question"
    if request.task_type == TaskType.TUTOR_HINT:
        response_mode = "one_hint_then_check_understanding"
    elif request.task_type == TaskType.TEACHER_REPORT:
        response_mode = "analytics_summary_with_intervention_actions"

    assets = [
        RetrievalAsset(type=item.asset_type, id=item.asset_id, summary=item.summary)
        for item in top_assets
    ]

    return RetrievalPacket(
        task_type=request.task_type.value,
        concept=graph_context["concept_id"],
        prerequisites=graph_context["prerequisites"],
        learner_level=request.student_level,
        recent_errors=request.prior_mistakes[:2],
        metadata_filters=filters,
        retrieved_assets=assets,
        recommended_response_mode=response_mode,
        retrieval_debug={
            "query": parsed,
            "ranked_candidate_ids": [item.asset_id for item in ranked],
            "top_scores_preview": [
                {
                    "asset_id": item.asset_id,
                    "semantic_similarity": item.semantic_similarity,
                    "concept_match": item.concept_match,
                }
                for item in ranked[:3]
            ],
        },
    )


def packet_to_dict(packet: RetrievalPacket) -> dict:
    result = asdict(packet)
    result["retrieved_assets"] = [asdict(asset) for asset in packet.retrieved_assets]
    return result
