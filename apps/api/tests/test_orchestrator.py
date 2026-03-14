from app.main import health, orchestrate_endpoint
from app.schemas import OrchestrationRequest, TaskType, UserType


def _request(task_type: TaskType) -> OrchestrationRequest:
    return OrchestrationRequest(
        task_type=task_type,
        user_type=UserType.STUDENT,
        board="CBSE",
        grade="8",
        subject="Math",
        chapter="Linear Equations",
        concept="Solving one-variable equations",
        student_level="beginner",
        language="en",
        prior_mistakes=["sign flip"],
        user_prompt="Help me understand this concept",
        learner_state={"mastery_score": 35, "retention_score": 30, "struggle_score": 68, "repeated_misconception": True},
    )


def test_healthcheck() -> None:
    body = health()
    assert body["status"] == "ok"
    assert body["service"] == "alfanumrik-orchestrator"


def test_no_model_route_for_deterministic_task() -> None:
    body = orchestrate_endpoint(_request(TaskType.DASHBOARD))
    assert body.lane == "no_model"
    assert body.used_retrieval_only is False
    assert body.retrieval_packet is None
    assert body.token_budget == 0


def test_retrieval_only_path_for_teacher_report() -> None:
    body = orchestrate_endpoint(_request(TaskType.TEACHER_REPORT))
    assert body.lane == "no_model"
    assert body.used_retrieval_only is True
    assert body.retrieval_packet is not None
    assert body.retrieval_packet["metadata_filters"]["language"] == "en"
    assert body.token_budget == 0


def test_cheap_lane_for_summarization() -> None:
    body = orchestrate_endpoint(_request(TaskType.SUMMARIZATION))
    assert body.lane == "cheap"
    assert body.used_retrieval_only is False
    assert body.retrieval_packet is not None
    assert len(body.retrieval_packet["retrieved_assets"]) >= 1
    assert body.token_budget == 320


def test_premium_lane_for_hard_reasoning() -> None:
    body = orchestrate_endpoint(_request(TaskType.HARD_REASONING))
    assert body.lane == "premium"
    assert body.used_retrieval_only is False
    assert body.retrieval_packet is not None
    assert body.token_budget == 1000
