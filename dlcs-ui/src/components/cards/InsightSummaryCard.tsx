import { CardShell } from "./CardShell";
import { PostAnalysis } from "../../types/analysis";

type Props = { data: PostAnalysis };

export const InsightSummaryCard = ({ data }: Props) => {
  return (
    <CardShell title="Strategic Implication" subtitle="戰略意涵" accent="cyan">
      <blockquote className="rounded-2xl bg-gradient-to-br from-slate-900 to-slate-800 p-4 text-lg font-semibold text-white shadow-inner">
        「這不是一則單純的政治嘲諷，而是一種低風險、高傳染性的日常化抵抗。」
      </blockquote>
      <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
          <div className="text-xs uppercase text-subtle">信任侵蝕</div>
          <p className="text-white">{data.section1.strategicImplication}</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
          <div className="text-xs uppercase text-subtle">Weapons of the Weak</div>
          <p className="text-white">日常嘲諷作為低風險抵抗，參照 Scott (1985)。</p>
        </div>
      </div>
    </CardShell>
  );
};

export default InsightSummaryCard;
