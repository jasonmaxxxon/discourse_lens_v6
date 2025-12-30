import { useEffect, useMemo, useRef, useState } from "react";

type Job = {
  id: string;
  pipeline_type: string;
  status: string;
  total_count?: number;
  processed_count?: number;
  created_at?: string;
  updated_at?: string;
};

const API_BASE = "/api/jobs";
const POLL_INTERVAL = 8000;

function progressFillClass(status?: string) {
  if (status === "processing") return "ops-progress-fill ops-progress-fill--processing";
  return "ops-progress-fill ops-progress-fill--solid";
}

function statusBadge(status: string) {
  if (status === "completed") return "badge badge-success";
  if (status === "failed") return "badge badge-danger";
  return "badge badge-warning";
}

export default function OpsSystemVitals() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [online, setOnline] = useState(true);
  const [degraded, setDegraded] = useState(false);
  const lastGood = useRef<Job[]>([]);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    const fetchJobs = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API_BASE}/?limit=50`);
        const isDegraded = res.headers.get("x-ops-degraded") === "1";
        const data = (await res.json()) as Job[];
        if (isDegraded && (!data || data.length === 0)) {
          setDegraded(true);
          setOnline(false);
          setJobs(lastGood.current);
          return;
        }
        setDegraded(isDegraded);
        setOnline(!isDegraded);
        setJobs(data || []);
        lastGood.current = data || [];
      } catch (e) {
        setOnline(false);
      } finally {
        setLoading(false);
      }
    };

    void fetchJobs();
    timerRef.current = window.setInterval(fetchJobs, POLL_INTERVAL);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const newestUpdated = useMemo(() => {
    const sorted = [...jobs].sort(
      (a, b) => new Date(b.updated_at || 0).getTime() - new Date(a.updated_at || 0).getTime()
    );
    return sorted[0]?.updated_at || null;
  }, [jobs]);

  const isSystemLive = useMemo(() => {
    if (!newestUpdated) return false;
    return Date.now() - new Date(newestUpdated).getTime() < 90_000;
  }, [newestUpdated]);

  const stats = useMemo(() => {
    const total = jobs.length;
    const processing = jobs.filter((j) => j.status === "processing").length;
    const completed = jobs.filter((j) => j.status === "completed").length;
    const failed = jobs.filter((j) => j.status === "failed").length;
    return { total, processing, completed, failed };
  }, [jobs]);

  const pipelineMix = useMemo(() => {
    const counts: Record<string, number> = {};
    jobs.forEach((j) => {
      const key = j.pipeline_type || "Unknown";
      counts[key] = (counts[key] || 0) + 1;
    });
    const total = Object.values(counts).reduce((a, b) => a + b, 0) || 1;
    let cursor = 0;
    const colors = ["var(--primary)", "var(--success)", "var(--warning)", "var(--danger)", "var(--text-secondary)"];
    const segments = Object.entries(counts).map(([key, val], idx) => {
      const start = cursor;
      const end = cursor + (val / total) * 360;
      cursor = end;
      return { key, start, end, color: colors[idx % colors.length], pct: Math.round((val / total) * 100) };
    });
    const gradient =
      segments.length === 0
        ? "conic-gradient(var(--primary) 0deg 360deg)"
        : `conic-gradient(${segments.map((s) => `${s.color} ${s.start}deg ${s.end}deg`).join(", ")})`;
    return { segments, gradient };
  }, [jobs]);

  return (
    <div className="app-shell p-4">
      <header className="app-header mb-4">
        <div>
          <div className="text-sm font-semibold uppercase tracking-wide text-[var(--text-secondary)]">System Vitals</div>
          <div className="text-xs text-muted">Aggregated from /api/jobs (truthful, no fabricated progress)</div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`badge ${online ? "badge-success" : "badge-danger"}`}>{online ? "Healthy" : "Degraded"}</span>
          {degraded && <span className="badge badge-warning">Read Fallback</span>}
          <div className="flex items-center gap-2">
            <span className="ops-chip--live">LIVE</span>
            <span className={`ops-heartbeat ${isSystemLive ? "ops-heartbeat--alive" : "ops-heartbeat--dead"}`} />
            <span className="text-[11px] text-muted">
              {newestUpdated ? new Date(newestUpdated).toLocaleTimeString() : "—"}
            </span>
          </div>
          <button className="btn btn-ghost text-xs" onClick={() => window.location.reload()}>
            <span className={`material-icons-outlined text-sm ${loading ? "animate-spin" : ""}`}>refresh</span>
            Refresh
          </button>
        </div>
      </header>

      <div className="grid grid-cols-4 gap-4 mb-4">
        <div className="card p-4">
          <div className="text-xs uppercase text-muted mb-2">Total Jobs</div>
          <div className="text-3xl font-semibold text-[var(--text-secondary)]">{stats.total}</div>
        </div>
        <div className="card p-4">
          <div className="text-xs uppercase text-muted mb-2">Processing</div>
          <div className="text-3xl font-semibold text-warning">{stats.processing}</div>
          <div className="ops-progress mt-2">
            <div
              className="ops-progress-fill ops-progress-fill--processing"
              style={{ width: `${stats.total ? (stats.processing / Math.max(stats.total, 1)) * 100 : 0}%` }}
            />
          </div>
        </div>
        <div className="card p-4">
          <div className="text-xs uppercase text-muted mb-2">Completed</div>
          <div className="text-3xl font-semibold text-success">{stats.completed}</div>
          <div className="ops-progress mt-2">
            <div
              className="ops-progress-fill ops-progress-fill--solid"
              style={{ width: `${stats.total ? (stats.completed / Math.max(stats.total, 1)) * 100 : 0}%` }}
            />
          </div>
        </div>
        <div className="card p-4">
          <div className="text-xs uppercase text-muted mb-2">Failed</div>
          <div className="text-3xl font-semibold text-danger">{stats.failed}</div>
        </div>
      </div>

      <div className="grid grid-cols-5 gap-4 mb-4">
        <div className="card p-4 col-span-2 flex items-center gap-4">
          <div className="h-24 w-24 rounded-full border border-[var(--border-subtle)]" style={{ backgroundImage: pipelineMix.gradient }} />
          <div className="flex-1">
            <div className="text-xs uppercase text-muted mb-2">Pipeline Mix</div>
            {pipelineMix.segments.length === 0 && <div className="text-muted text-sm">No jobs yet</div>}
            <div className="flex flex-col gap-1">
              {pipelineMix.segments.map((seg) => (
                <div key={seg.key} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span className="inline-block w-3 h-3 rounded-full" style={{ background: seg.color }} />
                    <span className="text-[var(--text-secondary)]">{seg.key}</span>
                  </div>
                  <span className="text-muted text-xs">{seg.pct}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="card col-span-3 p-4 overflow-hidden">
          <div className="card-header">Recent Jobs</div>
          <div className="overflow-auto">
            <table className="table">
              <thead>
                <tr>
                  <th className="w-20">Job</th>
                  <th className="w-24">Pipeline</th>
                  <th className="w-28">Status</th>
                  <th>Progress</th>
                  <th className="w-40">Updated</th>
                </tr>
              </thead>
              <tbody className="text-xs font-mono">
                {jobs.map((job) => {
                  const total = Math.max(job.total_count || 0, 1);
                  const pct = Math.min(((job.processed_count || 0) / total) * 100, 100);
                  return (
                    <tr key={job.id} className="hover:bg-[var(--bg-card-muted)]">
                      <td className="font-bold text-[var(--primary)]">{job.id.slice(0, 8)}</td>
                      <td>{job.pipeline_type}</td>
                      <td>
                        <span className={statusBadge(job.status)}>{job.status}</span>
                      </td>
                      <td>
                        <div className="ops-progress">
                          <div className={progressFillClass(job.status)} style={{ width: `${pct}%` }} />
                        </div>
                        <div className="text-[10px] text-muted mt-1">{(job.processed_count || 0) + "/" + total}</div>
                      </td>
                      <td className="text-muted">
                        {job.updated_at ? new Date(job.updated_at).toLocaleTimeString() : "-"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
