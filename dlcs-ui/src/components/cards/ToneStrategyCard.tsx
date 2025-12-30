import { StrategyBlock, ToneFingerprint } from "../../types/analysis";
import { CardShell } from "./CardShell";

type Props = { tone: ToneFingerprint; strategies: StrategyBlock };

const clamp01 = (value: number | undefined): number => {
  if (typeof value !== "number" || Number.isNaN(value)) return 0;
  return Math.min(1, Math.max(0, value));
};

export const ToneStrategyCard = ({ tone, strategies }: Props) => {
  const toneMetrics = [
    { label: "Cynicism", value: clamp01(tone.cynicism), color: "bg-amber-400" },
    { label: "Anger", value: clamp01(tone.anger), color: "bg-rose-400" },
    { label: "Hope", value: clamp01(tone.hope), color: "bg-emerald-400" },
    { label: "Despair", value: clamp01(tone.despair), color: "bg-slate-400" },
  ];
  const secondary = strategies.secondary ?? [];
  const tactics = strategies.tactics ?? [];
  const allZero = toneMetrics.every((metric) => metric.value === 0);

  return (
    <CardShell title="VIBE CHECK｜氣氛檢測" accent="amber" className="h-full">
      <div className="relative h-full flex flex-col gap-4">
        <div className="pointer-events-none absolute right-6 bottom-6 text-7xl md:text-8xl font-bold text-slate-700/20">
          02
        </div>
        <div className="flex items-center justify-between">
          <span className="text-[11px] uppercase tracking-[0.25em] text-slate-400">Tone Fingerprint</span>
          {strategies.primary && (
            <span className="rounded-full border border-amber-400/60 bg-amber-500/10 px-3 py-1 text-xs text-amber-100">
              {strategies.primary}
            </span>
          )}
        </div>

        <div className="space-y-3">
          {allZero && <p className="text-slate-300">尚未偵測到明顯情緒指紋。</p>}
          {toneMetrics.map((metric, idx) => (
            <div key={metric.label} className="space-y-1">
              <div className="flex justify-between text-[11px] uppercase tracking-[0.2em] text-slate-400">
                <span>{metric.label}</span>
                <span>{Math.round(metric.value * 100)}%</span>
              </div>
              <div className="h-3 rounded-full overflow-hidden border border-slate-700 bg-slate-900">
                <div
                  className={`h-full ${metric.color}`}
                  style={{ width: `${Math.round(metric.value * 100)}%`, opacity: allZero ? 0.2 : 1 }}
                />
              </div>
            </div>
          ))}
        </div>

        <div className="mt-auto space-y-2">
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">Primary Strategy</p>
          <div className="rounded-2xl border border-amber-400/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-50">
            {strategies.primary || "未提供"}
          </div>
          {secondary.length > 0 && (
            <div className="space-y-1">
              <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">Secondary</p>
              <div className="flex flex-wrap gap-2">
                {secondary.map((item, idx) => (
                  <span
                    key={`${item}-${idx}`}
                    className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-xs text-slate-200"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
          )}
          {tactics.length > 0 && (
            <div className="space-y-1">
              <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">Tactics</p>
              <ul className="list-disc space-y-1 pl-5 text-sm text-slate-100">
                {tactics.map((item, idx) => (
                  <li key={`${item}-${idx}`}>{item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </CardShell>
  );
};

export default ToneStrategyCard;
