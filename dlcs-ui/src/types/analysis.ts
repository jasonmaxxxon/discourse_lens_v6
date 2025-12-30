export interface FeedItem {
  id: string;
  snippet: string;
  createdAt: string;
  aiTags?: string[];
  author?: string | null;
  likeCount?: number | null;
  viewCount?: number | null;
  replyCount?: number | null;
  hasAnalysis?: boolean;
  analysisIsValid?: boolean;
  analysisVersion?: string | null;
  analysisBuildId?: string | null;
  archiveCapturedAt?: string | null;
  archiveBuildId?: string | null;
  hasArchive?: boolean;
}

export interface AnalysisResponse {
  analysis_json: any;
  analysis_is_valid?: boolean;
  analysis_version?: string;
  analysis_build_id?: string;
  analysis_invalid_reason?: string;
  analysis_missing_keys?: string[] | null;
}

export interface ToneFingerprint {
  cynicism: number;
  anger: number;
  hope: number;
  despair: number;
}

export interface StrategyBlock {
  primary: string;
  secondary: string[];
  tactics: string[];
}

export interface FactionSample {
  user?: string | null;
  text?: string | null;
  like_count?: number | null;
}

export interface BattlefieldFaction {
  name: string;
  summary?: string | null;
  share?: number | null;
  samples?: FactionSample[] | null;
}

export interface BattlefieldBlock {
  factions?: BattlefieldFaction[] | null;
}

export interface AnalysisSummary {
  one_line: string;
  narrative_type: string;
  key_frames: string[];
}

export interface AnalysisMeta {
  author?: string;
  url?: string;
  captured_at?: string;
}

export interface MetricsBlock {
  sector_id?: string;
  primary_emotion?: string;
  strategy_code?: string;
  civil_score?: number | null;
  homogeneity_score?: number | null;
  author_influence?: string;
  high_impact?: boolean | null;
  likes?: number;
  replies?: number;
  views?: number;
  is_new_phenomenon?: boolean | null;
}

export interface DiscoveryInfo {
  sub_variant_name?: string | null;
  is_new_phenomenon?: boolean | null;
  phenomenon_description?: string | null;
}

export interface RawClusterInsight {
  name?: string;
  summary?: string;
  pct?: number;
  share?: number;
  [key: string]: any;
}

export type ClusterInsightMap = Record<string, RawClusterInsight>;

export interface RawJsonPayload {
  Discovery_Channel?: {
    Sub_Variant_Name?: string;
    Is_New_Phenomenon?: boolean;
    Phenomenon_Description?: string;
    [key: string]: any;
  };
  Cluster_Insights?: Record<string, RawClusterInsight>;
  Quantifiable_Tags?: {
    Sector_ID?: string;
    Primary_Emotion?: string;
    Strategy_Code?: string;
    Civil_Score?: number;
    Homogeneity_Score?: number;
    Author_Influence?: string;
    [key: string]: any;
  };
  [key: string]: any;
}

export interface AnalysisLayer {
  title: string;
  summary: string;
  body?: string | null;
  slug?: string | null;
}

export interface AnalysisLayers {
  l1?: AnalysisLayer | null;
  l2?: AnalysisLayer | null;
  l3?: AnalysisLayer | null;
}

export interface AnalysisJson {
  post_id: number | string;
  meta: AnalysisMeta;
  summary: AnalysisSummary;
  tone: ToneFingerprint;
  strategies: StrategyBlock;
  battlefield: BattlefieldBlock;
  metrics?: MetricsBlock;
  layers?: AnalysisLayers;
  discovery?: DiscoveryInfo;
  raw_markdown?: string;
  raw_json?: RawJsonPayload;
}

export type RawAnalysisResponse = {
  post_id: string;
  full_report_markdown: string;
};

// --- Legacy analysis types (for legacy cards and mock data) ---

export type LegacyClusterInsight = {
  name: string;
  summary: string;
  pct?: number;
};

export type LegacyDiscoveryChannel = {
  Sub_Variant_Name: string;
  Is_New_Phenomenon: boolean;
  Phenomenon_Description: string;
};

export type LegacyClusterInsights = Record<string, LegacyClusterInsight>;

export type SectionOne = {
  executiveSummary: string;
  phenomenonSpotlight: string;
  l1DeepDive: string;
  l2Strategy: string;
  l3Battlefield: string;
  factionAnalysis: string;
  strategicImplication: string;
  academicReferences: { author: string; year: string; note: string }[];
};

export type StrategySnippet = {
  name: string;
  intensity: number;
  description: string;
  example: string;
  citation: string;
};

export type LegacyToneFingerprint = {
  assertiveness: number;
  cynicism: number;
  playfulness: number;
  contempt: number;
  description: string;
  example: string;
};

export type FactionSummary = {
  label: string;
  dominant?: boolean;
  summary: string;
  bullets: string[];
};

export type CommentSample = {
  author: string;
  text: string;
  likes: number;
  faction?: string;
  tags?: string[];
};

export type NarrativeShiftNode = {
  stage: string;
  label: string;
};

type LegacyAnalysisMeta = {
  Post_ID: string;
  Timestamp: string;
  High_Impact: boolean;
};

type LegacyQuantifiableTags = {
  Sector_ID: string;
  Primary_Emotion: string;
  Strategy_Code: string;
  Civil_Score: number;
  Homogeneity_Score: number;
  Author_Influence: string;
};

type LegacyPostStats = {
  Likes: number;
  Replies: number;
  Views: number;
};

export type PostAnalysis = {
  meta: LegacyAnalysisMeta;
  quant: LegacyQuantifiableTags;
  stats: LegacyPostStats;
  insights: LegacyClusterInsights;
  discovery: LegacyDiscoveryChannel;
  section1: SectionOne;
  strategies: StrategySnippet[];
  tone: LegacyToneFingerprint;
  factions: FactionSummary[];
  commentSamples: CommentSample[];
  narrativeShift: NarrativeShiftNode[];
};
