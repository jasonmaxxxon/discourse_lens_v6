import { DiscoveryInfo } from "../../types/analysis";
import { CardShell } from "./CardShell";

interface DiscoveryCardProps {
  discovery: DiscoveryInfo | null;
  fallbackTitle?: string;
}

const DiscoveryCard = ({ discovery, fallbackTitle }: DiscoveryCardProps) => {
  const subVariant = discovery?.sub_variant_name || fallbackTitle || "未命名現象";
  const isNew = discovery?.is_new_phenomenon;
  const desc = discovery?.phenomenon_description || "尚未提供詳細現象描述。";

  if (!discovery) {
    return (
      <CardShell title="現象焦點｜Phenomenon Spotlight" accent="cyan" className="h-full">
        <p className="text-sm text-slate-400">尚無現象數據。</p>
      </CardShell>
    );
  }

  return (
    <CardShell title="現象焦點｜Phenomenon Spotlight" accent="cyan" className="h-full">
      <div className="relative h-full flex flex-col justify-between">
        <div className="pointer-events-none absolute right-6 bottom-4 text-7xl md:text-8xl font-bold text-slate-700/20">
          01
        </div>

        <div className="flex items-center gap-3 mb-6">
          <span className="text-[11px] tracking-[0.25em] uppercase text-slate-400">
            COLLECTIVE MEME ｜ 集體幽默
          </span>
          {subVariant && (
            <span className="rounded-full border border-indigo-400/60 bg-indigo-500/10 px-3 py-1 text-xs text-indigo-100">
              {subVariant}
            </span>
          )}
          {isNew && (
            <span className="rounded-full border border-emerald-400/60 bg-emerald-500/20 px-3 py-1 text-[11px] font-semibold text-emerald-100">
              NEW PATTERN
            </span>
          )}
        </div>

        <div className="flex flex-col gap-4 md:gap-6">
          <h1 className="text-3xl md:text-4xl font-semibold leading-tight">{subVariant}</h1>
          <p className="text-sm md:text-base italic font-serif text-slate-200/90 leading-relaxed line-clamp-4">
            {desc}
          </p>
        </div>

        <div className="mt-6">
          <div className="w-full h-32 md:h-40 border-2 border-dashed border-slate-700 rounded-2xl flex items-center justify-center">
            <div className="text-xs md:text-sm text-slate-500 tracking-[0.2em] uppercase">
              pixel art placeholder
            </div>
          </div>
        </div>
      </div>
    </CardShell>
  );
};

export default DiscoveryCard;
