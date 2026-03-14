from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class MasterySnapshot:
    mastery_score: float
    confidence_score: float
    retention_score: float
    struggle_score: float
    attempts_count: int
    correct_attempts_count: int


@dataclass
class AttemptSignal:
    outcome_score: float
    used_hint: bool
    response_time_seconds: int
    expected_time_seconds: int
    error_severity: float
    confidence_self_reported: float | None = None


@dataclass
class MasteryUpdateResult:
    snapshot: MasterySnapshot
    state_label: str
    next_review_at: datetime


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _ema(previous: float, new_value: float, alpha: float) -> float:
    return alpha * new_value + (1 - alpha) * previous


def _compute_state_label(mastery: float, struggle: float) -> str:
    if mastery >= 80 and struggle <= 30:
        return "mastered"
    if mastery >= 60 and struggle <= 45:
        return "learning"
    if mastery < 40 or struggle >= 70:
        return "struggling"
    return "needs_revision"


def _review_days(mastery: float, struggle: float) -> int:
    if mastery >= 85 and struggle < 25:
        return 14
    if mastery >= 70 and struggle < 40:
        return 7
    if mastery >= 50:
        return 3
    return 1


def apply_attempt_to_mastery(
    current: MasterySnapshot,
    signal: AttemptSignal,
    now: datetime | None = None,
) -> MasteryUpdateResult:
    """Deterministic mastery update policy for student_id + concept_id unit.

    Uses weighted EMA updates and simple pedagogical penalties.
    """
    now = now or datetime.now(timezone.utc)

    speed_ratio = signal.expected_time_seconds / max(signal.response_time_seconds, 1)
    speed_score = _clamp(50 + (speed_ratio - 1.0) * 30)

    hint_penalty = 12 if signal.used_hint else 0
    error_penalty = _clamp(signal.error_severity * 10)

    mastery_signal = _clamp(signal.outcome_score - hint_penalty - 0.5 * error_penalty)

    confidence_input = signal.confidence_self_reported
    if confidence_input is None:
        confidence_input = 0.6 * signal.outcome_score + 0.4 * speed_score
    confidence_signal = _clamp(confidence_input - hint_penalty)

    retention_signal = _clamp(0.7 * signal.outcome_score + 0.3 * confidence_signal)

    struggle_signal = _clamp(100 - mastery_signal + error_penalty + (8 if signal.used_hint else 0))

    new_mastery = _clamp(_ema(current.mastery_score, mastery_signal, alpha=0.32))
    new_confidence = _clamp(_ema(current.confidence_score, confidence_signal, alpha=0.28))
    new_retention = _clamp(_ema(current.retention_score, retention_signal, alpha=0.18))
    new_struggle = _clamp(_ema(current.struggle_score, struggle_signal, alpha=0.30))

    attempts = current.attempts_count + 1
    correct_attempts = current.correct_attempts_count + (1 if signal.outcome_score >= 60 else 0)

    state_label = _compute_state_label(new_mastery, new_struggle)
    next_review_at = now + timedelta(days=_review_days(new_mastery, new_struggle))

    return MasteryUpdateResult(
        snapshot=MasterySnapshot(
            mastery_score=round(new_mastery, 2),
            confidence_score=round(new_confidence, 2),
            retention_score=round(new_retention, 2),
            struggle_score=round(new_struggle, 2),
            attempts_count=attempts,
            correct_attempts_count=correct_attempts,
        ),
        state_label=state_label,
        next_review_at=next_review_at,
    )
