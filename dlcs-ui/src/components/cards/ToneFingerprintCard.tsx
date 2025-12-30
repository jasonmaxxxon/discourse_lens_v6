import { CardShell } from "./CardShell";
import { PostAnalysis } from "../../types/analysis";

const ToneBar = ({ label, value }: { label: string; value: number }) => (
  <div className="space-y-1">
    <div className="flex items-center justify-between text-xs text-subtle">
      <span>{label}</span>
      <span className="font-semibold text-white">{Math.round(value * 100)}%</span>
    </div>
    <div className="h-2 w-full rounded-full bg-slate-800">
      <div
        className="h-2 rounded-full bg-gradient-to-r from-cyan-400 to-emerald-400"
        style={{ width: `${Math.min(100, Math.max(0, value * 100))}%` }}
      />
    </div>
  </div>
);

type Props = { data: PostAnalysis };

export const ToneFingerprintCard = ({ data }: Props) => {
  const t = data.tone;
  return (
    <CardShell title="Tone Fingerprint" subtitle="L1 語氣指紋" accent="pink">
      <div className="grid grid-cols-2 gap-3">
        <ToneBar label="Assertiveness" value={t.assertiveness} />
        <ToneBar label="Cynicism" value={t.cynicism} />
        <ToneBar label="Playfulness" value={t.playfulness} />
        <ToneBar label="Contempt" value={t.contempt} />
      </div>
      <div className="mt-3 space-y-2 text-sm text-subtle">
        <p className="text-white">{t.description}</p>
        <p className="text-xs text-slate-400">例句：{t.example}</p>
        <div className="flex gap-2 text-[11px] text-cyan-300">
          <span className="rounded-full bg-cyan-400/10 px-2 py-1">Searle 1969</span>
          <span className="rounded-full bg-cyan-400/10 px-2 py-1">Illocutionary Acts</span>
        </div>
      </div>
    </CardShell>
  );
};

export default ToneFingerprintCard;
