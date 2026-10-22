import type { AgentRun, ApiError, ApplyResult, Proposal, Scan } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  const body: unknown = await response.json();
  if (!response.ok) {
    const apiError = body as ApiError;
    const error = new Error(apiError.error?.message ?? "The request could not finish.");
    Object.assign(error, { code: apiError.error?.code ?? "request_failed" });
    throw error;
  }
  return body as T;
}

export function getScan(scanId: string): Promise<Scan> {
  return request<Scan>(`/api/scans/${scanId}`);
}

export function createScan(url: string, consent: boolean): Promise<Scan> {
  return request<Scan>("/api/scans", {
    method: "POST",
    body: JSON.stringify({ url, consent }),
  });
}

export function runAgent(scanId: string, mode: "auto" | "builtin" = "auto"): Promise<AgentRun> {
  return request<AgentRun>(`/api/scans/${scanId}/agent`, {
    method: "POST",
    body: JSON.stringify({ mode }),
  });
}

export function getProposal(proposalId: string): Promise<Proposal> {
  return request<Proposal>(`/api/proposals/${proposalId}`);
}

export function editProposal(proposalId: string, params: Record<string, string>): Promise<Proposal> {
  return request<Proposal>(`/api/proposals/${proposalId}`, {
    method: "PATCH",
    body: JSON.stringify({ params }),
  });
}

export function approveProposal(proposalId: string): Promise<{ proposalId: string; token: string; diffHash: string; expiresAt: string }> {
  return request(`/api/proposals/${proposalId}/approve`, { method: "POST" });
}

export function skipProposal(proposalId: string): Promise<Proposal> {
  return request<Proposal>(`/api/proposals/${proposalId}/skip`, { method: "POST" });
}

export function applyProposal(proposalId: string, token: string): Promise<ApplyResult> {
  return request<ApplyResult>(`/api/proposals/${proposalId}/apply`, {
    method: "POST",
    body: JSON.stringify({ token }),
  });
}
