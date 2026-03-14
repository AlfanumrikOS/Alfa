from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum


class HintLevel(str, Enum):
    NONE = "none"
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"
    ANSWER_REVEAL = "answer_reveal"


class DurationBand(str, Enum):
    FAST = "fast"
    NORMAL = "normal"
    SLOW = "slow"
    TIMEOUT = "timeout"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class EvidenceSource(str, Enum):
    FORMAL_TEST = "formal_test"
    ADAPTIVE_PRACTICE = "adaptive_practice"
    TUTOR_GUIDED = "tutor_guided"
    REVISION = "revision"


@dataclass
class MasterySnapshot:
    mastery_score: float
    confidence_score: float
    retention_score: float
    struggle_score: float
    attempts_count: int
    correct_attempts_count: int
    evidence_count: int = 0
    consecutive_correct_count: int = 0
    consecutive_wrong_count: int = 0
    last_attempt_at: datetime | None = None
    last_mastered_at: datetime | None = None


@dataclass
class AttemptSignal:
    outcome_score: float
    used_hint: bool
    response_time_seconds: int
    expected_time_seconds: int
    error_severity: float
    confidence_self_reported: float | None = None


@dataclass
class ConceptOutcome:
    concept_id: int
    weight: float
    correct: bool
    partial_credit: float
    misconception_triggered: bool = False
    repeated_misconception: bool = False
    relevant_reasoning: bool = False


@dataclass
class AttemptContext:
    event_type: str
    source_type: EvidenceSource
    question_difficulty: DifficultyLevel
    hint_level: HintLevel
    duration_band: DurationBand
    self_confidence: str | None
    retry_count: int = 0
    days_since_last_attempt: int = 0


@dataclass
class MasteryUpdateResult:
    snapshot: MasterySnapshot
    state_label: str
    next_review_at: datetime


@dataclass
class TeacherOverrideEvent:
    override_type: str
    reason: str
    teacher_id: int | None = None


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def derive_state_label(
    mastery: float,
    confidence: float,
    retention: float,
    struggle: float,
    attempts_count: int,
) -> str:
    if attempts_count == 0:
        return "unknown"
    if attempts_count <= 1 and mastery < 20:
        return "introduced"
    if mastery < 45 and struggle >= 60:
        return "struggling"
    if mastery < 50:
        return "learning"
    if 50 <= mastery < 65 and struggle < 65:
        return "improving"
    if 65 <= mastery < 80 and confidence >= 50:
        return "functional"
    if mastery >= 80 and confidence >= 70 and retention >= 60 and struggle < 45:
        return "mastered"
    if mastery >= 80 and (retention < 50 or struggle >= 45):
        return "fragile_mastery"
    if mastery >= 60 and retention < 45:
        return "needs_revision"
    if retention < 25 and mastery < 60:
        return "forgotten"
    return "learning"


def compute_next_review(
    mastery: float,
    retention: float,
    struggle: float,
    misconception_repeated: bool,
    now: datetime,
) -> datetime:
    if mastery < 30:
        days = 1
    elif mastery < 50:
        days = 2
    elif mastery < 65:
        days = 4
    elif mastery < 80:
        days = 7
    elif retention >= 80:
        days = 30
    elif retention >= 60:
        days = 14
    else:
        days = 7

    if struggle >= 70 or misconception_repeated:
        days = min(days, 1)

    return now + timedelta(days=days)


def score_correctness(outcome: ConceptOutcome, retry_count: int) -> float:
    if outcome.correct and retry_count == 0:
        return 30
    if outcome.correct and retry_count > 0:
        return 18
    if not outcome.correct and outcome.partial_credit >= 0.5:
        return 10
    if not outcome.correct and outcome.relevant_reasoning:
        return 4
    if outcome.repeated_misconception:
        return -22
    if not outcome.correct:
        return -15
    return 0


def score_hints(hint_level: HintLevel) -> float:
    mapping = {
        HintLevel.NONE: 10,
        HintLevel.LIGHT: 4,
        HintLevel.MODERATE: 0,
        HintLevel.HEAVY: -8,
        HintLevel.ANSWER_REVEAL: -14,
    }
    return mapping[hint_level]


def score_speed(duration_band: DurationBand, correct: bool) -> float:
    if duration_band == DurationBand.FAST:
        return 6
    if duration_band == DurationBand.NORMAL:
        return 3
    if duration_band == DurationBand.SLOW and correct:
        return 0
    if duration_band == DurationBand.SLOW and not correct:
        return -6
    return -10


def score_misconception(outcome: ConceptOutcome) -> float:
    if outcome.repeated_misconception:
        return -18
    if outcome.misconception_triggered:
        return -12
    return 4


def score_confidence_alignment(self_confidence: str | None, correct: bool) -> float:
    if not self_confidence:
        return 0
    conf = self_confidence.lower()
    if conf == "high" and correct:
        return 5
    if conf == "low" and correct:
        return 2
    if conf == "high" and not correct:
        return -8
    if conf == "low" and not correct:
        return -2
    return 0


def score_difficulty(difficulty: DifficultyLevel, correct: bool) -> float:
    if difficulty == DifficultyLevel.EASY and correct:
        return 4
    if difficulty == DifficultyLevel.MEDIUM and correct:
        return 8
    if difficulty == DifficultyLevel.HARD and correct:
        return 12
    if difficulty == DifficultyLevel.EASY and not correct:
        return -8
    if difficulty == DifficultyLevel.MEDIUM and not correct:
        return -10
    return -8


def score_recency(days_since_last_attempt: int, correct: bool) -> float:
    if days_since_last_attempt >= 14:
        return 12 if correct else -10
    if days_since_last_attempt >= 7:
        return 8 if correct else -6
    if days_since_last_attempt >= 2:
        return 4 if correct else -3
    return 0


def learning_rate(mastery_score: float, source_type: EvidenceSource, hint_level: HintLevel) -> float:
    if mastery_score < 20:
        lr = 0.35
    elif mastery_score < 65:
        lr = 0.25
    else:
        lr = 0.12

    if source_type == EvidenceSource.FORMAL_TEST:
        lr *= 1.15
    if source_type == EvidenceSource.TUTOR_GUIDED and hint_level in {HintLevel.HEAVY, HintLevel.ANSWER_REVEAL}:
        lr *= 0.75
    return lr


def _struggle_delta(outcome: ConceptOutcome, hint_level: HintLevel, duration_band: DurationBand) -> float:
    wrongness = 20 if not outcome.correct else -6
    hint_burden = {HintLevel.NONE: -4, HintLevel.LIGHT: 0, HintLevel.MODERATE: 4, HintLevel.HEAVY: 10, HintLevel.ANSWER_REVEAL: 14}[hint_level]
    repeated_mis = 14 if outcome.repeated_misconception else (6 if outcome.misconception_triggered else -2)
    time_component = {DurationBand.FAST: -2, DurationBand.NORMAL: 0, DurationBand.SLOW: 5, DurationBand.TIMEOUT: 10}[duration_band]
    return 0.35 * wrongness + 0.25 * hint_burden + 0.20 * repeated_mis + 0.20 * time_component


def update_mastery(
    old_state: MasterySnapshot,
    concept_outcome: ConceptOutcome,
    attempt_context: AttemptContext,
    now: datetime | None = None,
) -> MasteryUpdateResult:
    now = now or datetime.now(timezone.utc)

    correctness_component = score_correctness(concept_outcome, attempt_context.retry_count)
    hint_component = score_hints(attempt_context.hint_level)
    speed_component = score_speed(attempt_context.duration_band, concept_outcome.correct)
    misconception_component = score_misconception(concept_outcome)
    confidence_align = score_confidence_alignment(attempt_context.self_confidence, concept_outcome.correct)
    difficulty_component = score_difficulty(attempt_context.question_difficulty, concept_outcome.correct)
    recency_component = score_recency(attempt_context.days_since_last_attempt, concept_outcome.correct)

    mastery_delta_raw = (
        0.45 * correctness_component
        + 0.20 * difficulty_component
        + 0.15 * misconception_component
        + 0.10 * speed_component
        + 0.10 * recency_component
    ) * concept_outcome.weight

    confidence_delta_raw = (
        0.35 * correctness_component
        + 0.25 * hint_component
        + 0.20 * speed_component
        + 0.20 * confidence_align
    ) * concept_outcome.weight

    retention_delta_raw = (
        0.50 * recency_component + 0.30 * correctness_component + 0.20 * misconception_component
    ) * concept_outcome.weight

    struggle_delta_raw = _struggle_delta(concept_outcome, attempt_context.hint_level, attempt_context.duration_band)

    lr = learning_rate(old_state.mastery_score, attempt_context.source_type, attempt_context.hint_level)

    new_mastery = _clamp(old_state.mastery_score + lr * mastery_delta_raw)
    new_confidence = _clamp(old_state.confidence_score + lr * confidence_delta_raw)
    new_retention = _clamp(old_state.retention_score + lr * retention_delta_raw)
    new_struggle = _clamp(old_state.struggle_score + 0.25 * struggle_delta_raw)

    attempts = old_state.attempts_count + 1
    evidence_count = old_state.evidence_count + 1
    is_correct = concept_outcome.correct
    correct_attempts = old_state.correct_attempts_count + (1 if is_correct else 0)

    consecutive_correct = old_state.consecutive_correct_count + 1 if is_correct else 0
    consecutive_wrong = old_state.consecutive_wrong_count + 1 if not is_correct else 0

    label = derive_state_label(new_mastery, new_confidence, new_retention, new_struggle, attempts)
    next_review = compute_next_review(
        mastery=new_mastery,
        retention=new_retention,
        struggle=new_struggle,
        misconception_repeated=concept_outcome.repeated_misconception,
        now=now,
    )

    last_mastered = old_state.last_mastered_at
    if label in {"mastered", "functional"} and is_correct:
        last_mastered = now

    updated = MasterySnapshot(
        mastery_score=round(new_mastery, 2),
        confidence_score=round(new_confidence, 2),
        retention_score=round(new_retention, 2),
        struggle_score=round(new_struggle, 2),
        attempts_count=attempts,
        correct_attempts_count=correct_attempts,
        evidence_count=evidence_count,
        consecutive_correct_count=consecutive_correct,
        consecutive_wrong_count=consecutive_wrong,
        last_attempt_at=now,
        last_mastered_at=last_mastered,
    )

    return MasteryUpdateResult(snapshot=updated, state_label=label, next_review_at=next_review)


def apply_teacher_override(state: MasterySnapshot, event: TeacherOverrideEvent) -> MasterySnapshot:
    """Apply bounded teacher override effects without arbitrary score jumps."""
    if event.override_type == "needs_revision":
        state.retention_score = _clamp(state.retention_score - 8)
        state.struggle_score = _clamp(state.struggle_score + 6)
    elif event.override_type == "improved_with_support":
        state.mastery_score = _clamp(state.mastery_score + 4)
        state.confidence_score = _clamp(state.confidence_score + 3)
        state.struggle_score = _clamp(state.struggle_score - 4)
    elif event.override_type == "suppress_over_penalization":
        state.struggle_score = _clamp(state.struggle_score - 10)
    return state


def apply_daily_decay(state: MasterySnapshot, days_inactive: int) -> MasterySnapshot:
    """Decay retention/confidence and optionally mastery after grace periods."""
    if days_inactive <= 0:
        return state

    if state.mastery_score < 50:
        grace = 9999
    elif state.mastery_score < 80:
        grace = 10
    else:
        grace = 14

    overdue_days = max(0, days_inactive - grace)
    if overdue_days == 0:
        return state

    state.retention_score = _clamp(state.retention_score - 0.4 * overdue_days)
    state.confidence_score = _clamp(state.confidence_score - 0.2 * overdue_days)
    if state.retention_score < 50:
        state.mastery_score = _clamp(state.mastery_score - 0.1 * overdue_days)
    return state


def apply_attempt_to_mastery(
    current: MasterySnapshot,
    signal: AttemptSignal,
    now: datetime | None = None,
) -> MasteryUpdateResult:
    """Backward-compatible adapter for earlier API surface."""
    context = AttemptContext(
        event_type="question_attempted",
        source_type=EvidenceSource.ADAPTIVE_PRACTICE,
        question_difficulty=DifficultyLevel.MEDIUM,
        hint_level=HintLevel.HEAVY if signal.used_hint else HintLevel.NONE,
        duration_band=DurationBand.FAST if signal.response_time_seconds <= signal.expected_time_seconds else DurationBand.SLOW,
        self_confidence="high" if (signal.confidence_self_reported or 0) >= 70 else "low",
        retry_count=0,
        days_since_last_attempt=0,
    )
    outcome = ConceptOutcome(
        concept_id=0,
        weight=1.0,
        correct=signal.outcome_score >= 60,
        partial_credit=signal.outcome_score / 100,
        misconception_triggered=signal.error_severity >= 2,
        repeated_misconception=signal.error_severity >= 4,
        relevant_reasoning=signal.outcome_score >= 30,
    )
    return update_mastery(current, outcome, context, now=now)
