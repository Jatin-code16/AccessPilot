import { useState } from "react";
import type { AgentRun, ApplyResult, Finding, Proposal, Scan, TraceEntry } from "../types";
import { NeedsPersonCard } from "./NeedsPersonCard";
import { ResultCard } from "./ResultCard";
import { YourTurnCard } from "./YourTurnCard";

interface LogProps {
  scan: Scan | null;
  agentRun: AgentRun | null;
  activeProposal: Proposal | null;
  approvalToken: string | null;
  applyResult: ApplyResult | null;
  error: { code: string; message: string } | null;
  log: TraceEntry[];
  busy: boolean;
  onRunAgent: () => void;
  onApprove: () => void;
  onSkip: () => void;
  onApply: () => void;
}

export function Log({ scan, agentRun, activeProposal, approvalToken, applyResult, error, log, busy, onRunAgent, onApprove, onSkip, onApply }: LogProps) {
  const [expanded, setExpanded] = useState<number | null>(null);
  return (
    <section className="log-pane" aria-labelledby="log-title">
      <div className="pane-heading">
        <h2 id="log-title">Log</h2>
        <span>{log.length} recorded steps</span>
      </div>
      {!scan && <p className="system-prompt">Enter a page and confirm you are authorised.</p>}
      {error && <p className="system-error" role="alert">System: {error.message} ({error.code})</p>}
      <ol className="log-list" aria-live="polite">
        {log.map((entry) => (
          <li key={`${entry.seq}-${entry.name}`} className={`log-line actor-${entry.actor}`}>
            <div className="log-summary">
              <span className="actor-tag">{entry.actor === "retest" ? "Re-test" : entry.actor[0].toUpperCase() + entry.actor.slice(1)}</span>
              <span>{entry.summary}</span>
              {entry.durationMs !== undefined && <time>{(entry.durationMs / 1000).toFixed(1)}s</time>}
              {(entry.inputSummary || entry.outputSummary) && (
                <button type="button" className="show-button" aria-expanded={expanded === entry.seq} onClick={() => setExpanded(expanded === entry.seq ? null : entry.seq)}>
                  Show
                </button>
              )}
            </div>
            {expanded === entry.seq && <div className="log-detail"><p>{entry.inputSummary ?? "Step details recorded by the backend."}</p>{entry.outputSummary && <p>{entry.outputSummary}</p>}</div>}
          </li>
        ))}
      </ol>
      {scan && !agentRun && (
        <div className="agent-start">
          <p>Five findings are ready for review.</p>
          <button type="button" className="primary-button" onClick={onRunAgent} disabled={busy}>Run agent</button>
        </div>
      )}
      {agentRun?.fallbackReason && <div className="system-note">No AI model. Using built-in guidance.</div>}
      {activeProposal && (
        <YourTurnCard proposal={activeProposal} approved={approvalToken !== null} busy={busy} onApprove={onApprove} onSkip={onSkip} onApply={onApply} />
      )}
      {agentRun?.needsHuman.map((item) => {
        const finding = scan?.findings.find((candidate) => candidate.id === item.findingId);
        return finding ? <NeedsPersonCard key={item.findingId} finding={finding} reason={item.reason} /> : null;
      })}
      {applyResult && <ResultCard result={applyResult} />}
    </section>
  );
}
