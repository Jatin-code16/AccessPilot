from uuid import uuid4

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.errors import AccessPilotError
from app.core.models import Coverage, Engine, Scan, ScanRequest
from app.core.store import store
from app.core.trace import TraceTimer, utc_now
from app.core.url_policy import validate_url


router = APIRouter(prefix="/api/scans", tags=["scans"])


@router.post("", response_model=Scan, status_code=201)
def create_scan(request: ScanRequest) -> Scan:
    if not request.consent:
        raise AccessPilotError("consent_required", "Authorisation is required before scanning.", 400)
    validate_url(request.url, allow_loopback=get_settings().allow_loopback)
    timer = TraceTimer(1, "scanner", "validate_target", "Target authorised")
    trace = [timer.finish(output_summary="URL policy passed")]
    scan = Scan(
        id=str(uuid4()),
        url=request.url,
        workingCopyId=None,
        startedAt=utc_now(),
        durationMs=trace[0].duration_ms or 0,
        title="",
        engine=Engine(name="axe-core", version="unknown"),
        findings=[],
        passCount=0,
        coverage=Coverage(ran=[], didNotRun=[], needsPerson=[]),
        trace=trace,
    )
    raise AccessPilotError(
        "scan_failed",
        "The browser scan service is not configured with the vendored axe engine.",
        502,
    )


@router.get("/{scan_id}", response_model=Scan)
def get_scan(scan_id: str) -> Scan:
    scan = store.get_scan(scan_id)
    if scan is None:
        raise AccessPilotError("not_found", "Scan was not found.", 404)
    return scan
