import { CardShell } from "./CardShell";
import { PostAnalysis } from "../../types/analysis";

const columns = [
  { label: "Head", support: 62, oppose: 10, cynical: 28 },
  { label: "Mid", support: 48, oppose: 12, cynical: 40 },
  { label: "Tail", support: 35, oppose: 8, cynical: 57 },
];

type Props = { data: PostAnalysis };

export const CommentDynamicsCard = ({ data }: Props) => {
  const spotlight = data.section1.l3Battlefield;
  const topComment = data.commentSamples[0];
  return (
    <CardShell title="Collective Dynamics" subtitle="Head / Mid / Tail" accent="amber">
      <p className="text-sm text-subtle mb-3">{spotlight}</p>
      <div className="grid grid-cols-3 gap-3">
        {columns.map((col) => {
          const total = col.support + col.oppose + col.cynical || 1;
          return (
            <div key={col.label} className="rounded-xl bg-slate-900/60 p-3 text-sm">
              <div className="mb-2 font-semibold text-white">{col.label}</div>
              <div className="space-y-1 text-xs text-subtle">
                <div className="flex justify-between">
                  <span>Support</span>
                  <span>{col.support}%</span>
                </div>
                <div className="h-1.5 w-full rounded-full bg-slate-800">
                  <div className="h-1.5 rounded-full bg-emerald-400" style={{ width: `${(col.support / total) * 100}%` }} />
                </div>
                <div className="flex justify-between">
                  <span>Oppose</span>
                  <span>{col.oppose}%</span>
                </div>
                <div className="h-1.5 w-full rounded-full bg-slate-800">
                  <div className="h-1.5 rounded-full bg-rose-400" style={{ width: `${(col.oppose / total) * 100}%` }} />
                </div>
                <div className="flex justify-between">
                  <span>Cynical</span>
                  <span>{col.cynical}%</span>
                </div>
                <div className="h-1.5 w-full rounded-full bg-slate-800">
                  <div className="h-1.5 rounded-full bg-amber-400" style={{ width: `${(col.cynical / total) * 100}%` }} />
                </div>
              </div>
            </div>
          );
        })}
      </div>
      {topComment && (
        <div className="mt-3 rounded-xl border border-slate-800 bg-slate-900/70 p-3 text-sm text-white">
          <div className="flex items-center justify-between text-xs text-subtle">
            <span>@{topComment.author.replace(/^@/, "")}</span>
            <span>❤️ {topComment.likes}</span>
          </div>
          <p className="mt-2 text-white">{topComment.text}</p>
        </div>
      )}
    </CardShell>
  );
};

export default CommentDynamicsCard;
