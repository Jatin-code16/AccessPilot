import { useMemo, useState } from "react";
import { fixtureAgentRun, fixtureApplyResult, fixtureScan } from "./fixtures";
import type { AgentRun, ApplyResult, Proposal, Scan, WorkbenchStage } from "./types";

export function useWorkbench() {
  const [scan, setScan] = useState<Scan | null>(null);
  const [agentRun, setAgentRun] = useState<AgentRun | null>(null);
  const [activeProposal, setActiveProposal] = useState<Proposal | null>(null);
  const [approvalToken, setApprovalToken] = useState<string | null>(null);
  const [applyResult, setApplyResult] = useState<ApplyResult | null>(null);
  const [stage, setStage] = useState<WorkbenchStage>("scan");
  const [busy, setBusy] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">("light");

  const log = useMemo(() => [
    ...(scan?.trace ?? []),
    ...(agentRun?.trace ?? []),
    ...(applyResult?.trace ?? []),
  ].sort((left, right) => left.seq - right.seq), [agentRun, applyResult, scan]);

  function startScan() {
    setBusy(true);
    window.setTimeout(() => {
      setScan(fixtureScan);
      setAgentRun(null);
      setActiveProposal(null);
      setApprovalToken(null);
      setApplyResult(null);
      setStage("review");
      setBusy(false);
    }, 350);
  }

  function runFixtureAgent() {
    setBusy(true);
    window.setTimeout(() => {
      setAgentRun(fixtureAgentRun);
      setActiveProposal(fixtureAgentRun.proposals[0] ?? null);
      setStage("decision");
      setBusy(false);
    }, 300);
  }

  function approve() {
    if (!activeProposal) return;
    setApprovalToken(`fixture-token-${activeProposal.id}`);
    setActiveProposal({ ...activeProposal, status: "approved" });
  }

  function skip() {
    if (!activeProposal || !agentRun) return;
    const nextProposal = agentRun.proposals.find((proposal) => proposal.status === "proposed" && proposal.id !== activeProposal.id) ?? null;
    setActiveProposal(nextProposal);
    if (!nextProposal) setStage("retest");
  }

  function apply() {
    if (!activeProposal || !approvalToken) return;
    setBusy(true);
    window.setTimeout(() => {
      setApplyResult({ ...fixtureApplyResult, proposalId: activeProposal.id });
      setStage("retest");
      setBusy(false);
    }, 350);
  }

  return {
    scan, agentRun, activeProposal, approvalToken, applyResult, stage, busy, theme, log,
    setTheme, startScan, runFixtureAgent, approve, skip, apply,
  };
}
