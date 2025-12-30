import NarrativeDetailScreen from "./NarrativeDetailScreen";
import { useNarrativeAnalysis } from "../hooks/useNarrativeAnalysis";
import { getSlotStatus } from "../utils/slotContracts.ts";

type NarrativeDetailPageProps = {
  postId: string;
  navigate: (to: string) => void;
};

const NarrativeDetailPage = ({ postId, navigate }: NarrativeDetailPageProps) => {
  const { data, loading, error, meta } = useNarrativeAnalysis(postId);
  const secondaryReason = (() => {
    if (!error) return null;
    if (error.status === 404) {
      return `No analysis available for Post_ID ${postId} yet.`;
    }
    if (error.status) {
      return `Backend request failed (${error.status} – ${error.statusText || "Unknown error"}).`;
    }
    return error.message;
  })();

  if (loading) {
    return (
      <div className="bg-background-dark text-white min-h-screen flex flex-col">
        <div className="p-6">
          <div className="h-10 w-32 rounded-full bg-white/5 animate-pulse" />
        </div>
        <div className="flex-1 px-6 pb-8 space-y-4">
          <div className="h-40 w-full glass-panel rounded-2xl animate-pulse" />
          <div className="h-24 w-full glass-panel rounded-2xl animate-pulse" />
          <div className="h-64 w-full glass-panel rounded-2xl animate-pulse" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-background-dark text-white flex flex-col items-center justify-center p-6 text-center space-y-3">
        <p className="text-lg font-semibold">Unable to load narrative for this post.</p>
        <p className="text-sm text-slate-400">{secondaryReason || "No analysis returned for this post."}</p>
        {error?.bodySnippet && (
          <p className="text-xs text-slate-500 max-w-xl">
            {error.bodySnippet}
          </p>
        )}
        <div className="flex gap-3">
          <button
            onClick={() => window.location.reload()}
            className="rounded-full border border-primary/60 bg-primary/10 px-4 py-2 text-sm text-primary hover:bg-primary/20 transition"
          >
            Retry
          </button>
          <button
            onClick={() => navigate("/")}
            className="rounded-full border border-slate-600 bg-slate-800 px-4 py-2 text-sm text-white hover:bg-slate-700 transition"
          >
            Back
          </button>
        </div>
      </div>
    );
  }

  const slotStatus = data ? getSlotStatus(data, meta?.analysis_missing_keys as string[] | undefined) : {};

  return (
    <div className="bg-background-dark text-white min-h-screen">
      {meta?.analysis_is_valid === false && (
        <div className="bg-red-900/50 text-red-200 px-4 py-3 text-sm">
          分析無效：{meta.analysis_invalid_reason || "缺少必要欄位"}{" "}
          {meta?.analysis_missing_keys ? `(缺: ${meta.analysis_missing_keys.join(", ")})` : ""}
        </div>
      )}
      <NarrativeDetailScreen analysisJson={data} slotStatus={slotStatus} />
    </div>
  );
};

export default NarrativeDetailPage;
