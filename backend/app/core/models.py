from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


Impact = Literal["critical", "serious", "moderate", "minor"]
Actor = Literal["scanner", "agent", "you", "retest", "system"]
FindingSource = Literal["axe", "keyboard"]
FindingKind = Literal["violation", "incomplete"]
TemplateName = Literal["T1", "T2", "T3", "T4", "T5"]
ProposalStatus = Literal["proposed", "approved", "rejected", "skipped", "applied", "failed"]
Status = Literal["passed", "partial", "failed", "needs_human"]


class Explanation(StrictModel):
    who: str
    blocked_from: str = Field(alias="blockedFrom")
    why: str


class Finding(StrictModel):
    id: str
    match_key: str = Field(alias="matchKey")
    fingerprint: str
    source: FindingSource
    kind: FindingKind
    rule_id: str = Field(alias="ruleId")
    impact: Impact | None
    help: str
    help_url: str | None = Field(alias="helpUrl")
    tags: list[str]
    wcag: list[str]
    target: str
    snippet: str = Field(max_length=300)
    explanation: Explanation
    template: TemplateName | None
    needs_human: bool = Field(alias="needsHuman")


class TraceEntry(StrictModel):
    seq: int
    actor: Actor
    name: str
    summary: str = Field(max_length=120)
    input_summary: str | None = Field(default=None, alias="inputSummary")
    output_summary: str | None = Field(default=None, alias="outputSummary")
    duration_ms: int | None = Field(default=None, alias="durationMs")
    ok: bool
    error_code: str | None = Field(default=None, alias="errorCode")
    started_at: str = Field(alias="startedAt")


class Engine(StrictModel):
    name: Literal["axe-core"]
    version: str


class Coverage(StrictModel):
    ran: list[str]
    did_not_run: list[str] = Field(alias="didNotRun")
    needs_person: list[str] = Field(alias="needsPerson")


class ScanRequest(StrictModel):
    url: str = Field(min_length=1, max_length=2048)
    consent: bool
    keyboard_walk: bool = Field(default=False, alias="keyboardWalk")


class Scan(StrictModel):
    id: str
    url: str
    working_copy_id: str | None = Field(alias="workingCopyId")
    started_at: str = Field(alias="startedAt")
    duration_ms: int = Field(alias="durationMs")
    title: str
    engine: Engine
    findings: list[Finding]
    pass_count: int = Field(alias="passCount")
    coverage: Coverage
    trace: list[TraceEntry]


class HealthResponse(StrictModel):
    status: Literal["ok"]
    browser_available: bool = Field(alias="browserAvailable")
    model_configured: bool = Field(alias="modelConfigured")
    model_name: str | None = Field(alias="modelName")
    engine_version: str = Field(alias="engineVersion")
