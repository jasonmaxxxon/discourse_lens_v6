import React, { useMemo } from "react";
import { NarrativeAnalysis } from "../types/narrative";
import { SlotStatus } from "../utils/slotContracts";

type NarrativeDetailScreenProps = {
  analysisJson: NarrativeAnalysis;
  slotStatus?: Record<string, SlotStatus>;
};

const formatMetric = (val?: number) => {
  if (!val || !Number.isFinite(val)) return "0";
  if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}m`;
  if (val >= 1_000) return `${(val / 1_000).toFixed(1)}k`;
  return `${val}`;
};

const relativeTimeFromISO = (iso?: string) => {
  if (!iso) return "2h ago";
  const then = new Date(iso).getTime();
  const now = Date.now();
  if (Number.isNaN(then)) return "2h ago";
  const diff = Math.max(0, now - then);
  const minutes = Math.floor(diff / 60000);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 48) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
};

const computeBubbleStyle = (fallback: { top: string; left: string }, tone_x?: number, tone_y?: number) => {
  if (Number.isFinite(tone_x) && Number.isFinite(tone_y)) {
    const x = 10 + (tone_x as number) * 60;
    const y = 10 + (tone_y as number) * 60;
    return { top: `${y}%`, left: `${x}%` };
  }
  return fallback;
};

const voiceColor = (id: string | undefined) => {
  const lower = (id || "").toLowerCase();
  if (lower.includes("cynic")) return "yellow";
  if (lower.includes("believer")) return "primary";
  if (lower.includes("troll")) return "cyan";
  return "neutral";
};

export function NarrativeDetailScreen({ analysisJson, slotStatus }: NarrativeDetailScreenProps) {
  const { post, metrics, battlefield, insight_deck } = analysisJson;
  const factions = useMemo(() => {
    const list = insight_deck?.war_room_factions?.length ? insight_deck.war_room_factions : battlefield.factions;
    return (list || []).slice().sort((a, b) => (b.share_pct ?? 0) - (a.share_pct ?? 0));
  }, [insight_deck, battlefield]);

  const evidenceFactions = factions.slice(0, 3);
  const phenomenon = insight_deck.phenomenon;
  const vibe = insight_deck.vibe_check;
  const l1 = insight_deck.l1_analysis;

  return (
    <div className="bg-background-light dark:bg-background-dark text-white font-display overflow-hidden h-screen flex flex-col relative">
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-20%] left-[-20%] w-[80%] h-[80%] bg-primary/20 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-20%] right-[-20%] w-[80%] h-[80%] bg-neon-cyan/10 rounded-full blur-[120px]" />
      </div>

      <header className="relative z-20 flex items-center justify-between px-6 pt-6 pb-2">
        <button className="flex items-center justify-center size-10 rounded-full bg-white/5 hover:bg-white/10 transition-colors">
          <span className="material-symbols-outlined text-white">arrow_back</span>
        </button>
        <h2 className="text-sm font-bold tracking-widest uppercase text-white/70">Narrative Intel</h2>
        <button className="flex items-center justify-center size-10 rounded-full bg-white/5 hover:bg-white/10 transition-colors">
          <span className="material-symbols-outlined text-white">ios_share</span>
        </button>
      </header>

      <main className="relative z-10 flex flex-col h-full overflow-y-auto no-scrollbar pb-8">
        {/* Anchor Post */}
        <section className="flex-none px-6 py-4 mb-2">
          <div className="glass-panel rounded-2xl p-6 shadow-2xl shadow-black/50 relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-primary/20 blur-[60px] rounded-full pointer-events-none" />
            <div className="flex items-start gap-4 relative z-10">
              <div className="size-10 rounded-full border-2 border-primary p-0.5 shrink-0">
                <img
                  alt="User avatar"
                  className="w-full h-full rounded-full object-cover"
                  src={
                    post.author_avatar_url ||
                    "https://lh3.googleusercontent.com/aida-public/AB6AXuD0mQ5goTSEbbWMnRGi_pH8wkngIenNk_3d6ssUdbAfjQ_O2nQpdmnICCHQCezmhuy9SzIg0p-hynEH7cq0zr7rMmRIKkykMiDVC6DaMGtWF0Nhc012QQ1mrusLj0bxAC7EkqIxDerCWtkp0nzxumV5F12KAaTWdULdZvmDOTXy4G-xecfL6ksEhYKVxUrtMv5EtyK1gaqmFZ6z_-L7MyM4HKGZFhNF1hFjrlT26Cs5N74chEL4VVgCyBPlhTl59LrF1MPANlxW3aQF"
                  }
                />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex justify-between items-center mb-1">
                  <p className="font-bold text-white text-base">{post.author_handle}</p>
                  <span className="material-symbols-outlined text-white/50 text-[18px]">more_horiz</span>
                </div>
                <p className="font-serif text-2xl leading-normal text-white mb-2 font-medium"> {post.text} </p>
                <div className="flex items-center gap-2 mt-2">
                  {post.is_anchor && (
                    <span className="text-xs font-bold text-primary flex items-center gap-1 bg-black/40 px-2 py-1 rounded backdrop-blur-sm border border-primary/20">
                      <span className="material-symbols-outlined text-[14px]">link</span> ANCHOR SOURCE
                    </span>
                  )}
                  <span className="text-xs text-gray-400">{relativeTimeFromISO(post.timestamp_iso)}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Metrics */}
        <section className="flex-none px-6 mb-4">
          <div className="glass-panel rounded-xl p-4 flex justify-around items-center border-t border-white/20">
            <div className="text-center group cursor-pointer">
              <div className="text-neon-cyan font-display text-xl font-bold mb-1 group-hover:scale-110 transition-transform">
                {formatMetric(metrics.total_likes)}
              </div>
              <div className="text-[10px] uppercase tracking-widest text-gray-400">Likes</div>
            </div>
            <div className="w-px h-8 bg-white/10" />
            <div className="text-center group cursor-pointer">
              <div className="text-neon-purple font-display text-xl font-bold mb-1 group-hover:scale-110 transition-transform">
                {formatMetric(metrics.total_views)}
              </div>
              <div className="text-[10px] uppercase tracking-widest text-gray-400">Views</div>
            </div>
            <div className="w-px h-8 bg-white/10" />
            <div className="text-center group cursor-pointer">
              <div className="text-neon-yellow font-display text-xl font-bold mb-1 group-hover:scale-110 transition-transform">
                {formatMetric(metrics.total_engagement)}
              </div>
              <div className="text-[10px] uppercase tracking-widest text-gray-400">Engage</div>
            </div>
          </div>
        </section>

        {/* Voice Map */}
        <section className="flex-none px-6 mb-6">
          <div className="flex items-center gap-2 mb-3 px-1">
            <span className="material-symbols-outlined text-white/50 text-sm">bubble_chart</span>
            <h3 className="text-xs font-bold tracking-[0.2em] text-white/70 uppercase">Key Community Voice Map</h3>
          </div>
          <div className="glass-panel rounded-xl p-6 relative overflow-hidden h-64 flex items-center justify-center">
            <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:20px_20px]" />
            <span className="absolute left-2 top-1/2 -translate-y-1/2 -rotate-90 text-[9px] text-white/30 uppercase tracking-widest">
              Sarcasm
            </span>
            <span className="absolute bottom-2 left-1/2 -translate-x-1/2 text-[9px] text-white/30 uppercase tracking-widest">
              Constructive
            </span>
            {slotStatus?.segments?.ok === false && (
              <div className="text-sm text-slate-400">資料不足：{slotStatus.segments.missing.join(", ") || "segments empty"}</div>
            )}
            {factions.length === 0 && (
              <div className="text-sm text-slate-400">No factions detected for this post yet.</div>
            )}
            {factions.slice(0, 3).map((f, idx) => {
              const pct = Math.round(f.share_pct || 0);
              const styles = [
                computeBubbleStyle({ top: "20%", left: "20%" }, f.tone_x, f.tone_y),
                computeBubbleStyle({ top: "75%", left: "70%" }, f.tone_x, f.tone_y),
                computeBubbleStyle({ top: "30%", left: "80%" }, f.tone_x, f.tone_y),
              ];
              const sizeClass = ["size-24", "size-20", "size-14"][idx] || "size-16";
              const palette =
                idx === 0
                  ? { bg: "bg-neon-yellow/20", border: "border-neon-yellow/60", text: "text-neon-yellow", glow: "bubble-glow-yellow" }
                  : idx === 1
                  ? { bg: "bg-primary/20", border: "border-primary/60", text: "text-primary", glow: "bubble-glow-primary" }
                  : { bg: "bg-neon-cyan/20", border: "border-neon-cyan/60", text: "text-neon-cyan", glow: "bubble-glow-cyan" };
              return (
                <div
                  key={f.id}
                  className="absolute"
                  style={{ top: styles[idx]?.top, left: styles[idx]?.left }}
                >
                  <div
                    className={`${sizeClass} rounded-full ${palette.bg} border ${palette.border} ${palette.glow} backdrop-blur-sm flex flex-col items-center justify-center p-2 text-center relative z-10 cursor-pointer transition-transform hover:scale-110`}
                  >
                    <span className={`material-symbols-outlined ${palette.text} text-sm mb-1`}>chat</span>
                    <span className="text-[10px] font-bold text-white uppercase tracking-wider leading-tight">
                      {f.label}
                    </span>
                    <span className={`text-[9px] ${palette.text} mt-0.5 opacity-80`}>{pct}%</span>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Example Evidence */}
        <section className="flex-none px-6 mb-6">
          <div className="flex items-center gap-2 mb-3 px-1">
            <span className="material-symbols-outlined text-white/50 text-sm">format_quote</span>
            <h3 className="text-xs font-bold tracking-[0.2em] text-white/70 uppercase">Example Evidence</h3>
          </div>
          <div className="space-y-3">
            {evidenceFactions.map((f, idx) => {
              const sample = f.samples?.[0];
              const color = voiceColor(f.id);
              const palette =
                color === "yellow"
                  ? { text: "text-neon-yellow", badge: "bg-neon-yellow/10", border: "border-l-neon-yellow" }
                  : color === "primary"
                  ? { text: "text-primary", badge: "bg-primary/10", border: "border-l-primary" }
                  : color === "cyan"
                  ? { text: "text-neon-cyan", badge: "bg-neon-cyan/10", border: "border-l-neon-cyan" }
                  : { text: "text-white", badge: "bg-white/10", border: "border-l-white/20" };
              return (
                <div
                  key={`${f.id}-${idx}`}
                  className={`glass-panel rounded-lg p-3 border-l-2 ${palette.border} flex gap-3 items-start hover:bg-white/5 transition-colors cursor-pointer group`}
                >
                  <div className="bg-black/30 p-1.5 rounded shrink-0 border border-white/10 mt-1">
                    <span className={`material-symbols-outlined ${palette.text} text-xs group-hover:scale-125 transition-transform`}>
                      chat_bubble
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-baseline mb-1">
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-[10px] font-bold uppercase tracking-wider ${palette.text} ${palette.badge} px-1.5 py-0.5 rounded`}
                        >
                          {f.label}
                        </span>
                        <span className="text-[10px] text-gray-500">@{sample?.author_handle || "anon"}</span>
                      </div>
                      <span className="text-[9px] text-gray-600">
                        {sample ? `${formatMetric(sample.likes)} likes` : "—"}
                      </span>
                    </div>
                    <p className="text-sm text-gray-200 font-serif leading-snug italic">
                      {sample?.text || "No representative comment captured."}
                    </p>
                  </div>
                </div>
              );
            })}
            {evidenceFactions.length === 0 && (
              <div className="glass-panel rounded-lg p-3 text-sm text-slate-400 border border-white/10">
                No representative comments captured.
              </div>
            )}
          </div>
        </section>

        <div className="w-0.5 h-6 bg-gradient-to-b from-white/20 to-transparent mx-auto mb-2" />

        {/* Insight Deck */}
        <section className="flex-1 w-full flex flex-col justify-center min-h-0">
          <div className="px-6 mb-3 flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-sm animate-pulse">emergency_home</span>
            <h3 className="text-xs font-bold tracking-[0.2em] text-primary uppercase">Insight Deck</h3>
          </div>
          <div className="flex overflow-x-auto snap-x snap-mandatory px-6 gap-4 pb-8 no-scrollbar items-stretch h-full">
            {/* Phenomenon */}
            <div className="snap-center shrink-0 w-[85vw] max-w-sm h-full relative rounded-3xl overflow-hidden border border-white/10 group">
              <div
                className="absolute inset-0 bg-cover bg-center transition-transform duration-700 group-hover:scale-105"
                style={{
                  backgroundImage: `url('${
                    phenomenon.cover_image_url ||
                    "https://lh3.googleusercontent.com/aida-public/AB6AXuDKSv1Tez9uCo9_fFiU9w0GSCUMtsFMbvpVc44AHtPZ44Nt3_zCW7XfdiVpWlt9WbjCXy29Ce-UutF0ph4M4ZJb84T-S-0OL7lNBEd-AqVBKZ5oelWwGyyvN5KF2AxWh7Vsj5CQSocq-FZ_xtLcuMB0KUV4YwpijYHfXTCEXVDnjRGptXKLGZ1fXaTwIrgL48dqHaIryYHRrWLf-z0CFB9lz04ZBOEj5SaFLjO4SR4FIdb4_DMSk9Yi5vj5g7bgpupaP9Td52Pq7R8i"
                  }')`,
                }}
              />
              <div className="absolute inset-0 bg-gradient-to-t from-background-dark via-background-dark/80 to-transparent" />
              <div className="absolute inset-0 p-6 flex flex-col justify-between">
                <div className="flex justify-between items-start">
                  <div className="px-3 py-1 bg-white text-black font-bold text-xs tracking-widest uppercase">
                    Issue #{phenomenon.issue_id || "—"}
                  </div>
                  <div className="text-white/20 font-display text-6xl font-bold -mt-2 -mr-2">01</div>
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="size-2 bg-primary rounded-full animate-ping" />
                    <span className="text-primary font-bold text-xs tracking-widest uppercase">
                      {phenomenon.subtitle || "Trending Now"}
                    </span>
                  </div>
                  <h2 className="text-4xl font-bold leading-[0.9] text-white mb-2 neon-text-shadow">
                    {phenomenon.title}
                  </h2>
                  <p className="font-serif text-gray-300 text-sm leading-relaxed border-l-2 border-primary pl-3 mt-4">
                    {phenomenon.description}
                  </p>
                </div>
              </div>
            </div>

            {/* Vibe Check */}
            <div className="snap-center shrink-0 w-[85vw] max-w-sm h-full relative rounded-3xl overflow-hidden border border-white/10 bg-[#1a101f]">
              <div className="p-6 pb-2 border-b border-white/5">
                <div className="flex justify-between items-center mb-1">
                  <h3 className="text-2xl font-bold uppercase tracking-tight text-white">Vibe Check</h3>
                  <span className="material-symbols-outlined text-neon-yellow">equalizer</span>
                </div>
                <p className="text-xs text-gray-400 uppercase tracking-widest">Sentiment Analysis</p>
              </div>
              <div className="p-6 flex flex-col justify-center h-full gap-8 -mt-8">
                <div>
                  <div className="flex justify-between items-end mb-2">
                    <span className="text-neon-yellow font-bold text-lg tracking-wider">CYNICISM</span>
                    <span className="text-neon-yellow font-display text-3xl font-bold">
                      {Math.round(vibe.cynicism_pct || 0)}%
                    </span>
                  </div>
                  <div className="h-6 w-full bg-black/50 rounded-sm p-1 border border-white/10">
                    <div
                      className="h-full bg-neon-yellow shadow-[0_0_15px_rgba(204,255,0,0.6)] relative overflow-hidden"
                      style={{ width: `${Math.round(vibe.cynicism_pct || 0)}%` }}
                    >
                      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0IiBoZWlnaHQ9IjQiPgo8cmVjdCB3aWR0aD0iNCIgaGVpZ2h0PSI0IiBmaWxsPSIjMDAwIiBmaWxsLW9wYWNpdHk9IjAuMSIvPgo8L3N2Zz4=')] opacity-50" />
                    </div>
                  </div>
                  <p className="font-serif text-xs text-gray-400 mt-2 italic">
                    {vibe.cynicism_caption || '"Mostly sarcastic responses detected."'}
                  </p>
                </div>
                <div>
                  <div className="flex justify-between items-end mb-2">
                    <span className="text-neon-cyan font-bold text-lg tracking-wider">HOPE</span>
                    <span className="text-neon-cyan font-display text-3xl font-bold">
                      {Math.round(vibe.hope_pct || 0)}%
                    </span>
                  </div>
                  <div className="h-6 w-full bg-black/50 rounded-sm p-1 border border-white/10">
                    <div
                      className="h-full bg-neon-cyan shadow-[0_0_15px_rgba(0,243,255,0.6)] relative overflow-hidden"
                      style={{ width: `${Math.round(vibe.hope_pct || 0)}%` }}
                    >
                      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0IiBoZWlnaHQ9IjQiPgo8cmVjdCB3aWR0aD0iNCIgaGVpZ2h0PSI0IiBmaWxsPSIjMDAwIiBmaWxsLW9wYWNpdHk9IjAuMSIvPgo8L3N2Zz4=')] opacity-50" />
                    </div>
                  </div>
                  <p className="font-serif text-xs text-gray-400 mt-2 italic">
                    {vibe.hope_caption || '"Minority believes it\'s genuine art."'}
                  </p>
                </div>
              </div>
              <div className="absolute bottom-4 right-4 text-white/10 font-bold text-6xl">02</div>
            </div>

            {/* War Room */}
            <div className="snap-center shrink-0 w-[85vw] max-w-sm h-full relative rounded-3xl overflow-hidden border border-white/10 bg-midnight">
              <div className="p-6 border-b border-white/5 bg-primary/5">
                <div className="flex justify-between items-center mb-1">
                  <h3 className="text-2xl font-bold uppercase tracking-tight text-white">War Room</h3>
                  <span className="material-symbols-outlined text-primary">groups_3</span>
                </div>
                <p className="text-xs text-gray-400 uppercase tracking-widest">Faction Breakdown</p>
              </div>
              <div className="p-4 flex flex-col gap-3">
                {factions.length === 0 && (
                  <div className="text-sm text-slate-400">尚未偵測到清晰的派系結構。</div>
                )}
                {factions.slice(0, 3).map((f) => {
                  const color = voiceColor(f.id);
                  const pct = Math.round(f.share_pct || 0);
                  const baseClasses =
                    color === "primary"
                      ? "bg-primary/10 border border-primary/30"
                      : "bg-white/5 border border-white/5";
                  const barColor =
                    color === "primary" ? "bg-primary" : color === "yellow" ? "bg-gray-400" : "bg-green-600";
                  const icon =
                    color === "primary" ? "favorite" : color === "yellow" ? "sentiment_dissatisfied" : "trolley";
                  const circle =
                    color === "primary"
                      ? "bg-gradient-to-br from-primary to-purple-900 border border-primary shadow-[0_0_10px_rgba(244,37,192,0.4)]"
                      : color === "yellow"
                      ? "bg-gradient-to-br from-gray-700 to-black border border-gray-500"
                      : "bg-gradient-to-br from-green-900 to-black border border-green-700";
                  const pctColor =
                    color === "primary" ? "text-primary" : color === "yellow" ? "text-gray-400" : "text-green-500";
                  return (
                    <div key={f.id} className={`${baseClasses} p-3 rounded-xl flex items-center gap-4`}>
                      <div className={`size-12 rounded-full flex items-center justify-center ${circle}`}>
                        <span className={`material-symbols-outlined ${pctColor}`}>{icon}</span>
                      </div>
                      <div className="flex-1">
                        <h4 className="text-white font-bold text-sm uppercase">{f.label}</h4>
                        <div className="w-full bg-gray-800 h-1.5 rounded-full mt-2">
                          <div className={`${barColor} h-1.5 rounded-full`} style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                      <div className={`${pctColor} font-bold`}>{pct}%</div>
                    </div>
                  );
                })}
              </div>
              <div className="absolute bottom-4 right-4 text-white/10 font-bold text-6xl">03</div>
            </div>

            {/* L1 Analysis */}
            <div className="snap-center shrink-0 w-[85vw] max-w-sm h-full relative rounded-3xl overflow-hidden border border-white/10 bg-[#e8e4e1] text-background-dark">
              <div className="absolute top-0 right-0 p-4">
                <span className="bg-background-dark text-white text-[10px] font-bold px-2 py-1 uppercase tracking-widest rounded-full">
                  L1 Analysis
                </span>
              </div>
              <div className="p-8 flex flex-col h-full">
                <h3 className="text-3xl font-bold font-display leading-none mb-6">{l1.title}</h3>
                <div className="flex-1 overflow-y-auto no-scrollbar space-y-4">
                  {l1.paragraphs?.length ? (
                    l1.paragraphs.map((p, idx) => (
                      <p key={idx} className="font-serif text-lg leading-relaxed text-background-dark/90">
                        {p}
                      </p>
                    ))
                  ) : (
                    <p className="text-sm text-background-dark/70">No L1 analysis provided.</p>
                  )}
                </div>
                <div className="mt-4 pt-4 border-t border-black/10 flex justify-between items-center">
                  <span className="font-bold text-xs uppercase tracking-widest text-black/50">Read Full Report</span>
                  <span className="material-symbols-outlined text-black">arrow_forward</span>
                </div>
              </div>
              <div className="absolute bottom-4 right-4 text-black/5 font-bold text-6xl pointer-events-none">04</div>
            </div>

            <div className="w-2 shrink-0" />
          </div>
          <div className="flex justify-center gap-2 pb-2">
            <div className="w-2 h-2 rounded-full bg-primary" />
            <div className="w-2 h-2 rounded-full bg-white/20" />
            <div className="w-2 h-2 rounded-full bg-white/20" />
            <div className="w-2 h-2 rounded-full bg-white/20" />
          </div>
        </section>
      </main>
    </div>
  );
}

export default NarrativeDetailScreen;
