import { MetricsBlock } from "../../types/analysis";
import { CardShell } from "./CardShell";

type Props = { metrics?: MetricsBlock };

const formatNumber = (val?: number) => {
  if (val === undefined || val === null || Number.isNaN(val)) return "—";
  return val.toLocaleString();
};

export const EngagementCard = ({ metrics }: Props) => {
  const likes = metrics?.likes ?? 0;
  const views = metrics?.views ?? 0;
  const replies = metrics?.replies ?? 0;
  const ctr = views > 0 ? (likes / Math.max(views, 1)) * 100 : 0;

  return (
    <CardShell
      title="互動數據｜Engagement"
      subtitle="Likes / Replies / Views"
      accent={metrics?.high_impact ? "amber" : "cyan"}
    >
      <div className="space-y-4 text-white">
        {metrics?.high_impact && (
          <div className="inline-flex rounded-full bg-amber-500/20 px-3 py-1 text-xs font-semibold text-amber-100">
            High Impact
          </div>
        )}
        {!metrics && <p className="text-sm text-slate-300">尚無互動資料。</p>}
        {metrics && (
          <>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
                <p className="text-xs text-slate-400">Likes</p>
                <p className="text-xl font-bold">{formatNumber(likes)}</p>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
                <p className="text-xs text-slate-400">Replies</p>
                <p className="text-xl font-bold">{formatNumber(replies)}</p>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
                <p className="text-xs text-slate-400">Views</p>
                <p className="text-xl font-bold">{formatNumber(views)}</p>
              </div>
            </div>
            <div className="rounded-xl border border-cyan-400/40 bg-cyan-500/10 p-3 text-center">
              <p className="text-xs uppercase tracking-wide text-cyan-100">CTR (Likes / Views)</p>
              <p className="text-2xl font-semibold text-cyan-50">{`${ctr.toFixed(1)}%`}</p>
            </div>
            {likes === 0 && replies === 0 && views > 0 && (
              <p className="mt-3 text-xs text-slate-400">
                目前只有瀏覽量被紀錄，互動數據仍為 0。這類「只睇不讚」的貼文通常屬於被動觀看／潛水行為。
              </p>
            )}
            {views === 0 && (
              <p className="mt-3 text-xs text-slate-400">尚未取得可靠互動數據。</p>
            )}
          </>
        )}
      </div>
    </CardShell>
  );
};

export default EngagementCard;
