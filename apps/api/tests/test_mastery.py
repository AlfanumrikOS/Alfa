from datetime import datetime, timezone

from app.mastery import AttemptSignal, MasterySnapshot, apply_attempt_to_mastery


def test_mastery_update_improves_with_strong_attempt() -> None:
    current = MasterySnapshot(
        mastery_score=52,
        confidence_score=48,
        retention_score=45,
        struggle_score=50,
        attempts_count=10,
        correct_attempts_count=5,
    )
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
    assert result.snapshot.struggle_score < current.struggle_score
    assert result.snapshot.attempts_count == 11
    assert result.snapshot.correct_attempts_count == 6
    assert result.next_review_at > datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_mastery_update_penalizes_hint_heavy_weak_attempt() -> None:
    current = MasterySnapshot(
        mastery_score=60,
        confidence_score=62,
        retention_score=58,
        struggle_score=38,
        attempts_count=8,
        correct_attempts_count=5,
    )
    signal = AttemptSignal(
        outcome_score=35,
        used_hint=True,
        response_time_seconds=220,
        expected_time_seconds=90,
        error_severity=3.5,
        confidence_self_reported=25,
    )

    result = apply_attempt_to_mastery(current, signal, now=datetime(2026, 1, 1, tzinfo=timezone.utc))

    assert result.snapshot.mastery_score < current.mastery_score
    assert result.snapshot.struggle_score > current.struggle_score
    assert result.state_label in {"struggling", "needs_revision"}


def test_mastery_scores_clamped_to_valid_range() -> None:
    current = MasterySnapshot(
        mastery_score=99,
        confidence_score=99,
        retention_score=99,
        struggle_score=1,
        attempts_count=100,
        correct_attempts_count=90,
    )
    signal = AttemptSignal(
        outcome_score=120,
        used_hint=False,
        response_time_seconds=1,
        expected_time_seconds=90,
        error_severity=0,
        confidence_self_reported=150,
    )

    result = apply_attempt_to_mastery(current, signal)

    assert 0 <= result.snapshot.mastery_score <= 100
    assert 0 <= result.snapshot.confidence_score <= 100
    assert 0 <= result.snapshot.retention_score <= 100
    assert 0 <= result.snapshot.struggle_score <= 100
