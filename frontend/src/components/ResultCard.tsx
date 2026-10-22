import type { ApplyResult } from "../types";

const statusLabels = { passed: "Passed", partial: "Partly passed", failed: "Failed", needs_human: "Needs a person" };

export function ResultCard({ result }: { result: ApplyResult }) {
  return (
    <section className={`result-card result-${result.status}`} aria-labelledby="result-title">
      <div className="card-heading">
        <h3 id="result-title">Re-test: {statusLabels[result.status]}</h3>
        <span className="status-label">{result.status === "passed" ? "Observed" : "Review"}</span>
      </div>
      <p>{result.reason}</p>
      <dl className="result-counts">
        <div><dt>Resolved</dt><dd>{result.comparison.resolved.length}</dd></div>
        <div><dt>Remaining</dt><dd>{result.comparison.remaining.length}</dd></div>
        <div><dt>New</dt><dd>{result.comparison.introduced.length}</dd></div>
      </dl>
      <p className="control-result">Control page: {result.control.passed ? "no new issues" : "new issues found"}</p>
    </section>
  );
}
