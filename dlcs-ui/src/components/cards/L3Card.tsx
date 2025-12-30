import { AnalysisLayer } from "../../types/analysis";
import { CardShell } from "./CardShell";

interface L3CardProps {
  layer?: AnalysisLayer | null;
}

export function L3Card({ layer }: L3CardProps) {
  const title = layer?.title || "L3：輿論戰場與派系分析 / Battlefield & Factions";
  const summary = (layer?.body || layer?.summary || "").trim();

  return (
    <CardShell title={title} accent="pink">
      <div className="flex items-start gap-3 border-l-4 border-rose-500 pl-3">
        <div className="mt-1 h-2 w-2 rounded-full bg-rose-300" />
        <div className="space-y-1">
          {!summary ? (
            <p className="text-sm text-slate-400">
              此貼文的 L3（戰場與派系分析）摘要尚未從完整報告中抽取；分析模型仍在優化中。
            </p>
          ) : (
            <p className="whitespace-pre-line text-sm leading-relaxed text-white">{summary}</p>
          )}
        </div>
      </div>
    </CardShell>
  );
}

export default L3Card;
