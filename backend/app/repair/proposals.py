from hashlib import sha256
from uuid import uuid4

from app.core.errors import AccessPilotError
from app.core.config import Settings
from app.core.models import Finding, Proposal, Scan
from app.core.store import Store
from app.repair.templates import apply_template


def target_id(finding: Finding) -> str:
    target = finding.target.strip()
    if target.startswith("#"):
        return target[1:]
    raise AccessPilotError("template_mismatch", "The finding target has no stable element id.", 409)


def proposal_defaults(finding: Finding) -> dict[str, str]:
    if finding.template == "T1":
        return {"targetId": target_id(finding), "labelText": "Email address"}
    if finding.template == "T2":
        return {"targetId": target_id(finding), "altText": "Student photo"}
    if finding.template == "T3":
        return {"selector": finding.target, "newColor": "#4b5563"}
    if finding.template == "T4":
        return {"lang": "en"}
    return {"targetId": target_id(finding), "labelText": "Submit application"}


def build_proposal(scan: Scan, finding: Finding, settings: Settings, store: Store) -> Proposal:
    if finding.template is None:
        raise AccessPilotError("needs_human", "No repair template is available.", 409)
    params = proposal_defaults(finding)
    file_path = "golden/index.html" if finding.template != "T3" else "shared.css"
    source_path = settings.sites_root / file_path
    source_root = settings.sites_root
    if source_root.resolve() not in source_path.resolve().parents:
        raise AccessPilotError("path_not_allowed", "The proposal file is outside the demo site.", 403)
    text = source_path.read_text(encoding="utf-8")
    result = apply_template(finding.template, text, params, file_path)
    diff_hash = sha256(result.diff.encode()).hexdigest()
    proposal = Proposal(
        id=str(uuid4()), scanId=scan.id, findingId=finding.id, template=finding.template,
        status="proposed", rationale=finding.explanation.why, risk="low", files=[file_path],
        params=params, diff=result.diff, diffHash=diff_hash, proposedBy="builtin",
    )
    store.proposals[proposal.id] = proposal
    return proposal