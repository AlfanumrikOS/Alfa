from datetime import datetime, timezone

from app.mastery import (
    AttemptContext,
    AttemptSignal,
    ConceptOutcome,
    DifficultyLevel,
    DurationBand,
    EvidenceSource,
    HintLevel,
    MasterySnapshot,
    TeacherOverrideEvent,
    apply_attempt_to_mastery,
    apply_daily_decay,
    apply_teacher_override,
    compute_next_review,
    derive_state_label,
    update_mastery,
)


def _base_snapshot() -> MasterySnapshot:
    return MasterySnapshot(
        mastery_score=52,
        confidence_score=48,
        retention_score=45,
        struggle_score=50,
        attempts_count=10,
        correct_attempts_count=5,
    )


def test_mastery_update_improves_with_high_quality_evidence() -> None:
    old = _base_snapshot()
    outcome = ConceptOutcome(
        concept_id=301,
        weight=0.8,
        correct=True,
        partial_credit=1.0,
        misconception_triggered=False,
        repeated_misconception=False,
    )
    context = AttemptContext(
        event_type="question_attempted",
        source_type=EvidenceSource.FORMAL_TEST,
        question_difficulty=DifficultyLevel.MEDIUM,
        hint_level=HintLevel.NONE,
        duration_band=DurationBand.NORMAL,
        self_confidence="high",
        retry_count=0,
        days_since_last_attempt=8,
    )

    result = update_mastery(old, outcome, context, now=datetime(2026, 1, 1, tzinfo=timezone.utc))

    assert result.snapshot.mastery_score > old.mastery_score
    assert result.snapshot.confidence_score > old.confidence_score
    assert result.snapshot.struggle_score < old.struggle_score
    assert result.snapshot.attempts_count == old.attempts_count + 1


def test_mastery_update_penalizes_repeated_misconception() -> None:
    old = _base_snapshot()
    outcome = ConceptOutcome(
        concept_id=301,
        weight=1.0,
        correct=False,
        partial_credit=0.2,
        misconception_triggered=True,
        repeated_misconception=True,
    )
    context = AttemptContext(
        event_type="question_attempted",
        source_type=EvidenceSource.ADAPTIVE_PRACTICE,
        question_difficulty=DifficultyLevel.MEDIUM,
        hint_level=HintLevel.HEAVY,
        duration_band=DurationBand.SLOW,
        self_confidence="high",
        retry_count=2,
        days_since_last_attempt=1,
    )

    result = update_mastery(old, outcome, context)

    assert result.snapshot.mastery_score < old.mastery_score
    assert result.snapshot.struggle_score > old.struggle_score
    assert result.state_label in {"struggling", "learning", "needs_revision"}


def test_compute_next_review_shortens_on_repeated_misconception() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    review = compute_next_review(
        mastery=82,
        retention=70,
        struggle=40,
        misconception_repeated=True,
        now=now,
    )
    assert (review - now).days == 1


def test_state_labels_cover_fragile_mastery_and_mastered() -> None:
    fragile = derive_state_label(85, 74, 40, 52, attempts_count=20)
    mastered = derive_state_label(88, 76, 70, 22, attempts_count=20)
    assert fragile == "fragile_mastery"
    assert mastered == "mastered"


def test_daily_decay_after_grace_period() -> None:
    state = MasterySnapshot(
        mastery_score=82,
        confidence_score=80,
        retention_score=70,
        struggle_score=20,
        attempts_count=20,
        correct_attempts_count=16,
    )
    decayed = apply_daily_decay(state, days_inactive=20)
    assert decayed.retention_score < 70
    assert decayed.confidence_score < 80


def test_teacher_override_applies_bounded_changes() -> None:
    state = _base_snapshot()
    overridden = apply_teacher_override(
        state,
        TeacherOverrideEvent(override_type="improved_with_support", reason="Observed class improvement", teacher_id=22),
    )
    assert overridden.mastery_score > 52
    assert overridden.struggle_score < 50


def test_backward_compatible_apply_attempt_to_mastery_still_works() -> None:
    current = _base_snapshot()
    signal = AttemptSignal(
        outcome_score=88,
        used_hint=False,
        response_time_seconds=70,
        expected_time_seconds=90,
        error_severity=0.4,
        confidence_self_reported=82,
    )
    result = apply_attempt_to_mastery(current, signal, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert result.snapshot.mastery_score > current.mastery_score
    assert result.snapshot.attempts_count == current.attempts_count + 1
