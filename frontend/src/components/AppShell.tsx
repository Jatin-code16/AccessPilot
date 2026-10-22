import { useWorkbench } from "../state";
import { Log } from "./Log";
import { PagePane } from "./PagePane";
import { StageDots } from "./StageDots";

export function AppShell() {
  const workbench = useWorkbench();
  const hasScan = workbench.scan !== null;

  return (
    <div className="app-shell" data-theme={workbench.theme}>
      <header className="top-bar">
        <div className="brand-block">
          <p className="eyebrow">Open Workbench</p>
          <h1>AccessPilot</h1>
        </div>
        <div className="scan-controls">
          <label htmlFor="target-url">Page under test</label>
          <input id="target-url" defaultValue="http://127.0.0.1:8000/sites/original/golden/index.html" />
          <label className="consent-label">
            <input type="checkbox" defaultChecked />
            I&apos;m authorised
          </label>
          <button type="button" className="primary-button" onClick={workbench.startScan} disabled={workbench.busy}>
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
