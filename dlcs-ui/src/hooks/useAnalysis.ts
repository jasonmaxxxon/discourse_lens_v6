import { useEffect, useState } from "react";
import { fetchAnalysisJson } from "../api/analysis";
import { AnalysisJson } from "../types/analysis";

// Optional helper hook (not currently used by App) to load structured analysis.
export function useAnalysis(postId?: string) {
  const [data, setData] = useState<AnalysisJson | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (!postId) {
      setData(null);
      setLoading(false);
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    setData(null);

    fetchAnalysisJson(postId)
      .then((res) => {
        if (!cancelled) {
          setData(res);
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
  }, [postId]);

  return { data, loading, error } as const;
}
