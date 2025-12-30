import { StrategyBlock } from "../../types/analysis";
import { CardShell } from "./CardShell";

type Props = { strategies: StrategyBlock };

export const StrategyDetailCard = ({ strategies }: Props) => {
  const secondary = strategies?.secondary || [];
  const tactics = strategies?.tactics || [];

  return (
    <CardShell title="策略細節｜Strategy Details" subtitle="Primary / Secondary / Tactics" accent="pink">
      <div className="space-y-3 text-sm text-white">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-400">Primary Strategy</p>
          <p className="text-lg font-semibold">{strategies?.primary || "未提供"}</p>
        </div>

        {secondary.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs uppercase tracking-wide text-slate-400">Secondary</p>
            <div className="flex flex-wrap gap-2">
              {secondary.map((item, idx) => (
                <span
                  key={`${item}-${idx}`}
                  className="rounded-full border border-slate-700 bg-slate-800/80 px-3 py-1 text-xs text-slate-100"
                >
                  {item}
                </span>
              ))}
            </div>
          </div>
        )}

        {tactics.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs uppercase tracking-wide text-slate-400">Tactics</p>
            <ul className="list-disc space-y-1 pl-5 text-slate-100">
              {tactics.map((item, idx) => (
                <li key={`${item}-${idx}`}>{item}</li>
              ))}
            </ul>
          </div>
        )}

        {secondary.length === 0 && tactics.length === 0 && (
          <p className="text-slate-300">尚無次要策略或戰術描述。</p>
        )}
      </div>
    </CardShell>
  );
};

export default StrategyDetailCard;
