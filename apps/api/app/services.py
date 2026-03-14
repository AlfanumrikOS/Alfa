from app.retrieval import build_context_packet, packet_to_dict
from app.router_policy import TOKEN_BUDGETS, route_for_task
from app.schemas import OrchestrationRequest, OrchestrationResponse, TaskType


DETERMINISTIC_TASKS = {
    TaskType.DASHBOARD,
    TaskType.SCORING,
    TaskType.SCHEDULING,
}

RETRIEVAL_ONLY_TASKS = {
    TaskType.TEACHER_REPORT,
}


def build_context_payload(request: OrchestrationRequest) -> dict:
    return {
        "user_type": request.user_type.value,
        "board": request.board,
        "grade": request.grade,
        "subject": request.subject,
        "chapter": request.chapter,
        "concept": request.concept,
        "student_level": request.student_level,
        "language": request.language,
        "prior_mistakes": request.prior_mistakes,
    }


def can_use_deterministic_path(request: OrchestrationRequest) -> bool:
    return request.task_type in DETERMINISTIC_TASKS


def can_use_retrieval_only(request: OrchestrationRequest) -> bool:
    return request.task_type in RETRIEVAL_ONLY_TASKS


def compose_response(lane: str, request: OrchestrationRequest, retrieval_only: bool) -> str:
    if retrieval_only:
        return (
            "Retrieval-only response: returned compact curriculum-and-learner packet "
            "and generated deterministic template output without model inference."
        )

    if lane == "no_model":
        return (
            "No-model path executed: deterministic code completed the task "
            f"'{request.task_type.value}' with zero LLM cost."
        )

    if lane == "cheap":
        return (
            "Cheap-lane response generated with capped token budget using graph-grounded, "
            f"learner-aware retrieval for concept '{request.concept}'."
        )

    return (
        "Premium fallback response generated for hard reasoning after deterministic and "
        "retrieval-first policy checks."
    )


def orchestrate(request: OrchestrationRequest) -> OrchestrationResponse:
    context = build_context_payload(request)

    if can_use_deterministic_path(request):
        lane = "no_model"
        reason = "Deterministic policy matched task type."
        retrieval_only = False
        return OrchestrationResponse(
            lane=lane,
            reason=reason,
            used_retrieval_only=retrieval_only,
            context_payload=context,
            retrieval_packet=None,
            token_budget=TOKEN_BUDGETS[lane],
            response=compose_response(lane, request, retrieval_only),
        )

    packet = build_context_packet(request)
    packet_dict = packet_to_dict(packet)

    if can_use_retrieval_only(request):
        lane = "no_model"
        reason = "Retrieval + templates are sufficient; model call avoided."
        retrieval_only = True
        return OrchestrationResponse(
            lane=lane,
            reason=reason,
            used_retrieval_only=retrieval_only,
            context_payload=context,
            retrieval_packet=packet_dict,
            token_budget=TOKEN_BUDGETS[lane],
            response=compose_response(lane, request, retrieval_only),
        )

    decision = route_for_task(request.task_type)
    return OrchestrationResponse(
        lane=decision.lane,
        reason=decision.reason,
        used_retrieval_only=False,
        context_payload=context,
        retrieval_packet=packet_dict,
        token_budget=TOKEN_BUDGETS[decision.lane],
        response=compose_response(decision.lane, request, retrieval_only=False),
    )
