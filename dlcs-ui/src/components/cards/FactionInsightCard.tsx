import { useState } from "react";
import { CardShell } from "./CardShell";
import { PostAnalysis } from "../../types/analysis";
import { motion, AnimatePresence } from "framer-motion";

const variants = {
  enter: { x: 50, opacity: 0 },
  center: { x: 0, opacity: 1 },
  exit: { x: -50, opacity: 0 },
};

type Props = { data: PostAnalysis };

export const FactionInsightCard = ({ data }: Props) => {
  const [index, setIndex] = useState(0);
  const factions = data.factions;
  const current = factions[index % factions.length];

  const next = () => setIndex((i) => (i + 1) % factions.length);
  const prev = () => setIndex((i) => (i - 1 + factions.length) % factions.length);

  return (
    <CardShell title="Faction Insight" subtitle="派系洞察卡" accent="pink">
      <div className="flex items-center justify-between text-xs text-subtle">
        <span>
          Cluster {index + 1} / {factions.length}
        </span>
        <div className="flex gap-2">
          <button onClick={prev} className="rounded-full border border-slate-700 px-2 py-1">
            ←
          </button>
          <button onClick={next} className="rounded-full border border-slate-700 px-2 py-1">
            →
          </button>
        </div>
      </div>
      <div className="relative mt-2 h-44 overflow-hidden">
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={current.label}
            variants={variants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ duration: 0.3 }}
            className="absolute inset-0 flex flex-col gap-2 rounded-xl border border-slate-800 bg-slate-900/70 p-4"
          >
            <div className="flex items-center justify-between">
              <h4 className="text-lg font-bold text-white">{current.label}</h4>
              {current.dominant && (
                <span className="rounded-full bg-emerald-400/20 px-2 py-1 text-xs text-emerald-200">Dominant</span>
              )}
            </div>
            <p className="text-sm text-white">{current.summary}</p>
            <ul className="list-disc space-y-1 pl-4 text-xs text-subtle">
              {current.bullets.map((b) => (
                <li key={b}>{b}</li>
              ))}
            </ul>
          </motion.div>
        </AnimatePresence>
      </div>
    </CardShell>
  );
};

export default FactionInsightCard;
