import { useMemo, useState } from "react";
import { CardShell } from "./CardShell";
import { PostAnalysis } from "../../types/analysis";
import { motion } from "framer-motion";

const colors = ["#22d3ee", "#f59e0b", "#a855f7", "#38bdf8", "#f97316"];

type Props = { data: PostAnalysis };

export const FactionTerrainCard = ({ data }: Props) => {
  const clusters = useMemo(() => Object.entries(data.insights || {}) as [string, any][], [data.insights]);
  const [hovered, setHovered] = useState<string | null>(null);

  return (
    <CardShell title="Faction Terrain" subtitle="犬儒批評者 vs 務實憂慮者" accent="amber">
      <div className="relative h-64 overflow-hidden rounded-xl bg-gradient-to-br from-slate-900 to-slate-800 p-4">
        {clusters.map(([cid, info], idx) => {
          const pctVal = typeof info?.pct === "number" ? info.pct : 0.2;
          const pct = Math.max(0.05, pctVal);
          const size = 80 + pct * 180;
          const left = (idx / Math.max(clusters.length - 1, 1)) * 60 + 10;
          const top = (idx % 2 === 0 ? 25 : 55) + pct * 10;
          return (
            <motion.div
              key={cid}
              className="absolute flex flex-col items-center gap-1"
              style={{ left: `${left}%`, top: `${top}%` }}
              onHoverStart={() => setHovered(cid)}
              onHoverEnd={() => setHovered(null)}
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: idx * 0.05 }}
            >
              <motion.div
                className="flex items-center justify-center rounded-full border border-white/20 text-xs font-semibold shadow-lg"
                style={{
                  width: size,
                  height: size,
                  background: `${colors[idx % colors.length]}22`,
                  color: colors[idx % colors.length],
                }}
                animate={{ scale: hovered === cid ? 1.08 : 1 }}
              >
                <div className="text-center">
                  <div>{info.name || `Cluster ${cid}`}</div>
                  <div className="text-[11px] text-white/70">{Math.round((info.pct ?? 0) * 100)}%</div>
                </div>
              </motion.div>
            </motion.div>
          );
        })}
      </div>
      <div className="mt-3 text-sm text-subtle">
        {hovered && data.insights[hovered]
          ? data.insights[hovered].summary
          : data.section1.factionAnalysis}
      </div>
    </CardShell>
  );
};

export default FactionTerrainCard;
