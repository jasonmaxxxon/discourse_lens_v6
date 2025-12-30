// npm install react-markdown remark-gfm
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { fetchAnalysisMarkdown } from "../../api/analysis";
import { CardShell } from "./CardShell";

type Props = {
  postId: string;
  rawMarkdown?: string;
};

export const RawReportCard = ({ postId, rawMarkdown }: Props) => {
  const [markdown, setMarkdown] = useState<string>(rawMarkdown || "");
  const [loading, setLoading] = useState<boolean>(!rawMarkdown);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (rawMarkdown) {
      setMarkdown(rawMarkdown);
      setLoading(false);
      setError(null);
      return () => {
        /* no-op */
      };
    }

    setLoading(true);
    setError(null);
    fetchAnalysisMarkdown(postId)
      .then((md) => {
        if (!cancelled) {
          setMarkdown(md);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          const msg = err instanceof Error ? err.message : String(err);
          setError(msg || "Failed to load full report");
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [postId, rawMarkdown]);

  return (
    <CardShell title="DLCS Analysis – Full Report" subtitle={`Post #${postId}`} accent="cyan">
      <div className="max-h-[540px] w-[320px] overflow-y-auto rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm leading-relaxed text-white">
        {loading && <p className="text-slate-300">Loading markdown…</p>}
        {error && (
          <p className="rounded-lg border border-rose-500/40 bg-rose-500/10 p-2 text-rose-100">
            無法取得完整報告：{error}
          </p>
        )}
        {!loading && !error && markdown && (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            className="prose prose-invert max-w-none prose-sm"
          >
            {markdown}
          </ReactMarkdown>
        )}
        {!loading && !error && !markdown && <p className="text-slate-300">尚無完整 Markdown 報告。</p>}
      </div>
    </CardShell>
  );
};

export default RawReportCard;
