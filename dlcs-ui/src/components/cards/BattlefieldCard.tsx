import { BattlefieldBlock } from "../../types/analysis";
import { CardShell } from "./CardShell";

type Props = { battlefield: BattlefieldBlock };

export const BattlefieldCard = ({ battlefield }: Props) => {
  const factions =
    (battlefield?.factions || [])
      .filter((f) => f && f.name)
      .sort((a, b) => (b.share ?? 0) - (a.share ?? 0)) || [];
  const topFactions = factions.slice(0, 3);

  return (
    <CardShell title="WAR ROOM｜戰場分佈" accent="pink" className="h-full">
      <div className="relative h-full">
        <div className="pointer-events-none absolute right-6 bottom-6 text-7xl md:text-8xl font-bold text-slate-700/20">
          03
        </div>
        {topFactions.length === 0 && <p className="text-slate-300">尚未偵測到清晰的派系結構。</p>}
        {topFactions.length > 0 && (
          <div className="space-y-4 mt-4">
            {topFactions.map((faction, idx) => {
              const pct = typeof faction.share === "number" ? Math.round((faction.share || 0) * 100) : null;
              return (
              <div
                key={`${faction.name}-${idx}`}
                className="rounded-2xl border border-slate-700 bg-slate-950/80 p-4"
              >
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-sm font-semibold">{faction.name || `Faction ${idx + 1}`}</h3>
                  <span className="text-xs text-slate-400">
                    {pct !== null ? `${pct}%` : "比例未定"}
                  </span>
                </div>
                <div className="h-2 mb-2 bg-slate-900 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-400"
                    style={{ width: `${pct !== null ? pct : 0}%` }}
                  />
                </div>
                <p className="text-xs text-slate-300 leading-relaxed line-clamp-2">
                  {faction.summary || "暫無摘要"}
                </p>
                {faction.samples && faction.samples.length > 0 && (
                  <div className="mt-3 space-y-1 text-xs text-slate-300">
                    <div className="uppercase tracking-wide text-[10px] text-slate-400">Example comments</div>
                    {faction.samples.slice(0, 2).map((s, sidx) => (
                      <div key={sidx} className="flex gap-2">
                        <span className="shrink-0 text-[10px] text-slate-500">@{s.user || "anon"}</span>
                        <span className="line-clamp-2">{s.text || "…"}</span>
                        {typeof s.like_count === "number" && s.like_count > 0 && (
                          <span className="shrink-0 text-[10px] text-slate-500 ml-auto">❤️ {s.like_count}</span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
            })}
          </div>
        )}
      </div>
    </CardShell>
  );
};

export default BattlefieldCard;
