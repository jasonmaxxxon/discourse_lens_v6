import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Activity, Brain, Check, CheckCircle, Database, Eye, Globe, Loader2 } from "lucide-react";

type JobItemStatus = "pending" | "processing" | "completed" | "failed" | string;
type JobStage = "init" | "fetch" | "vision" | "analyst" | "store" | "completed" | string;

export type JobBatchSummary = {
  status?: string;
  total_count?: number;
  success_count?: number;
  fail_count?: number;
  last_heartbeat_at?: string;
};

type JobItem = {
  id?: string;
  target_id: string;
  stage: JobStage;
  status: JobItemStatus;
  updated_at?: string;
  result_post_id?: string;
  error_log?: string;
  meta?: Record<string, any>;
};

type CompletedPost = { postId: string; target?: string; status?: string };

const STAGES: JobStage[] = ["fetch", "vision", "analyst", "store"];

export function JobExecutionMonitor({
  jobId,
  onJobLoaded,
  onCompleted,
  onReset,
  onBack,
}: {
  jobId: string;
  onJobLoaded?: (summary: JobBatchSummary | null) => void;
  onCompleted?: (summary: JobBatchSummary | null) => void;
  onReset?: () => void;
  onBack?: () => void;
}) {
  const [item, setItem] = useState<JobItem | null>(null);
  const [summary, setSummary] = useState<JobBatchSummary | null>(null);
  const [completedPosts, setCompletedPosts] = useState<CompletedPost[]>([]);
  const [elapsed, setElapsed] = useState("0.0s");
  const [finalDuration, setFinalDuration] = useState<string | null>(null);
  const [logLines, setLogLines] = useState<string[]>([]);

  const startTimeRef = useRef<number>(Date.now());
  const pollRef = useRef<ReturnType<typeof window.setTimeout> | null>(null);
  const stopwatchRef = useRef<ReturnType<typeof window.setInterval> | null>(null);
  const lastStageRef = useRef<string>("");
  const completedPostsRef = useRef<CompletedPost[]>([]);

  const timerMs = 100;

  useEffect(() => {
    setItem(null);
    setSummary(null);
    setCompletedPosts([]);
    completedPostsRef.current = [];
    setFinalDuration(null);
    setElapsed("0.0s");
    startTimeRef.current = Date.now();
  }, [jobId]);

  const stageIndex = useMemo(() => {
    const s = item?.stage;
    const idx = STAGES.indexOf(s as JobStage);
    return idx < 0 ? 0 : idx;
  }, [item?.stage]);

  const progressPct = useMemo(() => {
    if (!item) return 0;
    if (item.status === "completed") return 100;
    const map: Record<string, number> = { fetch: 25, vision: 50, analyst: 75, store: 95 };
    return map[String(item.stage)] ?? 10;
  }, [item]);

  const mergeCompletedPosts = useCallback((itemsList: JobItem[]) => {
    const next = itemsList
      .map((it) => {
        const postId = (it as any).result_post_id ?? (it as any).meta?.result_post_id;
        if (!postId) return null;
        return { postId: String(postId), target: it.target_id, status: it.status } as CompletedPost;
      })
      .filter(Boolean) as CompletedPost[];

    if (!next.length) return completedPostsRef.current;

    const seen = new Set<string>();
    const merged: CompletedPost[] = [];
    for (const entry of [...completedPostsRef.current, ...next]) {
      if (seen.has(entry.postId)) continue;
      seen.add(entry.postId);
      merged.push(entry);
    }

    completedPostsRef.current = merged;
    setCompletedPosts(merged);
    return merged;
  }, []);

  // Poll items + stopwatch (stop on terminal state)
  useEffect(() => {
    if (!jobId) return;

    const start = startTimeRef.current;

    const stopAll = () => {
      if (pollRef.current) window.clearTimeout(pollRef.current);
      if (stopwatchRef.current) window.clearInterval(stopwatchRef.current);
      pollRef.current = null;
      stopwatchRef.current = null;
    };

    const computeDelay = (stage?: string, status?: string) => {
      const terminal = status === "completed" || status === "failed";
      if (terminal) return null;
      if (stage === "analyst" || stage === "store") return 2200;
      return 1400;
    };

    const poll = async () => {
      try {
        const [itemsRes, summaryRes] = await Promise.allSettled([
          fetch(`/api/jobs/${jobId}/items`, { cache: "no-store" }),
          fetch(`/api/jobs/${jobId}/summary`, { cache: "no-store" }),
        ]);

        if (summaryRes.status === "fulfilled" && summaryRes.value.ok) {
          const summaryPayload = await summaryRes.value.json();
          setSummary(summaryPayload);
          onJobLoaded?.(summaryPayload);
        }

        let itemsPayload: JobItem[] = [];
        if (itemsRes.status === "fulfilled" && itemsRes.value.ok) {
          const raw = await itemsRes.value.json();
          itemsPayload = (Array.isArray(raw) ? raw : raw?.items || raw?.data || []) as JobItem[];
        }

        if (!itemsPayload.length) {
          const fallbackRes = await fetch(`/api/jobs/${jobId}`, { cache: "no-store" });
          if (fallbackRes.ok) {
            const data = await fallbackRes.json();
            const arr = (Array.isArray(data?.items) ? data.items : data?.data || []) as JobItem[];
            itemsPayload = arr;
            if (data && !Array.isArray(data) && data.status) {
              setSummary((prev) => data ?? prev);
              onJobLoaded?.((data as any) ?? null);
            }
          }
        }

        if (itemsPayload.length) {
          mergeCompletedPosts(itemsPayload);
          const next = itemsPayload[0];
          if (next) {
            setItem(next);
            if (next.status === "completed" || next.status === "failed") {
              stopAll();
              setFinalDuration(((Date.now() - start) / 1000).toFixed(1) + "s");
              onCompleted?.(summary ?? null);
              return;
            }
          }
        }
      } catch (e) {
        console.error("Polling failed", e);
      }

      // Schedule next poll
      const delay = computeDelay(item?.stage, item?.status);
      if (delay !== null) {
        pollRef.current = window.setTimeout(poll, delay);
      }
    };

    poll();

    stopwatchRef.current = window.setInterval(() => {
      setElapsed(((Date.now() - start) / 1000).toFixed(1) + "s");
    }, timerMs);

    return () => stopAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId, mergeCompletedPosts]);

  // Live log lines (stage-driven)
  useEffect(() => {
    if (!item) return;

    const stage = String(item.stage || "");
    const status = String(item.status || "");

    setLogLines((prev) => {
      const next = [...prev];

      const appendOnce = (key: string, line: string) => {
        if (!next.some((l) => l.includes(key))) next.push(line);
      };

      appendOnce("INIT_ENGINE", `> Initializing analysis engine... <b class="text-emerald-500">[OK]</b>`);

      if (stage === "fetch") appendOnce("FETCH_RUN", `> Fetching target URL content... <b class="text-amber-500 animate-pulse">[RUNNING]</b>`);
      if (stage === "vision") {
        appendOnce("FETCH_OK", `> Fetching target URL content... <b class="text-emerald-500">[SUCCESS]</b>`);
        appendOnce("VISION_RUN", `> Detecting visual elements... <b class="text-amber-500 animate-pulse">[RUNNING]</b>`);
      }
      if (stage === "analyst") {
        appendOnce("VISION_DONE", `> Detecting visual elements... <b class="text-blue-500">[DONE]</b>`);
        appendOnce("ANALYST_RUN", `> Generating narrative insights... <b class="text-amber-500 animate-pulse">[RUNNING]</b>`);
      }
      if (stage === "store") {
        appendOnce("ANALYST_DONE", `> Generating narrative insights... <b class="text-blue-500">[DONE]</b>`);
        appendOnce("STORE_RUN", `> Finalizing and storing report... <b class="text-amber-500 animate-pulse">[RUNNING]</b>`);
      }

      if (status === "completed") {
        appendOnce("STORE_DONE", `> Finalizing and storing report... <b class="text-emerald-500">[DONE]</b>`);
        appendOnce("COMPLETE", `> Pipeline completed. Standing by for your action.`);
      }

      if (status === "failed") {
        appendOnce("FAILED", `> Pipeline failed at <b class="text-red-500">${stage}</b>.`);
      }

      lastStageRef.current = stage;
      return next;
    });
  }, [item?.stage, item?.status]);

  const getStepStatus = (step: JobStage): "pending" | "active" | "done" | "error" => {
    if (!item) return "pending";
    if (item.status === "failed") return step === item.stage ? "error" : "pending";
    if (item.status === "completed") return "done";

    const cur = STAGES.indexOf(item.stage as JobStage);
    const idx = STAGES.indexOf(step as JobStage);
    if (cur > idx) return "done";
    if (cur === idx) return "active";
    return "pending";
  };

  if (!jobId) {
    return (
      <div className="min-h-[200px] flex items-center justify-center bg-[#0f172a] text-white/70 rounded-xl border border-white/10">
        Missing jobId
      </div>
    );
  }

  if (!item) {
    return (
      <div className="min-h-[200px] flex flex-col items-center justify-center bg-[#0f172a] text-white rounded-xl border border-white/10 p-6 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
        <div className="text-sm text-white/60">Awaiting first job item…</div>
      </div>
    );
  }

  return (
    <div className="bg-[#0f172a] text-white rounded-2xl border border-white/10 shadow-2xl shadow-black/30 overflow-hidden">
      <div className="p-8 border-b border-white/10 bg-white/5">
        <label className="block text-xs font-bold text-white/60 uppercase tracking-wider mb-2">Target Source</label>
        <div className="flex items-center gap-3 text-white font-mono text-sm bg-[#0b1323] p-4 rounded-lg border border-white/10 shadow-sm">
          <span className="material-symbols-outlined text-[18px] text-white/50">link</span>
          <span className="truncate">{item.target_id}</span>
        </div>

        <div className="mt-4 flex flex-wrap gap-3 text-xs text-white/70">
          <span className="px-3 py-1 rounded-full bg-white/5 border border-white/10">
            status: <b className="text-white">{String(item.status)}</b>
          </span>
          <span className="px-3 py-1 rounded-full bg-white/5 border border-white/10">
            stage: <b className="text-white">{String(item.stage)}</b>
          </span>
          <span className="px-3 py-1 rounded-full bg-white/5 border border-white/10">
            elapsed: <b className="text-white">{finalDuration ?? elapsed}</b>
          </span>
          {summary?.success_count != null && (
            <span className="px-3 py-1 rounded-full bg-white/5 border border-white/10">
              ok: <b className="text-white">{summary.success_count}</b>
            </span>
          )}
          {summary?.fail_count != null && (
            <span className="px-3 py-1 rounded-full bg-white/5 border border-white/10">
              fail: <b className="text-white">{summary.fail_count}</b>
            </span>
          )}
        </div>
      </div>

      <div className="p-8">
        <div className="relative flex justify-between items-start max-w-3xl mx-auto">
          <div className="absolute top-5 left-0 w-full h-1 bg-white/10 rounded-full -z-10" />
          <div className="absolute top-5 left-0 h-1 bg-blue-500 rounded-full -z-0 transition-all duration-700 ease-out" style={{ width: `${progressPct}%` }} />

          <StepIndicator status={getStepStatus("fetch")} icon={Globe} label="Fetch" sub={getStepStatus("fetch") === "active" ? (finalDuration ?? elapsed) : ""} />
          <StepIndicator status={getStepStatus("vision")} icon={Eye} label="Vision" sub={getStepStatus("vision") === "active" ? "Analyzing..." : ""} />
          <StepIndicator status={getStepStatus("analyst")} icon={Brain} label="Analyst" sub={getStepStatus("analyst") === "active" ? "Thinking..." : ""} />
          <StepIndicator status={getStepStatus("store")} icon={Database} label="Store" sub={getStepStatus("store") === "active" ? "Writing..." : ""} />
        </div>

        {completedPosts.length > 0 && (
          <div className="mt-10 border border-dashed border-white/10 rounded-xl p-4 bg-white/5">
            <div className="flex items-center justify-between mb-3">
              <div className="text-xs font-bold uppercase tracking-widest text-white/70">Completed so far</div>
              <span className="text-[11px] text-white/60 font-mono">{completedPosts.length} posts</span>
            </div>
            <div className="space-y-2">
              {completedPosts.map((p) => (
                <div key={p.postId} className="flex items-center justify-between gap-3 px-3 py-2 rounded-lg bg-[#0b1323] border border-white/10">
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="p-2 rounded-md bg-blue-900/40 text-blue-200 material-symbols-outlined text-[16px]">link</span>
                    <div className="min-w-0">
                      <div className="font-mono text-sm text-white truncate">#{p.postId}</div>
                      <div className="text-xs text-white/60 truncate">{p.target || "Report ready"}</div>
                    </div>
                  </div>
                  <span className="text-[11px] px-2 py-1 rounded-full bg-white/10 text-white/80 border border-white/10">{p.status || "ready"}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {item.status === "completed" && (
          <div className="mt-10 flex flex-col items-center gap-4">
            <div className="flex items-center gap-2 text-emerald-300 bg-emerald-900/30 px-5 py-2 rounded-full border border-emerald-800 shadow-sm">
              <CheckCircle className="w-5 h-5" />
              <span className="font-bold">Analysis Complete</span>
            </div>
            <p className="text-white/60 text-sm">Report ready. Choose what to do next.</p>
            <div className="flex flex-wrap items-center justify-center gap-3">
              <button className="px-4 py-2 rounded-lg bg-white/10 text-white text-sm font-semibold opacity-60 cursor-not-allowed" disabled title="Coming soon">
                View Analysis (soon)
              </button>
              <button
                onClick={() => {
                  if (jobId) navigator.clipboard?.writeText(jobId).catch(() => undefined);
                }}
                className="px-4 py-2 rounded-lg bg-white text-slate-900 text-sm font-semibold border border-white shadow-sm hover:bg-slate-50"
              >
                Copy Job ID
              </button>
              <button
                onClick={() => onReset?.()}
                className="px-4 py-2 rounded-lg bg-white/10 text-white text-sm font-semibold border border-white/20 hover:bg-white/15"
              >
                Reset / New Job
              </button>
              <button
                onClick={() => onBack?.()}
                className="px-4 py-2 rounded-lg bg-white/5 text-white text-sm font-semibold border border-white/10 hover:bg-white/10"
              >
                Back to Dashboard
              </button>
            </div>
          </div>
        )}

        {item.status === "failed" && (
          <div className="mt-10 flex flex-col items-center gap-4 text-red-300">
            <div className="p-3 bg-red-900/40 rounded-full">
              <Activity className="w-8 h-8" />
            </div>
            <div className="text-center">
              <h3 className="font-bold text-lg">Analysis Failed</h3>
              <p className="text-sm opacity-80 mt-1 max-w-2xl break-words">{item.error_log || "Unknown error occurred"}</p>
            </div>
            <button onClick={() => onBack?.()} className="px-6 py-2 bg-white/10 rounded-lg text-sm font-bold text-white hover:bg-white/15">
              Back to Dashboard
            </button>
          </div>
        )}
      </div>

      <div className="bg-[#0b1323] border-t border-white/10 p-6">
        <div className="flex items-center justify-between mb-4 px-2">
          <h3 className="text-xs font-bold text-white/60 uppercase tracking-widest flex items-center gap-2">
            <Activity className="w-3 h-3" /> Live Execution Log
          </h3>
          <span className="text-[10px] font-mono text-white/50">
            STAGE: {String(item.stage)} / STATUS: {String(item.status)}
          </span>
        </div>

        <div className="bg-[#0f172a] rounded-xl border border-white/10 p-4 h-44 overflow-y-auto font-mono text-xs shadow-inner">
          <ul className="space-y-2">
            {logLines.map((l, i) => (
              <li key={i} className="flex gap-2 text-white/70">
                <span className="text-white/30 select-none">&gt;</span>
                <span
                  dangerouslySetInnerHTML={{
                    __html: l,
                  }}
                />
              </li>
            ))}
            {item.status === "processing" && (
              <li className="flex gap-2 text-white/50 animate-pulse">
                <span className="text-white/30">&gt;</span>
                <span className="w-2 h-4 bg-white/20 block"></span>
              </li>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
}

function StepIndicator({
  status,
  icon: Icon,
  label,
  sub,
}: {
  status: "pending" | "active" | "done" | "error";
  icon: any;
  label: string;
  sub?: string;
}) {
  const baseClasses = "relative z-10 flex flex-col items-center transition-all duration-500";
  const circleBase = "w-12 h-12 rounded-full flex items-center justify-center shadow-lg ring-4 transition-all duration-500";

  const styles = {
    pending: {
      circle: "bg-[#0f172a] text-white/30 ring-transparent shadow-none border-2 border-white/10",
      text: "text-white/50",
      icon: <Icon className="w-5 h-5" />,
    },
    active: {
      circle: "bg-blue-500 text-white ring-blue-900/40 scale-110 shadow-blue-500/30",
      text: "text-blue-200 font-bold",
      icon: <Loader2 className="w-5 h-5 animate-spin" />,
    },
    done: {
      circle: "bg-blue-500 text-white ring-white/10",
      text: "text-white/80 font-medium",
      icon: <Check className="w-6 h-6" />,
    },
    error: {
      circle: "bg-red-500 text-white ring-red-900/30",
      text: "text-red-300 font-bold",
      icon: <Activity className="w-6 h-6" />,
    },
  } as const;

  const s = styles[status];

  return (
    <div className={baseClasses}>
      <div className={`${circleBase} ${s.circle}`}>{s.icon}</div>
      <div className="mt-4 text-center space-y-0.5">
        <p className={`text-sm ${s.text}`}>{label}</p>
        {sub && <p className="text-xs text-white/50 font-mono">{sub}</p>}
      </div>
    </div>
  );
}
