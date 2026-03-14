"""Transport-agnostic entrypoint for Alfanumrik orchestration core.

This module keeps business logic independent from web frameworks so it can be
mounted by FastAPI, gRPC, or queue workers with minimal adapter code.
"""

from app.schemas import OrchestrationRequest, OrchestrationResponse
from app.services import orchestrate


def health() -> dict:
    return {"status": "ok", "service": "alfanumrik-orchestrator"}


def orchestrate_endpoint(request: OrchestrationRequest) -> OrchestrationResponse:
    return orchestrate(request)
