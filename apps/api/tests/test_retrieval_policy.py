from app.retrieval_policy import choose_response_mode


def test_policy_uses_bridge_mode_for_low_mastery_high_struggle() -> None:
    mode = choose_response_mode(
        task_type="tutor_hint",
        learner_state={"mastery_score": 30, "retention_score": 25, "struggle_score": 75, "repeated_misconception": True},
        prior_mistakes=["unit confusion", "step skip"],
    )
    assert mode == "prerequisite_recap_then_bridge_example_then_guided_hint"


def test_policy_prefers_concise_mode_for_high_mastery() -> None:
    mode = choose_response_mode(
        task_type="concept_explanation",
        learner_state={"mastery_score": 86, "retention_score": 72, "struggle_score": 22},
        prior_mistakes=[],
    )
    assert mode == "concise_explanation_then_challenge_check"


def test_policy_teacher_report_mode() -> None:
    mode = choose_response_mode(task_type="teacher_report", learner_state=None, prior_mistakes=[])
    assert mode == "analytics_summary_with_intervention_actions"
