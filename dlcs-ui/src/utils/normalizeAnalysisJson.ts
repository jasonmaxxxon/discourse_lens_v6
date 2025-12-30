import {
  BattlefieldFaction,
  FactionSampleComment,
  NarrativeAnalysis,
  NarrativeMetrics,
  NarrativePost,
} from "../types/narrative";

const toPct = (val: any): number => {
  const num = Number(val);
  if (!Number.isFinite(num)) return 0;
  return num <= 1 ? Math.max(0, Math.min(1, num)) * 100 : num;
};

const mapSamples = (samples: any[] | undefined): FactionSampleComment[] => {
  if (!Array.isArray(samples)) return [];
  return samples.map((s) => ({
    author_handle: s?.author_handle || s?.user || "anon",
    text: s?.text || "",
    likes: Number(s?.likes ?? s?.like_count ?? 0) || 0,
  }));
};

export const normalizeAnalysisJson = (raw: any): NarrativeAnalysis => {
  if (!raw || typeof raw !== "object") {
    throw new Error("analysis_json payload is empty or invalid");
  }

  if (typeof window !== "undefined" && import.meta.env.DEV) {
    console.debug("[normalizeAnalysisJson] Raw payload keys", {
      topLevelKeys: Object.keys(raw || {}),
      hasBattlefield: Boolean(raw?.battlefield),
      hasSummary: Boolean(raw?.summary),
      postId: raw?.post_id ?? raw?.post?.id,
    });
  }

  const post: NarrativePost = {
    id: raw?.post?.id?.toString() || raw?.post_id?.toString() || raw?.meta?.id?.toString() || "unknown",
    author_handle: raw?.post?.author_handle || raw?.meta?.author || raw?.post?.author || "unknown",
    author_avatar_url: raw?.post?.author_avatar_url || raw?.meta?.author_avatar_url,
    text:
      raw?.post?.text ||
      raw?.meta?.post_text ||
      raw?.post_text ||
      raw?.summary?.one_line ||
      raw?.summary?.narrative_type ||
      "",
    timestamp_iso: raw?.post?.timestamp_iso || raw?.meta?.captured_at || raw?.meta?.created_at,
    is_anchor: Boolean(raw?.post?.is_anchor ?? true),
  };

  const metrics: NarrativeMetrics = {
    total_likes: Number(raw?.metrics?.total_likes ?? raw?.metrics?.likes ?? raw?.metrics?.Likes ?? 0) || 0,
    total_views: Number(raw?.metrics?.total_views ?? raw?.metrics?.views ?? raw?.metrics?.Views ?? 0) || 0,
    total_engagement:
      Number(raw?.metrics?.total_engagement ?? raw?.metrics?.engagement ?? raw?.metrics?.Engagement ?? 0) || 0,
  };

  if (!metrics.total_engagement) {
    metrics.total_engagement = metrics.total_likes + (Number(raw?.metrics?.replies ?? raw?.metrics?.Replies ?? 0) || 0);
  }

  const factions: BattlefieldFaction[] =
    raw?.battlefield?.factions?.map((f: any, idx: number) => ({
      id: f?.id || f?.label || f?.name || `faction-${idx}`,
      label: f?.label || f?.name || `Faction ${idx + 1}`,
      share_pct: toPct(f?.share ?? f?.share_pct ?? f?.pct ?? f?.percentage),
      tone_x: Number(f?.tone_x ?? f?.tone?.x ?? f?.tone?.x_coord),
      tone_y: Number(f?.tone_y ?? f?.tone?.y ?? f?.tone?.y_coord),
      samples: mapSamples(f?.samples),
    })) || [];

  const toneBlock = raw?.tone || raw?.Tone || {};
  const deckSource = raw?.insight_deck || {};
  const insight_deck = {
    phenomenon: {
      issue_id: deckSource?.phenomenon?.issue_id || raw?.metrics?.sector_id || raw?.post_id || "000",
      title:
        deckSource?.phenomenon?.title ||
        raw?.summary?.narrative_type ||
        raw?.summary?.one_line ||
        "Narrative Phenomenon",
      subtitle: deckSource?.phenomenon?.subtitle || "Trending Now",
      description:
        deckSource?.phenomenon?.description ||
        raw?.summary?.one_line ||
        raw?.summary?.narrative_type ||
        "No description provided.",
      cover_image_url: deckSource?.phenomenon?.cover_image_url,
    },
    vibe_check: {
      cynicism_pct:
        toPct(deckSource?.vibe_check?.cynicism_pct) ||
        toPct(toneBlock?.cynicism ?? toneBlock?.Cynicism),
      hope_pct:
        toPct(deckSource?.vibe_check?.hope_pct) || toPct(toneBlock?.hope ?? toneBlock?.Hope),
      cynicism_caption: deckSource?.vibe_check?.cynicism_caption || toneBlock?.cynicism_caption,
      hope_caption: deckSource?.vibe_check?.hope_caption || toneBlock?.hope_caption,
    },
    war_room_factions: deckSource?.war_room_factions && Array.isArray(deckSource.war_room_factions)
      ? deckSource.war_room_factions
      : factions,
    l1_analysis: {
      title: deckSource?.l1_analysis?.title || raw?.layers?.l1?.title || "Hidden Meaning",
      paragraphs:
        deckSource?.l1_analysis?.paragraphs && Array.isArray(deckSource.l1_analysis.paragraphs)
          ? deckSource.l1_analysis.paragraphs
          : raw?.layers?.l1?.summary
          ? [raw.layers.l1.summary]
          : [raw?.strategies?.primary, raw?.strategies?.tactics?.[0]]
              .filter((p) => typeof p === "string" && p.trim().length > 0)
              .map((p) => p as string),
      highlights: deckSource?.l1_analysis?.highlights || [],
    },
  };

  return {
    post,
    metrics,
    battlefield: { factions },
    insight_deck,
  };
};
