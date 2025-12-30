import { CardShell } from "./CardShell";
import { PostAnalysis } from "../../types/analysis";

const dotColors = ["#22d3ee", "#f97316", "#a855f7", "#10b981"];

type Props = { data: PostAnalysis };

export const NarrativeShiftCard = ({ data }: Props) => {
  return (
    <CardShell title="Narrative Shift" subtitle="敘事轉移" accent="amber">
      <div className="flex items-center gap-3 overflow-x-auto pb-2">
        {data.narrativeShift.map((n, idx) => (
          <div key={n.stage} className="flex items-center gap-2">
            <div className="flex h-12 w-12 items-center justify-center rounded-full border border-slate-700 bg-slate-900 text-center text-xs font-semibold" style={{ color: dotColors[idx % dotColors.length] }}>
              {n.stage}
            </div>
            <div className="text-sm text-white">{n.label}</div>
            {idx < data.narrativeShift.length - 1 && (
              <div className="w-10 border-t border-dashed border-slate-700" aria-hidden />
            )}
          </div>
        ))}
      </div>
      <p className="mt-3 text-sm text-subtle">
        從官方式祝賀轉向功能性嘲諷，最終成為對制度的犬儒批評與無力感：{data.section1.phenomenonSpotlight}
      </p>
    </CardShell>
  );
};

export default NarrativeShiftCard;
