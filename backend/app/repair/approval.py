from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

from app.core.config import Settings
from app.core.errors import AccessPilotError
from app.core.models import ApprovalResponse, Proposal
from app.core.store import Approval, Store


def approve(proposal: Proposal, store: Store, settings: Settings) -> ApprovalResponse:
    if proposal.status in {"applied", "skipped"}:
        raise AccessPilotError("invalid_state", "This proposal cannot be approved.", 409)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.approval_ttl_seconds)
    token = token_urlsafe(32)
    store.approvals[token] = Approval(proposal.id, proposal.diff_hash, expires_at)
    proposal.status = "approved"
    return ApprovalResponse(proposalId=proposal.id, token=token, diffHash=proposal.diff_hash, expiresAt=expires_at.isoformat())


def consume(token: str, proposal: Proposal, store: Store) -> None:
    approval = store.approvals.get(token)
    if approval is None or approval.used or approval.proposal_id != proposal.id or approval.diff_hash != proposal.diff_hash:
        raise AccessPilotError("approval_required", "A valid approval token is required.", 403)
    if approval.expires_at <= datetime.now(timezone.utc):
        raise AccessPilotError("approval_required", "The approval token has expired.", 403)
    approval.used = True