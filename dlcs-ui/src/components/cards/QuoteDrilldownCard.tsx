import { CardShell } from "./CardShell";
import { PostAnalysis } from "../../types/analysis";

const Tag = ({ label }: { label: string }) => (
  <span className="rounded-full bg-slate-800 px-2 py-1 text-[11px] text-cyan-200">{label}</span>
);

type Props = { data: PostAnalysis };

export const QuoteDrilldownCard = ({ data }: Props) => {
  return (
    <CardShell title="Representative Comments" subtitle="語料鑽取" accent="cyan">
      <div className="space-y-3">
        {data.commentSamples.map((c) => (
          <div key={c.author + c.text} className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
            <div className="flex items-center justify-between text-xs text-subtle">
              <span>{c.author}</span>
              <span>❤️ {c.likes}</span>
            </div>
            <p className="mt-2 text-sm text-white">{c.text}</p>
            <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-subtle">
              {c.tags?.map((t) => (
                <Tag key={t} label={t} />
              ))}
              {c.faction && <Tag label={c.faction} />}
            </div>
          </div>
        ))}
      </div>
    </CardShell>
  );
};

export default QuoteDrilldownCard;
