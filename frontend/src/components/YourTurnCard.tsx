import type { Proposal } from "../types";

export function YourTurnCard({ proposal, approved, busy, onApprove, onSkip, onApply }: { proposal: Proposal; approved: boolean; busy: boolean; onApprove: () => void; onSkip: () => void; onApply: () => void }) {
  return (
    <section className={`decision-card ${approved ? "approved-card" : "draft-card"}`} aria-labelledby="your-turn-title">
      <div className="card-heading">
        <h3 id="your-turn-title">Your turn</h3>
        <span className="draft-label">{approved ? "You approved" : "Draft"}</span>
      </div>
      <p className="impact-line">{proposal.rationale}</p>
      <div className="diff-heading"><span>Proposed change</span><span>{proposal.template}</span></div>
      <pre className="diff"><code>{proposal.diff}</code></pre>
      <dl className="proposal-meta">
        <div><dt>Risk</dt><dd>{proposal.risk}</dd></div>
        <div><dt>File</dt><dd>{proposal.files[0]}</dd></div>
      </dl>
      <div className="card-actions">
        {!approved && <button type="button" className="primary-button" onClick={onApprove}>Approve</button>}
        {approved && <button type="button" className="primary-button" onClick={onApply} disabled={busy}>{busy ? "Applying..." : "Apply to copy"}</button>}
        {!approved && <button type="button" className="secondary-button" onClick={onSkip}>Skip</button>}
      </div>
    </section>
  );
}
