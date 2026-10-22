from fastapi import APIRouter

from app.core.config import get_settings
from app.core.errors import AccessPilotError
from app.core.models import Scan, ScanRequest
from app.core.store import store
from app.core.url_policy import validate_url
from app.scan.service import run_scan


router = APIRouter(prefix="/api/scans", tags=["scans"])


@router.post("", response_model=Scan, status_code=201)
def create_scan(request: ScanRequest) -> Scan:
    if not request.consent:
        raise AccessPilotError("consent_required", "Authorisation is required before scanning.", 400)
    validate_url(request.url, allow_loopback=get_settings().allow_loopback)
    scan = run_scan(request.url, get_settings())
    store.save_scan(scan)
    return scan


@router.get("/{scan_id}", response_model=Scan)
def get_scan(scan_id: str) -> Scan:
    scan = store.get_scan(scan_id)
    if scan is None:
        raise AccessPilotError("not_found", "Scan was not found.", 404)
    return scan
