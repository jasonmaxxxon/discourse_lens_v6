import { fetchJson } from "./client";
import { AnalysisJson, AnalysisResponse, FeedItem, RawAnalysisResponse } from "../types/analysis";

const fallbackSnippet = (text: unknown): string => {
  if (typeof text !== "string") return "";
  const normalized = text.replace(/\s+/g, " ").trim();
  return normalized.length > 180 ? `${normalized.slice(0, 180)}…` : normalized;
};

export async function fetchPosts(): Promise<FeedItem[]> {
  const rows = await fetchJson<any[]>(`/api/posts`);
  return (rows || []).map((row) => {
    const createdAt =
      row.created_at ||
      row.captured_at ||
      row.createdAt ||
      row.capturedAt ||
      "";
    const snippet =
      typeof row.snippet === "string"
        ? row.snippet
        : fallbackSnippet(row.post_text);
    const rawTags = row.ai_tags ?? row.aiTags;
    let aiTags: string[] | undefined;
    if (Array.isArray(rawTags)) {
      aiTags = rawTags.map((t) => String(t));
    } else if (rawTags && typeof rawTags === "object") {
      aiTags = Object.values(rawTags)
        .filter((v) => v !== null && v !== undefined)
        .map((v) => String(v));
    } else if (rawTags != null) {
      aiTags = [String(rawTags)];
    }
    return {
      id: String(row.id),
      snippet,
      createdAt,
      aiTags,
      author: row.author || row.meta?.author,
      likeCount: row.like_count ?? row.likes,
      viewCount: row.view_count ?? row.views,
      replyCount: row.reply_count ?? row.replies,
      hasAnalysis: Boolean(row.has_analysis ?? row.analysis_json),
      analysisIsValid: row.analysis_is_valid,
      analysisVersion: row.analysis_version,
      analysisBuildId: row.analysis_build_id,
      archiveCapturedAt: row.archive_captured_at,
      archiveBuildId: row.archive_build_id,
      hasArchive: row.has_archive ?? Boolean(row.archive_captured_at),
    };
  });
}

export async function fetchAnalysisJson(postId: string, init?: RequestInit): Promise<AnalysisResponse> {
  return fetchJson<AnalysisResponse>(`/api/analysis-json/${postId}`, init);
}

/** Legacy markdown endpoint, kept for the full report card. */
export async function fetchAnalysisMarkdown(postId: string): Promise<string> {
  const raw = await fetchJson<RawAnalysisResponse>(`/api/analysis/${postId}`);
  return raw.full_report_markdown;
}
