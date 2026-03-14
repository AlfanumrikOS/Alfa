from app.schemas import RouteDecision, TaskType


NO_MODEL_TASKS = {
    TaskType.DASHBOARD,
    TaskType.SCORING,
    TaskType.SCHEDULING,
}

CHEAP_MODEL_TASKS = {
    TaskType.SUMMARIZATION,
    TaskType.TRANSLATION,
    TaskType.QUESTION_DRAFT,
}

PREMIUM_MODEL_TASKS = {
    TaskType.HARD_REASONING,
    TaskType.LESSON_PLANNING,
}

TOKEN_BUDGETS = {
    "no_model": 0,
    "cheap": 320,
    "premium": 1000,
}


def route_for_task(task_type: TaskType) -> RouteDecision:
    if task_type in NO_MODEL_TASKS:
        return RouteDecision(
            lane="no_model",
            reason="Task is deterministic and should run in rules/analytics engine.",
        )

    if task_type in CHEAP_MODEL_TASKS:
        return RouteDecision(
            lane="cheap",
            reason="Task is language-light and suitable for low-cost model lane.",
        )

    if task_type in PREMIUM_MODEL_TASKS:
        return RouteDecision(
            lane="premium",
            reason="Task requires high-stakes reasoning quality fallback.",
        )

    return RouteDecision(
        lane="cheap",
        reason="Default lane keeps costs controlled for standard tutoring/reporting tasks.",
    )
