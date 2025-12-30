import { MetricsBlock } from "../../types/analysis";
import { CardShell } from "./CardShell";

const civilLabel = (score?: number | null) => {
  if (score === undefined || score === null) return "N/A";
  if (score >= 8) return "Deliberative";
  if (score >= 4) return "Heated";
  return "Toxic";
};

const homogeneityLabel = (score?: number | null) => {
  if (score === undefined || score === null) return "N/A";
  if (score >= 0.8) return "Echo";
  if (score >= 0.4) return "Polarized";
  return "Fragmented";
};

const barWidth = (score?: number | null, max = 1) => {
  if (score === undefined || score === null) return "0%";
  const pct = Math.max(0, Math.min(1, score / max)) * 100;
  return `${pct}%`;
};

type Props = { metrics?: MetricsBlock };

export const MetricsCard = ({ metrics }: Props) => {
  if (!metrics) {
    return (
      <CardShell title="量化指標｜Quantitative Metrics" subtitle="尚無量化資料" accent="cyan">
        <div className="text-sm text-slate-300">尚未取得量化資料。</div>
      </CardShell>
    );
  }

  return (
    <CardShell
      title="量化指標｜Quantitative Metrics"
      subtitle="Section 2 tags"
      accent={metrics.is_new_phenomenon ? "pink" : "cyan"}
    >
      <div className="space-y-3 text-sm text-white">
        <div className="flex flex-wrap gap-2">
          {metrics.sector_id && (
            <span className="rounded-full border border-slate-700 bg-slate-800/80 px-3 py-1 text-xs text-slate-100">
              {`Sector: ${metrics.sector_id}`}
            </span>
          )}
          {metrics.primary_emotion && (
            <span className="rounded-full border border-slate-700 bg-slate-800/80 px-3 py-1 text-xs text-slate-100">
              {`Emotion: ${metrics.primary_emotion}`}
            </span>
          )}
          {metrics.strategy_code && (
            <span className="rounded-full border border-slate-700 bg-slate-800/80 px-3 py-1 text-xs text-slate-100">
              {`Strategy: ${metrics.strategy_code}`}
            </span>
          )}
          {metrics.author_influence && (
            <span className="rounded-full border border-slate-700 bg-slate-800/80 px-3 py-1 text-xs text-slate-100">
              {`Influence: ${metrics.author_influence}`}
            </span>
          )}
          {metrics.is_new_phenomenon && (
            <span className="rounded-full border border-pink-400/60 bg-pink-500/20 px-3 py-1 text-xs text-pink-100">
              新現象 / NEW
            </span>
          )}
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-300">
            <span>Civil Score</span>
            <span>
              {metrics.civil_score ?? "N/A"} ({civilLabel(metrics.civil_score)})
            </span>
          </div>
          <div className="h-2 rounded-full bg-slate-800">
            <div className="h-2 rounded-full bg-emerald-400" style={{ width: barWidth(metrics.civil_score, 10) }} />
          </div>

          <div className="flex items-center justify-between text-xs text-slate-300">
            <span>Homogeneity</span>
            <span>
              {metrics.homogeneity_score != null ? Math.round((metrics.homogeneity_score || 0) * 100) : "N/A"}% (
              {homogeneityLabel(metrics.homogeneity_score)})
            </span>
          </div>
          <div className="h-2 rounded-full bg-slate-800">
            <div
              className="h-2 rounded-full bg-amber-400"
              style={{ width: barWidth(metrics.homogeneity_score ?? 0, 1) }}
            />
          </div>
        </div>
      </div>
    </CardShell>
  );
};

export default MetricsCard;
