import { useState } from "react";
import { JobExecutionMonitor } from "../components/JobExecutionMonitor";

function extractJobId(jobRes: any): string | null {
  if (!jobRes) return null;
  const candidates = [
    jobRes.job_id,
    jobRes.id,
    jobRes.jobId,
    jobRes.data?.job_id,
    jobRes.data?.id,
    jobRes.result?.job_id,
    jobRes.result?.id,
  ];
  for (const c of candidates) {
    if (typeof c === "string" && c.trim()) return c.trim();
  }
  return null;
}

export default function PipelineAPage() {
  const [url, setUrl] = useState("");
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [isLaunching, setIsLaunching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLaunch = async () => {
    if (!url.trim() || isLaunching) return;
    setError(null);
    setIsLaunching(true);
    try {
      const res = await fetch("/api/run/a", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim(), mode: "analyze" }),
      });
      if (!res.ok) {
        const errText = await res.text().catch(() => "");
        throw new Error(`POST /api/run/a failed (${res.status}) ${errText}`);
      }
      const json = await res.json();
      const jid = extractJobId(json);
      if (!jid) throw new Error("Job created but no jobId returned.");
      setActiveJobId(jid);
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setIsLaunching(false);
    }
  };

  const handleReset = () => {
    setActiveJobId(null);
    setUrl("");
    setError(null);
    setIsLaunching(false);
  };

  return (
    <div className="min-h-screen bg-[#0f172a] text-white p-6 flex flex-col items-center">
      <div className="w-full max-w-5xl space-y-6">
        <header className="flex items-center justify-between">
          <div>
            <div className="text-xs font-bold uppercase tracking-[0.2em] text-white/60">Pipeline A</div>
            <h1 className="text-3xl font-bold mt-1">Active Console</h1>
            <p className="text-sm text-white/60">Enter a Threads URL, execute, and monitor progress on the same page.</p>
          </div>
          <div className="text-xs text-white/70 font-mono">{activeJobId ? `job=${activeJobId.slice(0, 8)}` : "idle"}</div>
        </header>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-2xl shadow-black/20 space-y-3">
          <label className="text-xs font-bold uppercase tracking-[0.12em] text-white/60">Target URL</label>
          <div className="flex gap-3 items-center">
            <input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://www.threads.net/@user/post/..."
              className="flex-1 px-4 py-3 rounded-lg bg-[#0b1323] border border-white/10 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLaunching}
            />
            <button
              className="px-4 py-3 rounded-lg bg-blue-500 text-white font-semibold disabled:opacity-60 disabled:cursor-not-allowed shadow-lg shadow-blue-500/30"
              onClick={() => void handleLaunch()}
              disabled={!url.trim() || isLaunching}
            >
              {isLaunching ? "Initializing..." : "Execute"}
            </button>
          </div>
          {error && <div className="text-sm text-red-300">{error}</div>}
        </div>

        {activeJobId && (
          <div className="space-y-4">
            <div className="text-xs text-white/60 font-mono">Job ID: {activeJobId}</div>
            <JobExecutionMonitor
              jobId={activeJobId}
              onReset={handleReset}
              onBack={() => (window.location.href = "/")}
            />
          </div>
        )}
      </div>
    </div>
  );
}
