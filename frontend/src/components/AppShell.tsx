import { useState } from "react";
import { useWorkbench } from "../state";
import { Log } from "./Log";
import { PagePane } from "./PagePane";
import { StageDots } from "./StageDots";

export function AppShell() {
  const workbench = useWorkbench();
  const hasScan = workbench.scan !== null;
  const [url, setUrl] = useState("http://127.0.0.1:8000/sites/original/golden/index.html");
  const [consent, setConsent] = useState(false);

  return (
    <div className="app-shell" data-theme={workbench.theme}>
      <header className="top-bar">
        <div className="brand-block">
          <p className="eyebrow">Open Workbench</p>
          <h1>AccessPilot</h1>
        </div>
        <div className="scan-controls">
          <label htmlFor="target-url">Page under test</label>
          <input id="target-url" value={url} onChange={(event) => setUrl(event.target.value)} />
          <label className="consent-label">
            <input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} />
            I&apos;m authorised
          </label>
          <button type="button" className="primary-button" onClick={() => void workbench.startScan(url, consent)} disabled={workbench.busy || !consent}>
            {workbench.busy && !hasScan ? "Scanning..." : "Scan"}
          </button>
        </div>
        <div className="more-menu">
          <button type="button" className="secondary-button">More</button>
          <div className="menu-panel">
            <button type="button">Coverage</button>
            <button type="button">Keyboard path</button>
            <button type="button">Export</button>
            <button type="button" onClick={() => workbench.setTheme(workbench.theme === "light" ? "dark" : "light")}>
              {workbench.theme === "light" ? "Dark theme" : "Light theme"}
            </button>
          </div>
        </div>
      </header>
      <StageDots current={workbench.stage} />
      <main className="workbench">
        <PagePane scan={workbench.scan} />
        <Log
          scan={workbench.scan}
          agentRun={workbench.agentRun}
          activeProposal={workbench.activeProposal}
          approvalToken={workbench.approvalToken}
          applyResult={workbench.applyResult}
          error={workbench.error}
          log={workbench.log}
          busy={workbench.busy}
          onRunAgent={workbench.runFixtureAgent}
          onApprove={workbench.approve}
          onSkip={workbench.skip}
          onApply={workbench.apply}
        />
      </main>
    </div>
  );
}
