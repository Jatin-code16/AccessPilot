from pathlib import Path

from app.core.errors import AccessPilotError


def require_scan_assets(axe_path: Path) -> None:
    if not axe_path.is_file():
        raise AccessPilotError("browser_unavailable", "The vendored axe engine is missing.", 503)
