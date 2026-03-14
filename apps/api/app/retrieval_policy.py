
def choose_response_mode(task_type: str, learner_state: dict | None, prior_mistakes: list[str]) -> str:
    learner_state = learner_state or {}
    mastery = float(learner_state.get("mastery_score", 50))
    retention = float(learner_state.get("retention_score", 50))
    struggle = float(learner_state.get("struggle_score", 50))
    repeated_misconception = bool(learner_state.get("repeated_misconception", False))

    if task_type == "teacher_report":
        return "analytics_summary_with_intervention_actions"

    if task_type == "tutor_hint":
        if mastery < 40 or struggle > 60 or repeated_misconception or len(prior_mistakes) >= 2:
            return "prerequisite_recap_then_bridge_example_then_guided_hint"
        return "one_hint_then_check_understanding"

    if mastery < 40 and struggle > 60:
        return "simple_explanation_then_prerequisite_recap"
    if mastery >= 80 and retention >= 60 and struggle < 40:
        return "concise_explanation_then_challenge_check"
    if retention < 45:
        return "revision_recall_then_targeted_example"

    return "simple_explanation_then_guided_question"
