import { CardShell } from "./CardShell";
import { PostAnalysis } from "../../types/analysis";

const bars = [
  { key: "Boundary Strength", value: 0.78 },
  { key: "Symbolic Power Erosion", value: 0.86 },
  { key: "Demoralization", value: 0.73 },
  { key: "Outgroup Focus", value: 0.42 },
];

type Props = { data: PostAnalysis };

export const IdeologyCompressionCard = ({ data }: Props) => {
  return (
    <CardShell title="Ideology Compression" subtitle="L3 boundary / power" accent="cyan">
      <div className="space-y-3">
        {bars.map((b) => (
          <div key={b.key} className="space-y-1">
            <div className="flex items-center justify-between text-sm text-subtle">
              <span>{b.key}</span>
              <span className="font-semibold text-white">{Math.round(b.value * 100)}%</span>
            </div>
            <div className="h-2 w-full rounded-full bg-slate-800">
              <div
                className="h-2 rounded-full bg-gradient-to-r from-emerald-400 to-cyan-400"
                style={{ width: `${b.value * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
      <p className="mt-3 text-sm text-white">
        這個場域不是衝突戰場，而是高度同質的犬儒迴聲室。{data.section1.l3Battlefield}
      </p>
    </CardShell>
  );
};

export default IdeologyCompressionCard;
