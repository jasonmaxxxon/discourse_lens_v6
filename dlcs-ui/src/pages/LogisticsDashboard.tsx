import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import PipelineActionPanel from "../components/PipelineActionPanel";

type Job = {
  id: string;
  pipeline_type: string;
  status: string;
  total_count?: number;
  processed_count?: number;
  success_count?: number;
  failed_count?: number;
  created_at?: string;
  last_heartbeat_at?: string | null;
};

type JobItem = {
  id: string;
  target_id: string;
  stage?: string;
  status?: string;
  result_post_id?: string | null;
  error_log?: string | null;
  updated_at?: string;
};

type JobSummary = {
  job_id: string;
  pipeline_type?: string;
  status?: string;
  total_count?: number;
  processed_count?: number;
  success_count?: number;
  failed_count?: number;
  last_item_updated_at?: string | null;
  last_heartbeat_at?: string | null;
  degraded?: boolean;
};

const API_BASE = "/api/jobs";
// Polling intervals (ms); increase to reduce Supabase/API load.
const INTERVAL_ACTIVE = 6000;
const INTERVAL_IDLE = 15000;

function normalizePipelineCode(v?: string | null) {
  const s = (v || "").trim().toUpperCase();
  if (!s) return "";
  const m = s.match(/([A-Z])/);
  return m ? m[1] : s;
}

function signatureOf(item: JobItem) {
  return [item.stage || item.status || "", item.status || "", item.error_log || ""].join("|");
}

export default function LogisticsDashboard() {
  // ----------------------------
  // 1) Raw inputs (URL params) + state
  // ----------------------------
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const pipelineQuery = normalizePipelineCode(searchParams.get("pipeline"));

  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [items, setItems] = useState<JobItem[]>([]);
  const [summary, setSummary] = useState<JobSummary | null>(null);
  const [online, setOnline] = useState(true);
  const [degraded, setDegraded] = useState(false);
  const [loading, setLoading] = useState(false);

  const timeoutRef = useRef<number | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const isPollingRef = useRef(false);
  const selectedJobIdRef = useRef<string | null>(null);
  const lastGoodJobs = useRef<Job[]>([]);
  const lastGoodItems = useRef<JobItem[]>([]);
  const lastGoodSummary = useRef<JobSummary | null>(null);
  const prevItemsRef = useRef<Record<string, string>>({});
  const [flashIds, setFlashIds] = useState<Record<string, number>>({});

  // ----------------------------
  // 2) Derived data MUST be defined before any handler uses them (TDZ-safe)
  // ----------------------------
  const visibleJobs = useMemo(() => {
    if (!pipelineQuery) return jobs;
    return jobs.filter((j) => normalizePipelineCode(j.pipeline_type) === pipelineQuery);
  }, [jobs, pipelineQuery]);

  const runningCount = useMemo(
    () => visibleJobs.filter((j) => (j.status || "").toLowerCase() === "processing").length,
    [visibleJobs]
  );

  useEffect(() => {
    selectedJobIdRef.current = selectedJobId;
  }, [selectedJobId]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const queryJobId = params.get("job_id");
    if (queryJobId) setSelectedJobId(queryJobId);
  }, []);

  const clearTimersAndAbort = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
  }, []);

  const fetchJobs = useCallback(async (controller: AbortController) => {
    const res = await fetch(`${API_BASE}/`, { signal: controller.signal });
    if (!res.ok) throw new Error(`jobs fetch failed (${res.status})`);
    const degradedHeader = res.headers.get("x-ops-degraded") === "1";
    const data = (await res.json()) as Job[];
    if (degradedHeader && data.length === 0) {
      setDegraded(true);
      return lastGoodJobs.current;
    }
    setDegraded(degradedHeader);
    setJobs(data);
    lastGoodJobs.current = data;

    // DO NOT auto-select here (selection depends on filtering).
    return data;
  }, []);

  const fetchItems = useCallback(async (jobId: string, controller: AbortController) => {
    const res = await fetch(`${API_BASE}/${jobId}/items`, { signal: controller.signal });
    if (!res.ok) throw new Error(`items fetch failed (${res.status})`);
    const degradedHeader = res.headers.get("x-ops-degraded") === "1";
    const data = (await res.json()) as JobItem[];
    if (degradedHeader && data.length === 0) {
      setDegraded(true);
      return lastGoodItems.current;
    }
    setDegraded((prev) => prev || degradedHeader);
    setItems(data);
    lastGoodItems.current = data;

    const nextFlash: Record<string, number> = {};
    const prev = prevItemsRef.current;
    for (const it of data) {
      const sig = signatureOf(it);
      if (prev[it.id] && prev[it.id] !== sig) {
        nextFlash[it.id] = Date.now();
      }
      prev[it.id] = sig;
    }
    if (Object.keys(nextFlash).length) {
      setFlashIds((old) => ({ ...old, ...nextFlash }));
      window.setTimeout(() => {
        setFlashIds((old) => {
          const copy = { ...old };
          for (const id of Object.keys(nextFlash)) delete copy[id];
          return copy;
        });
      }, 2000);
    }
    return data;
  }, []);

  const fetchSummary = useCallback(async (jobId: string, controller: AbortController) => {
    const res = await fetch(`${API_BASE}/${jobId}/summary`, { signal: controller.signal });
    if (!res.ok) throw new Error(`summary fetch failed (${res.status})`);
    const degradedHeader = res.headers.get("x-ops-degraded") === "1";
    const data = (await res.json()) as JobSummary;
    if (degradedHeader && !data) {
      setDegraded(true);
      return lastGoodSummary.current;
    }
    setDegraded((prev) => prev || degradedHeader);
    setSummary(data);
    lastGoodSummary.current = data;
    setOnline(!data?.degraded);
    return data;
  }, []);

  // ----------------------------
  // 3) Polling
  // ----------------------------
  const poll = useCallback(async () => {
    if (isPollingRef.current) return;
    isPollingRef.current = true;
    setLoading(true);
    clearTimersAndAbort();
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      await fetchJobs(controller);
      const currentJobId = selectedJobIdRef.current;
      if (currentJobId) {
        await fetchSummary(currentJobId, controller);
        await fetchItems(currentJobId, controller);
      } else {
        setItems([]);
        setSummary(null);
      }
    } catch (e) {
      // fall back to idle polling
    } finally {
      setLoading(false);
      isPollingRef.current = false;
      const delay = document.hidden ? INTERVAL_IDLE : INTERVAL_ACTIVE;
      timeoutRef.current = window.setTimeout(() => void poll(), delay);
    }
  }, [clearTimersAndAbort, fetchItems, fetchJobs, fetchSummary]);

  useEffect(() => {
    const onVis = () => {
      if (!document.hidden) void poll();
    };
    document.addEventListener("visibilitychange", onVis);
    void poll();
    return () => {
      document.removeEventListener("visibilitychange", onVis);
      clearTimersAndAbort();
    };
  }, [clearTimersAndAbort, poll]);

  // ----------------------------
  // 4) Selection logic: keep selected job valid under filtering
  // ----------------------------
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const queryJobId = params.get("job_id");
    if (queryJobId && jobs.some((j) => j.id === queryJobId)) {
      setSelectedJobId(queryJobId);
      return;
    }

    if (selectedJobId && visibleJobs.some((j) => j.id === selectedJobId)) return;
    if (visibleJobs.length > 0) setSelectedJobId(visibleJobs[0].id);
    else setSelectedJobId(null);
  }, [jobs, pipelineQuery, selectedJobId, visibleJobs]);

  // ----------------------------
  // 5) Handlers (TDZ-safe: they do NOT reference derived vars in deps)
  // ----------------------------
  const handleJobCreated = useCallback(
    (jobId?: string) => {
      console.log("[Dashboard] handleJobCreated:", jobId);

      if (!jobId) {
        console.error("[Dashboard] missing jobId; cannot navigate");
        try {
          (window as any).toast?.({
            title: "Launch failed",
            description: "No jobId received; cannot open progress page.",
            variant: "destructive",
          });
        } catch {
          alert("Launch failed: missing jobId.");
        }
        return;
      }

      setSelectedJobId(jobId);
      navigate(`/pipeline/progress/${jobId}`);

      // Background refresh; do not block navigation
      void poll();
    },
    [navigate, poll]
  );

  // ----------------------------
  // UI helpers
  // ----------------------------
  const pct = useMemo(() => {
    if (!summary) return 0;
    const total = Math.max(summary.total_count || 0, 1);
    const done = Math.max(summary.processed_count || 0, 0);
    return Math.min(Math.round((done / total) * 100), 100);
  }, [summary]);

  const showActionPanel = !!pipelineQuery;

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xl font-semibold">Logistics</div>
          <div className="text-sm text-slate-500">
            {degraded ? "DEGRADED (serving cached data)" : online ? "ONLINE" : "OFFLINE"}
            {loading ? " · polling…" : ""}
            {pipelineQuery ? ` · pipeline=${pipelineQuery}` : ""}
          </div>
        </div>
        <div className="text-sm text-slate-500">Jobs: {visibleJobs.length} · Running: {runningCount}</div>
      </div>

      {showActionPanel && (
        <PipelineActionPanel pipeline={pipelineQuery} onJobCreated={handleJobCreated} />
      )}

      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-4">
          <div className="rounded border bg-white">
            <div className="px-3 py-2 border-b text-sm font-medium">
              {pipelineQuery ? `Pipeline ${pipelineQuery} Jobs` : "Jobs"}
            </div>
            <div className="max-h-[60vh] overflow-auto">
              {visibleJobs.map((j) => (
                <button
                  key={j.id}
                  className={`w-full text-left px-3 py-2 border-b hover:bg-slate-50 ${
                    selectedJobId === j.id ? "bg-slate-100" : ""
                  }`}
                  onClick={() => setSelectedJobId(j.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="font-mono text-xs">#{j.id.slice(0, 8)}</div>
                    <div className="text-xs">{j.status}</div>
                  </div>
                  <div className="text-xs text-slate-500">pipeline: {j.pipeline_type}</div>
                  <div className="text-xs text-slate-500">
                    {j.processed_count ?? 0}/{j.total_count ?? 0} ok:{j.success_count ?? 0} err:{j.failed_count ?? 0}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="col-span-8 space-y-4">
          <div className="rounded border bg-white p-4">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium">Job Summary</div>
              <div className="text-xs text-slate-500">{selectedJobId ? `job_id=${selectedJobId}` : "no selection"}</div>
            </div>
            {!summary ? (
              <div className="text-sm text-slate-400 mt-3">No summary.</div>
            ) : (
              <div className="mt-3 space-y-2">
                <div className="text-sm">
                  status: <span className="font-mono">{summary.status}</span> · pipeline:{" "}
                  <span className="font-mono">{summary.pipeline_type}</span>
                </div>
                <div className="h-2 rounded bg-slate-100 overflow-hidden">
                  <div className="h-2 bg-slate-800" style={{ width: `${pct}%` }} />
                </div>
                <div className="text-xs text-slate-500">
                  processed {summary.processed_count}/{summary.total_count} · ok {summary.success_count} · err {summary.failed_count} · hb{" "}
                  {summary.last_heartbeat_at ? new Date(summary.last_heartbeat_at).toLocaleTimeString() : "—"}
                </div>
              </div>
            )}
          </div>

          <div className="rounded border bg-white">
            <div className="px-3 py-2 border-b text-sm font-medium">Items</div>
            <div className="max-h-[55vh] overflow-auto">
              {items.length === 0 ? (
                <div className="p-4 text-sm text-slate-400">No items.</div>
              ) : (
                <table className="w-full text-xs">
                  <thead className="sticky top-0 bg-white border-b">
                    <tr className="text-left text-slate-500">
                      <th className="p-2">target</th>
                      <th className="p-2 w-28">stage</th>
                      <th className="p-2 w-28">status</th>
                      <th className="p-2 w-40">updated</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((it) => (
                      <tr
                        key={it.id}
                        className={`border-b ${flashIds[it.id] ? "bg-yellow-50" : ""}`}
                      >
                        <td className="p-2 font-mono truncate max-w-[420px]" title={it.target_id}>
                          {it.target_id}
                        </td>
                        <td className="p-2 font-mono">{it.stage || "—"}</td>
                        <td className="p-2 font-mono">
                          {it.status}
                          {it.status === "failed" && it.error_log ? (
                            <div className="text-[11px] text-red-600 truncate" title={it.error_log}>
                              {it.error_log}
                            </div>
                          ) : null}
                        </td>
                        <td className="p-2 font-mono text-slate-500">
                          {it.updated_at ? new Date(it.updated_at).toLocaleTimeString() : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
