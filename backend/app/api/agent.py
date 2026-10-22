from fastapi import APIRouter

from app.agent.fallback import run_builtin
from app.core.config import get_settings
from app.core.errors import AccessPilotError
from app.core.models import AgentRequest, AgentRun
from app.core.store import store


router = APIRouter(prefix="/api/scans", tags=["agent"])


@router.post("/{scan_id}/agent", response_model=AgentRun)
def run_agent(scan_id: str, request: AgentRequest | None = None) -> AgentRun:
    scan = store.get_scan(scan_id)
    if scan is None:
        raise AccessPilotError("not_found", "Scan was not found.", 404)
    mode = request.mode if request else "auto"
    if mode not in {"auto", "builtin"}:
        raise AccessPilotError("invalid_request", "Agent mode is invalid.", 422)
    agent_run = run_builtin(scan, get_settings(), store)
    store.agent_runs[agent_run.id] = agent_run
    return agent_run