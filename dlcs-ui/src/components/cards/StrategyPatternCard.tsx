import { useState } from "react";
import { CardShell } from "./CardShell";
import { PostAnalysis, StrategySnippet } from "../../types/analysis";
import { motion } from "framer-motion";
import clsx from "clsx";

type FlipProps = { snippet: StrategySnippet };

const StrategyChip = ({ snippet }: FlipProps) => {
  const [flipped, setFlipped] = useState(false);
  return (
    <motion.div
      className="[perspective:1200px]"
      whileHover={{ scale: 1.04 }}
      onClick={() => setFlipped((s) => !s)}
    >
      <motion.div
        animate={{ rotateY: flipped ? 180 : 0 }}
        transition={{ duration: 0.5 }}
        className="relative h-32 w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-3 shadow"
        style={{ transformStyle: "preserve-3d" }}
      >
        <div
          className={clsx(
            "absolute inset-0 flex flex-col justify-between",
            flipped && "[transform:rotateY(180deg)]"
          )}
          style={{ backfaceVisibility: "hidden" }}
        >
          <div className="flex items-center justify-between text-sm font-semibold text-white">
            <span>{snippet.name}</span>
            <span className="text-xs text-amber-300">{Math.round(snippet.intensity * 100)}%</span>
          </div>
          <div className="h-2 w-full rounded-full bg-slate-800">
            <div
              className="h-2 rounded-full bg-gradient-to-r from-amber-400 to-pink-400"
              style={{ width: `${snippet.intensity * 100}%` }}
            />
          </div>
          <div className="text-xs text-subtle">Tap to flip →</div>
        </div>
        <div
          className="absolute inset-0 flex flex-col justify-between px-1"
          style={{ transform: "rotateY(180deg)", backfaceVisibility: "hidden" }}
        >
          <p className="text-sm text-white">{snippet.description}</p>
          <div className="text-xs text-slate-400">例：{snippet.example}</div>
          <div className="text-[11px] text-cyan-300">{snippet.citation}</div>
        </div>
      </motion.div>
    </motion.div>
  );
};

type Props = { data: PostAnalysis };

export const StrategyPatternCard = ({ data }: Props) => {
  return (
    <CardShell title="Strategy Pattern" subtitle="L2 策略卡" accent="amber">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {data.strategies.map((snippet) => (
          <StrategyChip key={snippet.name} snippet={snippet} />
        ))}
      </div>
    </CardShell>
  );
};

export default StrategyPatternCard;
