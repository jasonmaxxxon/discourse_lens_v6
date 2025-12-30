import { PostAnalysis } from "../../types/analysis";

export const Header = ({ data }: { data: PostAnalysis }) => {
  const { meta, quant } = data;
  return (
    <header className="flex flex-col gap-3 rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-2xl font-bold">DiscourseLens</div>
          <div className="text-subtle text-sm">Narrative Intelligence Playground</div>
        </div>
        <div className="text-right text-xs text-subtle">Post #{meta.Post_ID}</div>
      </div>
      <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
        <InfoPill label="Primary Emotion" value={quant.Primary_Emotion} />
        <InfoPill label="Homogeneity" value={quant.Homogeneity_Score.toFixed(2)} />
        <InfoPill label="Influence" value={quant.Author_Influence} />
        <InfoPill label="Sector" value={quant.Sector_ID} />
      </div>
    </header>
  );
};

const InfoPill = ({ label, value }: { label: string; value: string }) => (
  <div className="rounded-xl border border-slate-800 bg-slate-950/70 px-3 py-2 text-white">
    <div className="text-[11px] uppercase tracking-wide text-subtle">{label}</div>
    <div className="text-base font-semibold">{value}</div>
  </div>
);

export default Header;
