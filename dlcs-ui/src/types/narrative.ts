export type FactionSampleComment = {
  author_handle: string;
  text: string;
  likes: number;
};

export type BattlefieldFaction = {
  id: string;
  label: string;
  share_pct: number;
  tone_x?: number;
  tone_y?: number;
  samples?: FactionSampleComment[];
};

export type InsightPhenomenon = {
  issue_id: string;
  title: string;
  subtitle?: string;
  description: string;
  cover_image_url?: string;
};

export type InsightVibeCheck = {
  cynicism_pct: number;
  hope_pct: number;
  cynicism_caption?: string;
  hope_caption?: string;
};

export type InsightL1Analysis = {
  title: string;
  paragraphs: string[];
  highlights?: { phrase: string; label: string }[];
};

export type InsightDeck = {
  phenomenon: InsightPhenomenon;
  vibe_check: InsightVibeCheck;
  war_room_factions: BattlefieldFaction[];
  l1_analysis: InsightL1Analysis;
};

export type NarrativeMetrics = {
  total_likes: number;
  total_views: number;
  total_engagement: number;
};

export type NarrativePost = {
  id: string;
  author_handle: string;
  author_avatar_url?: string;
  text: string;
  timestamp_iso?: string;
  is_anchor?: boolean;
};

export type NarrativeAnalysis = {
  post: NarrativePost;
  metrics: NarrativeMetrics;
  battlefield: {
    factions: BattlefieldFaction[];
  };
  insight_deck: InsightDeck;
};

export type NarrativeDetailScreenProps = {
  analysisJson: NarrativeAnalysis;
};
