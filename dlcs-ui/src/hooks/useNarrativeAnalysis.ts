import { useEffect, useState } from "react";
import { fetchAnalysisJson } from "../api/analysis";
import { API_BASE, HttpError } from "../api/client";
import { NarrativeAnalysis } from "../types/narrative";
import { normalizeAnalysisJson } from "../utils/normalizeAnalysisJson";
import { AnalysisResponse } from "../types/analysis";

export type NarrativeError = {
  message: string;
  status?: number;
  statusText?: string;
  url?: string;
  bodySnippet?: string;
};

export function useNarrativeAnalysis(postId?: string) {
  const [data, setData] = useState<NarrativeAnalysis | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<NarrativeError | null>(null);
  const [meta, setMeta] = useState<Partial<AnalysisResponse> | null>(null);

  useEffect(() => {
    if (!postId) return;
    let cancelled = false;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setData(null);
    setMeta(null);

    fetchAnalysisJson(postId, { signal: controller.signal })
      .then((resp) => {
        if (cancelled) return;
        try {
          const normalized = normalizeAnalysisJson(resp.analysis_json as any);
          setData(normalized);
          setMeta(resp);
          setLoading(false);
        } catch (e) {
          const msg = e instanceof Error ? e.message : "Unexpected data shape";
          setError({ message: msg });
          setLoading(false);
        }
      })
      .catch((e) => {
        if (cancelled || controller.signal.aborted) return;
        const httpErr = e as HttpError;
        const detail: NarrativeError = {
          message: httpErr?.message || "Failed to load narrative",
          status: httpErr?.status,
          statusText: httpErr?.statusText,
          url: httpErr?.url || `${API_BASE}/api/analysis-json/${postId}`,
          bodySnippet: httpErr?.bodySnippet,
        };
        console.error("[useNarrativeAnalysis] Request failed", {
          postId,
          urlTried: detail.url,
          status: detail.status,
          statusText: detail.statusText,
          bodySnippet: detail.bodySnippet,
          error: e,
        });
        setError(detail);
        setLoading(false);
      });

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [postId]);

  return { data, loading, error, meta } as const;
}
