import type { Scan } from "../types";

export function PagePane({ scan }: { scan: Scan | null }) {
  return (
    <section className="page-pane" aria-labelledby="page-pane-title">
      <div className="pane-heading">
        <h2 id="page-pane-title">The real page</h2>
        <span>{scan ? scan.title : "Waiting for a scan"}</span>
      </div>
      {scan ? (
        <div className="demo-page">
          <p className="demo-kicker">College scholarship form</p>
          <h3>Tell us about your study plans</h3>
          <p className="demo-copy">Complete the form to apply for support.</p>
          <div className="demo-field">
            <span className="fake-input">{scan.findings[0]?.target ?? "#email"}</span>
            <span className="finding-mark">1</span>
          </div>
          <div className="demo-field image-field">
            <span className="fake-image">Campus photo</span>
            <span className="finding-mark">2</span>
          </div>
          <p className="demo-helper">
            Required fields
            <span className="finding-mark">3</span>
          </p>
          <button type="button" className="demo-submit">Submit application</button>
          <span className="finding-mark button-mark">5</span>
          <div className="demo-help">Need help?</div>
        </div>
      ) : (
        <div className="empty-page">
          <p>Enter a page and start a scan.</p>
          <p>The checked page will appear here.</p>
        </div>
      )}
      <div className="overlay-note" aria-hidden="true">Boxes mark checked elements.</div>
    </section>
  );
}
