import { FactionRow } from "../../hooks/useClusterData";
import { CardShell } from "./CardShell";

interface ClusterTableCardProps {
  factions: FactionRow[];
}

const ClusterTableCard = ({ factions }: ClusterTableCardProps) => {
  if (!factions.length) {
    return (
      <CardShell title="派系總覽｜Faction Overview" accent="pink">
        <p className="text-sm text-slate-400">尚無派系資料。</p>
      </CardShell>
    );
  }

  const top = factions.slice(0, 6);

  return (
    <CardShell title="派系總覽｜Faction Overview" accent="pink">
      <div className="space-y-2 text-sm text-white">
        {top.map((f, idx) => {
          const pct = (f.share || 0) * 100;
          const isDominant = idx === 0 && pct > 0;
          return (
            <div
              key={`${f.name}-${idx}`}
              className="flex flex-col gap-0.5 rounded-lg border border-slate-800/60 bg-slate-900/40 px-2 py-1.5"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-white truncate">{f.name}</span>
                <span className={`text-[10px] ${isDominant ? "text-emerald-300 font-semibold" : "text-slate-400"}`}>
                  {pct > 0 ? `${pct.toFixed(1)}%` : "N/A"}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 line-clamp-2">{f.summary || "—"}</p>
            </div>
          );
        })}
      </div>
      {factions.length > top.length && (
        <p className="mt-2 text-[10px] text-slate-500">另有 {factions.length - top.length} 個次要派系未列出。</p>
      )}
    </CardShell>
  );
};

export default ClusterTableCard;
