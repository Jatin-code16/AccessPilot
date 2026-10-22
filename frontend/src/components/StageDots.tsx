import type { WorkbenchStage } from "../types";

const stages: { id: WorkbenchStage; label: string }[] = [
  { id: "scan", label: "Scan" },
  { id: "review", label: "Review" },
  { id: "decision", label: "Your decision" },
  { id: "retest", label: "Re-test" },
];

export function StageDots({ current }: { current: WorkbenchStage }) {
  const currentIndex = stages.findIndex((stage) => stage.id === current);
  return (
    <nav className="stage-nav" aria-label="Workbench stages">
      <ol>
        {stages.map((stage, index) => (
          <li key={stage.id} className={index <= currentIndex ? "stage-complete" : ""}>
            <span aria-hidden="true" className="stage-dot" />
            <span aria-current={stage.id === current ? "step" : undefined}>{stage.label}</span>
          </li>
        ))}
      </ol>
    </nav>
  );
}
