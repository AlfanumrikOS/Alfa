from app.retrieval import build_context_packet, rank_candidates
from app.schemas import OrchestrationRequest, RetrievalCandidate, TaskType, UserType


def _request(task_type: TaskType = TaskType.TUTOR_HINT) -> OrchestrationRequest:
    return OrchestrationRequest(
        task_type=task_type,
        user_type=UserType.STUDENT,
        board="CBSE",
        grade="6",
        subject="Math",
        chapter="Ratio",
        concept="Ratio word problems",
        student_level="basic",
        language="en_hi",
        prior_mistakes=["unit comparison confusion", "multi-step skip"],
        user_prompt="I don't understand ratio word problems",
    )


def test_retrieval_packet_is_structured_and_compact() -> None:
    packet = build_context_packet(_request())
    assert packet.task_type == "tutor_hint"
    assert packet.concept.startswith("math_")
    assert packet.metadata_filters["board"] == "CBSE"
    assert packet.metadata_filters["language"] == "en_hi"
    assert 1 <= len(packet.retrieved_assets) <= 3
    assert packet.recommended_response_mode == "one_hint_then_check_understanding"


def test_rank_candidates_orders_by_composite_score() -> None:
    candidates = [
        RetrievalCandidate(
            asset_id="low",
            asset_type="explanation",
            summary="low",
            semantic_similarity=0.6,
            concept_match=0.6,
            learner_fit=0.6,
            language_match=0.6,
            quality_score=0.6,
            misconception_relevance=0.6,
        ),
        RetrievalCandidate(
            asset_id="high",
            asset_type="worked_example",
            summary="high",
            semantic_similarity=0.95,
            concept_match=0.92,
            learner_fit=0.93,
            language_match=1.0,
            quality_score=0.9,
            misconception_relevance=0.88,
        ),
    ]
    ranked = rank_candidates(candidates)
    assert ranked[0].asset_id == "high"
