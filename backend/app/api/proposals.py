from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.errors import AccessPilotError
from app.core.models import ApprovalResponse, ApplyRequest, ApplyResult, Proposal, ProposalEdit
from app.core.store import store
from app.repair.approval import approve as approve_proposal
from app.repair.approval import consume
from app.repair.proposals import proposal_defaults
from app.repair.templates import apply_template


router = APIRouter(prefix="/api/proposals", tags=["proposals"])


def get_proposal(proposal_id: str) -> Proposal:
    proposal = store.proposals.get(proposal_id)
    if proposal is None:
        raise AccessPilotError("not_found", "Proposal was not found.", 404)
    return proposal


def proposal_source(proposal: Proposal) -> tuple[Path, str]:
    settings = get_settings()
    relative_path = proposal.files[0]
    root = settings.sites_root
    path = (root / relative_path).resolve()
    if root.resolve() not in path.parents or path.suffix not in {".html", ".css"}:
        raise AccessPilotError("path_not_allowed", "The proposal file is outside the demo site.", 403)
    return path, relative_path


@router.get("/{proposal_id}", response_model=Proposal)
def read_proposal(proposal_id: str) -> Proposal:
    return get_proposal(proposal_id)


@router.patch("/{proposal_id}", response_model=Proposal)
def edit_proposal(proposal_id: str, request: ProposalEdit) -> Proposal:
    proposal = get_proposal(proposal_id)
    if proposal.status == "applied":
        raise AccessPilotError("invalid_state", "An applied proposal cannot be edited.", 409)
    allowed = {"T1": {"labelText"}, "T2": {"altText"}, "T3": set(), "T4": set(), "T5": {"labelText"}}[proposal.template]
    if set(request.params) != allowed or any(not value.strip() or len(value) > 200 or any(ord(char) < 32 for char in value) for value in request.params.values()):
        raise AccessPilotError("invalid_request", "Only allowed wording parameters may be edited.", 422)
    params = {**proposal.params, **request.params}
    path, relative_path = proposal_source(proposal)
    result = apply_template(proposal.template, path.read_text(encoding="utf-8"), params, relative_path)
    proposal.params = params
    proposal.diff = result.diff
    proposal.diff_hash = sha256(result.diff.encode()).hexdigest()
    proposal.status = "proposed"
    return proposal


@router.post("/{proposal_id}/approve", response_model=ApprovalResponse)
def approve(proposal_id: str) -> ApprovalResponse:
    return approve_proposal(get_proposal(proposal_id), store, get_settings())


@router.post("/{proposal_id}/skip", response_model=Proposal)
def skip(proposal_id: str) -> Proposal:
    proposal = get_proposal(proposal_id)
    if proposal.status == "applied":
        raise AccessPilotError("invalid_state", "An applied proposal cannot be skipped.", 409)
    proposal.status = "skipped"
    return proposal


@router.post("/{proposal_id}/apply", response_model=ApplyResult)
def apply(proposal_id: str, request: ApplyRequest) -> ApplyResult:
    proposal = get_proposal(proposal_id)
    consume(request.token, proposal, store)
    if proposal.status != "approved":
        raise AccessPilotError("invalid_state", "The proposal must be approved first.", 409)
    scan = store.get_scan(proposal.scan_id)
    if scan is None or "/sites/original/golden/" not in scan.url:
        raise AccessPilotError("apply_not_allowed", "Only the bundled Golden Site may be changed.", 403)
    settings = get_settings()
    from app.repair.workspace import allowed_path, create_workspace, snapshot
    from app.scan.service import run_scan
    from app.verify.compare import compare
    from app.verify.status import derive_status

    workspace = create_workspace(settings.sites_root, settings.work_root, scan.id)
    store.working_copies[scan.id] = str(workspace)
    control_url = f"http://127.0.0.1:{settings.backend_port}/sites/work/{scan.id}/control/index.html"
    control_before = run_scan(control_url, settings)
    store.baseline_findings[scan.id] = {finding.match_key for finding in control_before.findings}
    snapshot_number = store.snapshot_numbers.get(scan.id, 0) + 1
    store.snapshot_numbers[scan.id] = snapshot_number
    snapshot(workspace, proposal.files, snapshot_number)
    target_path = allowed_path(workspace, proposal.files[0])
    try:
        result = apply_template(proposal.template, target_path.read_text(encoding="utf-8"), proposal.params, proposal.files[0])
        target_path.write_text(result.source, encoding="utf-8")
        after_url = f"http://127.0.0.1:{settings.backend_port}/sites/work/{scan.id}/golden/index.html"
        after = run_scan(after_url, settings)
        control_after = run_scan(control_url, settings)
    except Exception as error:
        snapshot_path = workspace / ".snapshots" / str(snapshot_number) / proposal.files[0]
        target_path.write_bytes(snapshot_path.read_bytes())
        proposal.status = "failed"
        raise AccessPilotError("scan_failed", "The patched page could not be re-tested.", 502) from error
    resolved, remaining, introduced = compare(scan, after)
    control_new = sorted({finding.match_key for finding in control_after.findings} - store.baseline_findings[scan.id])
    status = derive_status(proposal.finding_id in {finding.id for finding in scan.findings if finding.match_key in resolved}, remaining, introduced, not control_new)
    proposal.status = "applied" if status != "failed" else "failed"
    result = ApplyResult(
        proposalId=proposal.id, beforeScanId=scan.id, afterScanId=after.id,
        comparison={"resolved": resolved, "remaining": remaining, "introduced": introduced},
        control={"passed": not control_new, "newFindings": control_new}, status=status,
        reason=f"Resolved {len(resolved)}, remaining {len(remaining)}, new {len(introduced)}.", trace=after.trace,
    )
    store.results[proposal.id] = result
    return result