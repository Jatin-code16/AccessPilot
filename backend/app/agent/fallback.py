from uuid import uuid4

from app.core.config import Settings
from app.core.errors import AccessPilotError
from app.core.models import AgentRun, Finding, Proposal, Scan, TraceEntry
from app.core.store import Store
from app.core.trace import TraceTimer
from app.repair.proposals import build_proposal


def run_builtin(scan: Scan, settings: Settings, store: Store) -> AgentRun:
    trace: list[TraceEntry] = [TraceTimer(1, "agent", "agent_started", "Agent started").finish(output_summary="Using built-in guidance")]
    proposals: list[Proposal] = []
    needs_human: list[dict[str, str]] = []
    explanations = {finding.id: finding.explanation.why for finding in scan.findings}
    for index, finding in enumerate(scan.findings, start=2):
        if finding.template is None or finding.needs_human:
            needs_human.append({"findingId": finding.id, "reason": "No safe automatic repair template is available."})
            trace.append(TraceTimer(index, "agent", "mark_needs_human", "Needs a person").finish(output_summary=finding.rule_id))
            continue
        try:
            proposal = build_proposal(scan, finding, settings, store)
        except AccessPilotError as error:
            needs_human.append({"findingId": finding.id, "reason": error.message})
            trace.append(TraceTimer(index, "agent", "mark_needs_human", "Needs a person").finish(output_summary=error.code))
            continue
        proposals.append(proposal)
        trace.append(TraceTimer(index, "agent", "draft_repair", "Drafted a fix").finish(output_summary=proposal.template))
    return AgentRun(
        id=str(uuid4()), scanId=scan.id, aiUsed=False, model=None, fallbackReason="no_key",
        explanations=explanations, proposals=proposals, needsHuman=needs_human, trace=trace,
    )