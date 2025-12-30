import { CardShell } from "./CardShell";
import { PostAnalysis } from "../../types/analysis";

type Props = {
  data: PostAnalysis;
};

export const EventCoverCard = ({ data }: Props) => {
  const { section1, meta, quant, stats } = data;
  return (
    <CardShell
      title="Event Cover"
      subtitle="Executive snapshot"
      accent="cyan"
      className="bg-gradient-to-br from-slate-900 to-slate-950"
    >
      <div className="space-y-3">
        <h2 className="text-2xl font-extrabold leading-tight">
          {section1.executiveSummary}
        </h2>
        <p className="text-subtle text-sm leading-relaxed">
          {section1.phenomenonSpotlight}
        </p>
        <div className="flex flex-wrap gap-3 text-sm text-subtle">
          <span className="rounded-full border border-slate-700 px-3 py-1 font-semibold text-white">
            Post #{meta.Post_ID}
          </span>
          <span className="rounded-full border border-amber-400/50 bg-amber-400/10 px-3 py-1">
            Emotion: {quant.Primary_Emotion}
          </span>
          <span className="rounded-full border border-cyan-400/50 bg-cyan-400/10 px-3 py-1">
            Views: {stats.Views.toLocaleString()}
          </span>
          <span className="rounded-full border border-pink-400/50 bg-pink-400/10 px-3 py-1">
            Likes: {stats.Likes.toLocaleString()} · Replies: {stats.Replies.toLocaleString()}
          </span>
        </div>
        <div className="text-xs text-subtle">Scroll → 探索完整分析宇宙</div>
      </div>
    </CardShell>
  );
};

export default EventCoverCard;
