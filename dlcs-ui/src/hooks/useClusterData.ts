import { AnalysisJson, RawClusterInsight } from "../types/analysis";

export interface FactionRow {
  name: string;
  summary: string;
  share: number;
}

export interface UseClusterResult {
  factions: FactionRow[];
}

export function useClusterData(analysis?: AnalysisJson | null): UseClusterResult {
  if (!analysis) return { factions: [] };

  let factions: FactionRow[] =
    analysis.battlefield?.factions?.map((f) => ({
      name: f.name || "未命名派系",
      summary: f.summary || "",
      share: typeof f.share === "number" ? Math.max(0, Math.min(1, f.share)) : 0,
    })) ?? [];

  if (!factions.length && analysis.raw_json?.Cluster_Insights) {
    const raw = analysis.raw_json.Cluster_Insights;
    const entries = Object.entries<RawClusterInsight>(raw);
    if (entries.length) {
      const withShare = entries.map(([cid, info]) => {
        const name = info.name || `Cluster ${cid}`;
        const summary = info.summary || "";
        let share = info.share ?? info.pct ?? 0;
        if (typeof share === "number" && share > 1) share = share / 100;
        return { name, summary, share: typeof share === "number" ? share : 0 };
      });
      const totalShare = withShare.reduce((s, f) => s + (f.share || 0), 0);
      if (totalShare <= 0 && withShare.length > 0) {
        const equal = 1 / withShare.length;
        factions = withShare.map((f) => ({ ...f, share: equal }));
      } else {
        factions = withShare;
      }
    }
  }

  factions.sort((a, b) => b.share - a.share);

  return { factions };
}
