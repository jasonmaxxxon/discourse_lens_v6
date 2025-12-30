import { UseQuantDiagnosticsResult } from "../../hooks/useQuantDiagnostics";
import { CardShell } from "./CardShell";

interface QuantDiagnosticsCardProps {
  quant: UseQuantDiagnosticsResult;
}

const QuantDiagnosticsCard = ({ quant }: QuantDiagnosticsCardProps) => {
  const {
    sectorId,
    primaryEmotion,
    strategyCode,
    civil,
    homogeneity,
    authorInfluence,
    isNewPhenomenon,
    highImpact,
  } = quant;

  const Item = ({ label, value }: { label: string; value: React.ReactNode }) => (
    <div className="flex flex-col gap-0.5">
      <span className="text-[10px] uppercase tracking-wide text-slate-500">{label}</span>
      <span className="text-xs text-slate-100">{value || "N/A"}</span>
    </div>
  );

  return (
    <CardShell title="量化診斷｜Quantitative Diagnostics" subtitle="Sector / Emotion / Homogeneity" accent="amber">
      <div className="flex items-center justify-between mb-2">
        <div className="flex flex-wrap gap-2">
          {sectorId && (
            <span className="rounded-full border border-slate-700 bg-slate-800/80 px-3 py-1 text-xs text-slate-100">
              {sectorId}
            </span>
          )}
          {primaryEmotion && (
            <span className="rounded-full border border-slate-700 bg-slate-800/80 px-3 py-1 text-xs text-slate-100">
              Emotion: {primaryEmotion}
            </span>
          )}
          {strategyCode && (
            <span className="rounded-full border border-slate-700 bg-slate-800/80 px-3 py-1 text-xs text-slate-100">
              Strategy: {strategyCode}
            </span>
          )}
          {authorInfluence && (
            <span className="rounded-full border border-slate-700 bg-slate-800/80 px-3 py-1 text-xs text-slate-100">
              Influence: {authorInfluence}
            </span>
          )}
          {isNewPhenomenon && (
            <span className="rounded-full border border-amber-500/40 bg-amber-500/10 px-3 py-1 text-[11px] font-semibold text-amber-100">
              NEW PATTERN
            </span>
          )}
          {highImpact && (
            <span className="rounded-full border border-rose-500/60 bg-rose-500/20 px-3 py-1 text-[11px] font-semibold text-rose-100">
              HIGH IMPACT
            </span>
          )}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3 text-sm text-white">
        <Item
          label="Homogeneity"
          value={homogeneity.value != null ? `${homogeneity.value.toFixed(2)}｜${homogeneity.label}` : homogeneity.label}
        />
        <Item label="Civil Score" value={civil.value != null ? `${civil.value.toFixed(1)}｜${civil.label}` : civil.label} />
        <Item label="Sector" value={sectorId || "N/A"} />
        <Item label="Primary Emotion" value={primaryEmotion || "N/A"} />
        <Item label="Strategy Code" value={strategyCode || "N/A"} />
        <Item label="Author Influence" value={authorInfluence || "N/A"} />
      </div>
    </CardShell>
  );
};

export default QuantDiagnosticsCard;
