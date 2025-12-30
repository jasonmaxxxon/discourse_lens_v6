import { useEffect, useState } from "react";
import AnalysisRail from "../components/AnalysisRail";
import PostSelector from "../components/PostSelector";
import { fetchAnalysisJson } from "../api/analysis";
import { AnalysisJson } from "../types/analysis";

type HomePageProps = {
  navigate: (to: string) => void;
};

export function HomePage({ navigate }: HomePageProps) {
  const [selectedPostId, setSelectedPostId] = useState<string | undefined>();
  const [analysis, setAnalysis] = useState<AnalysisJson | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedPostId) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    setAnalysis(null);

    fetchAnalysisJson(selectedPostId)
      .then((data) => {
        if (!cancelled) {
          setAnalysis(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          const msg = err instanceof Error ? err.message : String(err);
          setError(msg || "Failed to load analysis");
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedPostId]);

  return (
    <main className="min-h-screen bg-gradient-to-b from-background via-[#0b142b] to-background px-4 pb-12 text-white md:px-8">
      <div className="mx-auto max-w-6xl space-y-6 py-8">
        <header className="space-y-2">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">DiscourseLens – Structured Analysis</h1>
              <p className="text-subtle text-sm">
                選擇任意已完成分析的貼文，查看結構化結果與完整報告。
              </p>
            </div>
            {analysis?.post_id && (
              <button
                onClick={() => navigate(`/narrative/${analysis.post_id}`)}
                className="rounded-full border border-cyan-400/60 bg-cyan-500/10 px-4 py-2 text-sm text-cyan-100 hover:border-cyan-300 hover:bg-cyan-500/20 transition"
              >
                開啟 Narrative Deck
              </button>
            )}
          </div>
        </header>

        <PostSelector selectedPostId={selectedPostId} onSelect={setSelectedPostId} />

        {loading && (
          <div className="space-y-4">
            <div className="h-24 w-full animate-pulse rounded-2xl bg-slate-800/60" />
            <div className="h-[520px] w-full animate-pulse rounded-2xl bg-slate-800/40" />
          </div>
        )}
        {error && (
          <div className="rounded-2xl border border-rose-500/40 bg-rose-500/10 p-4 text-sm text-rose-100">
            無法取得分析：{error}
          </div>
        )}
        {!loading && !error && analysis && <AnalysisRail data={analysis} />}
        {!loading && !error && !analysis && (
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 text-sm text-slate-300">
            請先選擇一篇貼文以載入分析結果。
          </div>
        )}
      </div>
    </main>
  );
}

export default HomePage;
