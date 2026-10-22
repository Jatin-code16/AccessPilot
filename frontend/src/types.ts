export type Impact = "critical" | "serious" | "moderate" | "minor";
export type Actor = "scanner" | "agent" | "you" | "retest" | "system";
export type Status = "passed" | "partial" | "failed" | "needs_human";
export type Template = "T1" | "T2" | "T3" | "T4" | "T5";

export interface Finding {
  id: string;
  matchKey: string;
  fingerprint: string;
  source: "axe" | "keyboard";
  kind: "violation" | "incomplete";
  ruleId: string;
  impact: Impact | null;
  help: string;
  helpUrl: string | null;
  tags: string[];
  wcag: string[];
  target: string;
  snippet: string;
  explanation: { who: string; blockedFrom: string; why: string };
  template: Template | null;
  needsHuman: boolean;
}

export interface TraceEntry {
  seq: number;
  actor: Actor;
  name: string;
  summary: string;
  inputSummary?: string;
  outputSummary?: string;
  durationMs?: number;
  ok: boolean;
  errorCode?: string;
  startedAt: string;
}

export interface Scan {
  id: string;
  url: string;
  workingCopyId: string | null;
  startedAt: string;
  durationMs: number;
  title: string;
  engine: { name: "axe-core"; version: string };
  findings: Finding[];
  passCount: number;
  coverage: { ran: string[]; didNotRun: string[]; needsPerson: string[] };
  trace: TraceEntry[];
}

export interface Proposal {
  id: string;
  scanId: string;
  findingId: string;
  template: Template;
  status: "proposed" | "approved" | "rejected" | "skipped" | "applied" | "failed";
  rationale: string;
  risk: "low" | "medium";
  files: string[];
  params: Record<string, string>;
  diff: string;
  diffHash: string;
  proposedBy: "agent" | "builtin";
}

export interface ApplyResult {
  proposalId: string;
  beforeScanId: string;
  afterScanId: string;
  comparison: { resolved: string[]; remaining: string[]; introduced: string[] };
  control: { passed: boolean; newFindings: string[] };
  status: Status;
  reason: string;
  trace: TraceEntry[];
}

export interface AgentRun {
  id: string;
  scanId: string;
  aiUsed: boolean;
  model: string | null;
  fallbackReason: "no_key" | "provider_error" | "bad_output" | "budget_exceeded" | null;
  explanations: Record<string, string>;
  proposals: Proposal[];
  needsHuman: { findingId: string; reason: string }[];
  trace: TraceEntry[];
}

export interface ApiError {
  error: { code: string; message: string };
}

export type WorkbenchStage = "scan" | "review" | "decision" | "retest";
