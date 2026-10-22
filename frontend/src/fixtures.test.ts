import { describe, expect, it } from "vitest";
import { fixtureAgentRun, fixtureApplyResult, fixtureScan } from "./fixtures";

describe("frontend integration fixtures", () => {
  it("uses the shared scan shape and bounded finding snippets", () => {
    expect(fixtureScan.engine.name).toBe("axe-core");
    expect(fixtureScan.findings.length).toBeGreaterThan(0);
    expect(fixtureScan.findings.every((finding) => finding.snippet.length <= 300)).toBe(true);
    expect(fixtureScan.findings.every((finding) => finding.matchKey.includes("|"))).toBe(true);
  });

  it("keeps unsupported findings in the needs-person collection", () => {
    expect(fixtureAgentRun.proposals.every((proposal) => proposal.template !== undefined)).toBe(true);
    expect(fixtureAgentRun.needsHuman).toHaveLength(1);
    expect(fixtureAgentRun.proposals.some((proposal) => proposal.findingId === "finding-clickable-div")).toBe(false);
  });

  it("renders only verifier status values", () => {
    expect(["passed", "partial", "failed", "needs_human"]).toContain(fixtureApplyResult.status);
    expect(fixtureApplyResult.comparison.introduced).toHaveLength(0);
  });
});
