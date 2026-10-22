import shutil
from pathlib import Path

from app.core.errors import AccessPilotError


def create_workspace(sites_root: Path, work_root: Path, workspace_id: str) -> Path:
    destination = work_root / workspace_id
    if not destination.exists():
        shutil.copytree(sites_root, destination)
    return destination


def allowed_path(workspace: Path, relative_path: str) -> Path:
    candidate = (workspace / relative_path).resolve()
    root = workspace.resolve()
    if root not in candidate.parents or candidate.suffix not in {".html", ".css"}:
        raise AccessPilotError("path_not_allowed", "The file is outside the working copy.", 403)
    return candidate


def snapshot(workspace: Path, paths: list[str], number: int) -> None:
    snapshot_root = workspace / ".snapshots" / str(number)
    snapshot_root.mkdir(parents=True, exist_ok=True)
    for relative_path in paths:
        source = allowed_path(workspace, relative_path)
        destination = snapshot_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)