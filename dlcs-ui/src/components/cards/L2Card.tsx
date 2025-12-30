import { AnalysisLayer } from "../../types/analysis";
import { CardShell } from "./CardShell";

interface L2CardProps {
  layer?: AnalysisLayer | null;
}

export function L2Card({ layer }: L2CardProps) {
  const title = layer?.title || "L2：批判性策略分析 / Critical Strategy";
  const body = (layer?.body || layer?.summary || "").trim();

  return (
    <CardShell title={title} accent="amber">
      <div className="flex items-start gap-3 border-l-4 border-violet-500 pl-3">
        <div className="mt-1 h-2 w-2 rounded-full bg-violet-300" />
        <div className="space-y-1">
          {!body ? (
            <p className="text-sm text-slate-400">
              此貼文的 L2（批判性策略分析）摘要尚未從完整報告中抽取；分析模型仍在優化中。
            </p>
          ) : (
            <p className="whitespace-pre-line text-sm leading-relaxed text-white">{body}</p>
          )}
        </div>
      </div>
    </CardShell>
  );
}

export default L2Card;
