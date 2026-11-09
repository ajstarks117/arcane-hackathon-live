import builds from "./actions-repairs.json";
import cases from "./demo-cases.json";
import token from "./demo-token.json";
import type { Run, Step } from "./api";

export type DemoCase = "token" | keyof typeof cases | keyof typeof builds;
export const recordedBuilds = Object.values(builds);
export type BuildId = keyof typeof builds;
export function buildFromUrl(value: string): BuildId | undefined {
  try {
    const url = new URL(value.trim());
    if (url.origin !== "https://github.com" || url.username || url.password) return;
    return (Object.keys(builds) as BuildId[]).find(id => builds[id].url.toLowerCase() === (url.origin + url.pathname.replace(/\/$/, "")).toLowerCase());
  } catch { return; }
}
export interface Replay { id: string; issue: DemoCase; start: number }
const stageEnds = [3500, 8500, 15000, 19500, 27000, 30000];

export function replayRun(entry: Replay, now: number): Run {
  const data = entry.issue === "token" ? token : entry.issue === "21" || entry.issue === "22" ? cases[entry.issue] : builds[entry.issue];
  const elapsed = Math.max(0, now - entry.start);
  const done = stageEnds.filter(end => elapsed >= end).length;
  const finished = done === stageEnds.length;
  const steps: Step[] = data.steps.map((step, i) => ({
    ...step,
    status: i < done ? (step.status === "failed" ? "failed" : "done") : i === done ? "running" : "pending",
    body: i < done ? step.body : i === done ? "Replaying this stage…" : "Waiting for earlier stages.",
    evidence: i < done ? step.evidence : "",
  }));
  const patchDiff = done >= 3 ? data.patchDiff : "";
  const lines = patchDiff.split("\n");
  const startedAt = new Date(entry.start).toISOString();
  return {
    id: entry.id, source: "demo-replay", repo: "ajstarks117/TEST-REPO", branch: "main",
    sha: "sha" in data ? data.sha : "1e690ab160af391f1223dc0ca46bb75db0cd316a",
    startedAt, finishedAt: finished ? new Date(entry.start + 30000).toISOString() : null,
    status: finished ? "ready" : "working", stage: steps[done]?.title ?? "Done",
    title: data.title, failingTest: data.failingTest, failingFile: data.failingFile,
    failureLog: data.rootCause, rootCause: done ? data.rootCause : "", steps, patchDiff,
    diffSummary: {files: lines.filter(s => s.startsWith("+++ ")).length,
      add: lines.filter(s => s.startsWith("+") && !s.startsWith("+++")).length,
      del: lines.filter(s => s.startsWith("-") && !s.startsWith("---")).length},
    validatorSummary: done >= 5 ? data.validatorSummary : "", testsPassed: done >= 5 ? data.testsPassed : null,
    prUrl: finished ? data.prUrl : null, confidence: finished && "confidence" in data ? data.confidence : null,
    model: "model" in data ? data.model : "", attempts: "attempts" in data ? data.attempts : 0,
    logs: steps.slice(0, done).map((s,i) => ({t:new Date(entry.start + stageEnds[i]).toISOString(), level:"INFO", msg:s.body})),
    logCount: done, commitMessage:"", author:"", workflowRun:"url" in data ? data.url : "", hint:"", failingLine:0, suspectedFunction:"",
    bisectReport:"", cascadeReport:"", autoApproved:false, error:null, memoryHit:false, conflict:null,
    agentsUsed:[], decision:"none", rejectReason:"", assignee:"", reason:"",
  };
}
