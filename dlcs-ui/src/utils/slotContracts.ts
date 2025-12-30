import { NarrativeAnalysis } from "../types/narrative";

type SlotStatus = { ok: boolean; missing: string[] };

export function getSlotStatus(data: NarrativeAnalysis, missingKeys?: string[]): Record<string, SlotStatus> {
  const missingList = missingKeys || [];
  const status: Record<string, SlotStatus> = {};

  // Phenomenon
  const phenMissing: string[] = [];
  if (!data.insight_deck?.phenomenon?.title) phenMissing.push("phenomenon.title");
  const phenOk = phenMissing.length === 0 && !missingList.includes("phenomenon.name");
  status.phenomenon = { ok: phenOk, missing: [...phenMissing, ...missingList.filter((m) => m.startsWith("phenomenon"))] };

  // Vibe
  const vibeMissing: string[] = [];
  if (data.insight_deck?.vibe_check?.cynicism_pct == null) vibeMissing.push("vibe.cynicism_pct");
  if (data.insight_deck?.vibe_check?.hope_pct == null) vibeMissing.push("vibe.hope_pct");
  status.vibe = { ok: vibeMissing.length === 0, missing: vibeMissing };

  // Segments
  const segmentsMissing: string[] = [];
  if (!data.battlefield?.factions?.length) segmentsMissing.push("segments.none");
  status.segments = { ok: segmentsMissing.length === 0, missing: segmentsMissing };

  // Narrative Stack
  const stackMissing: string[] = [];
  if (!data.insight_deck?.l1_analysis?.paragraphs?.length) stackMissing.push("narrative.l1");
  status.narrative = { ok: stackMissing.length === 0, missing: stackMissing };

  return status;
}
