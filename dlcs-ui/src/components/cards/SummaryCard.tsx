import { AnalysisMeta, AnalysisSummary } from "../../types/analysis";
import { CardShell } from "./CardShell";

type Props = {
  summary: AnalysisSummary;
  meta?: AnalysisMeta;
};

export const SummaryCard = ({ summary, meta }: Props) => {
  const frames = summary.key_frames || [];

  return (
    <CardShell title="現象摘要｜Phenomenon Spotlight" subtitle="摘要與焦點" accent="cyan">
      <div className="max-h-[540px] w-[320px] overflow-y-auto rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-sm leading-relaxed text-white">
        <p className="text-base font-semibold text-white">{summary.one_line || "尚無摘要"}</p>
        <p className="mt-2 text-xs uppercase tracking-wide text-slate-400">
          敘事類型｜Narrative: {summary.narrative_type || "未提供"}
        </p>
        {frames.length > 0 && (
          <div className="mt-3 space-y-1">
            <p className="text-[11px] uppercase tracking-wide text-slate-400">Key Frames</p>
            <ul className="space-y-1 text-sm text-slate-100">
              {frames.map((frame, idx) => (
                <li key={`${frame}-${idx}`} className="rounded-md bg-slate-800/60 px-2 py-1">
                  {frame}
                </li>
              ))}
            </ul>
          </div>
        )}
        {meta && (meta.author || meta.url || meta.captured_at) && (
          <div className="mt-4 space-y-1 text-xs text-slate-300">
            {meta.author && <p>作者：{meta.author}</p>}
            {meta.url && (
              <p className="truncate">
                來源：<span className="text-cyan-200">{meta.url}</span>
              </p>
            )}
            {meta.captured_at && <p>擷取時間：{meta.captured_at}</p>}
          </div>
        )}
      </div>
    </CardShell>
  );
};

export default SummaryCard;
