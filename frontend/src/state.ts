import { useMemo, useState } from "react";
import { fixtureAgentRun, fixtureApplyResult, fixtureScan } from "./fixtures";
import { applyProposal, approveProposal, createScan, runAgent } from "./api/client";
import type { AgentRun, ApplyResult, Proposal, Scan, WorkbenchStage } from "./types";

const useFixtures = import.meta.env.VITE_USE_FIXTURES !== "false";

export function useWorkbench() {
  const [scan, setScan] = useState<Scan | null>(null);
  const [agentRun, setAgentRun] = useState<AgentRun | null>(null);
  const [activeProposal, setActiveProposal] = useState<Proposal | null>(null);
  const [approvalToken, setApprovalToken] = useState<string | null>(null);
  const [applyResult, setApplyResult] = useState<ApplyResult | null>(null);
  const [stage, setStage] = useState<WorkbenchStage>("scan");
  const [busy, setBusy] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [error, setError] = useState<{ code: string; message: string } | null>(null);

  const log = useMemo(() => [
    ...(scan?.trace ?? []),
    ...(agentRun?.trace ?? []),
    ...(applyResult?.trace ?? []),
  ].sort((left, right) => left.seq - right.seq), [agentRun, applyResult, scan]);

  async function startScan(url: string, consent: boolean) {
    setBusy(true);
    setError(null);
    if (useFixtures) {
      window.setTimeout(() => {
        setScan(fixtureScan);
        setAgentRun(null);
        setActiveProposal(null);
        setApprovalToken(null);
        setApplyResult(null);
        setStage("review");
        setBusy(false);
      }, 350);
      return;
    }
    try {
      setScan(await createScan(url, consent));
      setAgentRun(null);
      setActiveProposal(null);
      setApprovalToken(null);
      setApplyResult(null);
      setStage("review");
    } catch (caught) {
      const requestError = caught as Error & { code?: string };
      setError({ code: requestError.code ?? "request_failed", message: requestError.message });
    } finally {
      setBusy(false);
    }
  }

  async function runFixtureAgent() {
    setBusy(true);
    setError(null);
    if (useFixtures) {
      window.setTimeout(() => {
        setAgentRun(fixtureAgentRun);
        setActiveProposal(fixtureAgentRun.proposals[0] ?? null);
        setStage("decision");
        setBusy(false);
      }, 300);
      return;
    }
    try {
      if (!scan) return;
      const response = await runAgent(scan.id);
      setAgentRun(response);
      setActiveProposal(response.proposals[0] ?? null);
      setStage("decision");
    } catch (caught) {
      const requestError = caught as Error & { code?: string };
      setError({ code: requestError.code ?? "request_failed", message: requestError.message });
    } finally {
      setBusy(false);
    }
  }

  async function approve() {
    if (!activeProposal) return;
    setError(null);
    if (useFixtures) {
      setApprovalToken(`fixture-token-${activeProposal.id}`);
      setActiveProposal({ ...activeProposal, status: "approved" });
      return;
    }
    try {
      const approval = await approveProposal(activeProposal.id);
      setApprovalToken(approval.token);
      setActiveProposal({ ...activeProposal, status: "approved" });
    } catch (caught) {
      const requestError = caught as Error & { code?: string };
      setError({ code: requestError.code ?? "request_failed", message: requestError.message });
    }
  }

  function skip() {
    if (!activeProposal || !agentRun) return;
    const nextProposal = agentRun.proposals.find((proposal) => proposal.status === "proposed" && proposal.id !== activeProposal.id) ?? null;
    setActiveProposal(nextProposal);
    if (!nextProposal) setStage("retest");
  }

  async function apply() {
    if (!activeProposal || !approvalToken) return;
    setBusy(true);
    setError(null);
    if (useFixtures) {
      window.setTimeout(() => {
        setApplyResult({ ...fixtureApplyResult, proposalId: activeProposal.id });
        setStage("retest");
        setBusy(false);
      }, 350);
      return;
    }
    try {
      setApplyResult(await applyProposal(activeProposal.id, approvalToken));
      setStage("retest");
    } catch (caught) {
      const requestError = caught as Error & { code?: string };
      setError({ code: requestError.code ?? "request_failed", message: requestError.message });
    } finally {
      setBusy(false);
    }
  }

  return {
    scan, agentRun, activeProposal, approvalToken, applyResult, stage, busy, theme, log, error,
    setTheme, startScan, runFixtureAgent, approve, skip, apply,
  };
}
