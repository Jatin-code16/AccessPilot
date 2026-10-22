import type { Finding } from "../types";

export function NeedsPersonCard({ finding, reason }: { finding: Finding; reason: string }) {
  return (
    <section className="decision-card needs-person-card" aria-labelledby={`needs-${finding.id}`}>
      <div className="card-heading">
        <h3 id={`needs-${finding.id}`}>Needs a person</h3>
        <span className="status-label">Review</span>
      </div>
      <p>{reason}</p>
      <dl className="finding-meta">
        <div><dt>What was found</dt><dd>{finding.help}</dd></div>
        <div><dt>Where</dt><dd><code>{finding.target}</code></dd></div>
      </dl>
      <button type="button" className="secondary-button">Mark as noted</button>
    </section>
  );
}
