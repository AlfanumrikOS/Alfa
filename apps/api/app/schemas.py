from dataclasses import dataclass, field
from enum import Enum


class TaskType(str, Enum):
    DASHBOARD = "dashboard"
    SCORING = "scoring"
    SCHEDULING = "scheduling"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    QUESTION_DRAFT = "question_draft"
    TUTOR_HINT = "tutor_hint"
    CONCEPT_EXPLANATION = "concept_explanation"
    TEACHER_REPORT = "teacher_report"
    HARD_REASONING = "hard_reasoning"
    LESSON_PLANNING = "lesson_planning"


class UserType(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    PARENT = "parent"
    ADMIN = "admin"


@dataclass
class OrchestrationRequest:
    task_type: TaskType
    user_type: UserType
    board: str
    grade: str
    subject: str
    chapter: str
    concept: str
    student_level: str
    language: str
    user_prompt: str
    prior_mistakes: list[str] = field(default_factory=list)


@dataclass
class RouteDecision:
    lane: str
    reason: str


@dataclass
class RetrievalAsset:
    type: str
    id: str
    summary: str


@dataclass
class RetrievalCandidate:
    asset_id: str
    asset_type: str
    summary: str
    semantic_similarity: float
    concept_match: float
    learner_fit: float
    language_match: float
    quality_score: float
    misconception_relevance: float


@dataclass
class RetrievalPacket:
    task_type: str
    concept: str
    prerequisites: list[str]
    learner_level: str
    recent_errors: list[str]
    metadata_filters: dict
    retrieved_assets: list[RetrievalAsset]
    recommended_response_mode: str
    retrieval_debug: dict


@dataclass
class OrchestrationResponse:
    lane: str
    reason: str
    used_retrieval_only: bool
    context_payload: dict
    retrieval_packet: dict | None
    token_budget: int
    response: str
