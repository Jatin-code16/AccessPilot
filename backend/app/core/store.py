from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock

from app.core.models import AgentRun, ApplyResult, Proposal, Scan


@dataclass
class Approval:
    proposal_id: str
    diff_hash: str
    expires_at: datetime
    used: bool = False


@dataclass
class Store:
    scans: dict[str, Scan] = field(default_factory=dict)
    agent_runs: dict[str, AgentRun] = field(default_factory=dict)
    proposals: dict[str, Proposal] = field(default_factory=dict)
    results: dict[str, ApplyResult] = field(default_factory=dict)
    approvals: dict[str, Approval] = field(default_factory=dict)
    baseline_findings: dict[str, set[str]] = field(default_factory=dict)
    working_copies: dict[str, str] = field(default_factory=dict)
    snapshot_numbers: dict[str, int] = field(default_factory=dict)
    lock: Lock = field(default_factory=Lock)

    def save_scan(self, scan: Scan) -> None:
        with self.lock:
            self.scans[scan.id] = scan

    def get_scan(self, scan_id: str) -> Scan | None:
        with self.lock:
            return self.scans.get(scan_id)


store = Store()
