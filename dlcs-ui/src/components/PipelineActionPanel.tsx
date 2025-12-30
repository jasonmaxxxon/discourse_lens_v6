import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

type Props = {
  pipeline: string; // "A" | "B" | "C" | ...
  onJobCreated?: (jobId?: string) => void; // parent can force refresh
};

type CreateJobPayload = {
  pipeline_type: string;
  mode?: string;
  input_config?: Record<string, unknown>;
};

function normalizePipeline(p: string) {
  return (p || "").trim().toUpperCase();
}

function isProbablyUrl(s: string) {
  return /^https?:\/\/\S+/i.test(s.trim());
}

export default function PipelineActionPanel({ pipeline, onJobCreated }: Props) {
  const type = useMemo(() => normalizePipeline(pipeline), [pipeline]);
  const navigate = useNavigate();

  const [input, setInput] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  const canRun = input.trim().length > 0 && !submitting;

  async function handleRun() {
    setErr(null);
    setOk(null);

    const v = input.trim();
    if (!v) return;

    setSubmitting(true);
    try {
      const launchNonce =
        typeof crypto !== "undefined" && "randomUUID" in crypto ? (crypto as any).randomUUID() : `nonce-${Date.now()}`;

      if (type === "A") {
        const launchState = {
          pipelineType: "A",
          mode: "ingest",
          inputConfig: { target: v, url: v, target_url: v, targets: [v] },
          launchNonce,
        };
        sessionStorage.setItem("dl_launch_payload", JSON.stringify(launchState));
        navigate("/pipeline/launch", { state: launchState, replace: false });
        setOk("A launched.");
        setInput("");
        return;
      }

      if (type === "B") {
        const lines = v
          .split("\n")
          .map((s) => s.trim())
          .filter(Boolean);

        const urls = lines.filter(isProbablyUrl);
        const keywords = lines.filter((x) => !isProbablyUrl(x));

        const launchState = {
          pipelineType: "B",
          mode: "discover",
          inputConfig: {
            targets: lines,
            urls,
            keywords,
          },
          launchNonce,
        };
        sessionStorage.setItem("dl_launch_payload", JSON.stringify(launchState));
        navigate("/pipeline/launch", { state: launchState, replace: false });
        setOk(`B batch launching (${lines.length}).`);
        setInput("");
        return;
      }

      setErr(`Pipeline ${type} actions not enabled.`);
    } catch (e: any) {
      setErr(e?.message || String(e));
    } finally {
      setSubmitting(false);
    }
  }

  if (!type) return null;

  if (type !== "A" && type !== "B") {
    return (
      <section className="card w-full max-w-6xl">
        <div className="card-header flex items-center justify-between">
          <span>Pipeline {type} Controls</span>
          <span className="badge badge-neutral">READ ONLY</span>
        </div>
        <div className="p-4 text-xs text-muted">
          This pipeline view is available for monitoring. Manual launch is not wired yet.
        </div>
      </section>
    );
  }

  const title = type === "A" ? "Pipeline A — Single URL" : "Pipeline B — Batch Runner";
  const helper = type === "A" ? "Paste one URL and launch." : "Enter one item per line (keywords or URLs).";
  const buttonText = type === "A" ? "Launch" : "Run Batch";

  return (
    <section className="card w-full max-w-6xl">
      <div className="card-header flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <span className="font-semibold">{title}</span>
            <span className="badge badge-warning">LIVE</span>
          </div>
          <div className="text-xs text-muted">{helper}</div>
        </div>

        <button
          className="btn btn-primary"
          disabled={!canRun}
          onClick={() => void handleRun()}
          title="Create job"
        >
          {submitting ? (
            <span className="inline-flex items-center gap-2">
              <span className="material-symbols-outlined animate-spin text-[18px]">sync</span>
              Posting
            </span>
          ) : (
            <span className="inline-flex items-center gap-2">
              <span className="material-symbols-outlined text-[18px]">play_arrow</span>
              {buttonText}
            </span>
          )}
        </button>
      </div>

      <div className="p-4 pt-0 space-y-3">
        {type === "A" ? (
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="https://www.threads.net/@user/post/..."
            className="w-full border border-[var(--border-subtle)] rounded-lg px-3 py-2 bg-[var(--bg-card)] text-[var(--text-primary)]"
          />
        ) : (
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={"keyword 1\nkeyword 2\nhttps://..."}
            rows={4}
            className="w-full border border-[var(--border-subtle)] rounded-lg px-3 py-2 bg-[var(--bg-card)] text-[var(--text-primary)]"
          />
        )}

        {(err || ok) && (
          <div className="text-xs font-mono">
            {ok && (
              <div className="badge badge-success inline-flex items-center gap-1">
                <span className="material-symbols-outlined text-[14px]">check</span>
                {ok}
              </div>
            )}
            {err && (
              <div className="badge badge-danger inline-flex items-center gap-1">
                <span className="material-symbols-outlined text-[14px]">error</span>
                {err}
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
