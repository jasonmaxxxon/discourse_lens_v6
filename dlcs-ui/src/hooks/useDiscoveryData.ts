import { AnalysisJson, DiscoveryInfo } from "../types/analysis";

export interface UseDiscoveryResult {
  discovery: DiscoveryInfo | null;
}

export function useDiscoveryData(analysis?: AnalysisJson | null): UseDiscoveryResult {
  if (!analysis) return { discovery: null };

  const normalized: DiscoveryInfo = { ...(analysis.discovery || {}) };

  const raw = analysis.raw_json?.Discovery_Channel;
  if (!normalized.sub_variant_name && raw?.Sub_Variant_Name) {
    normalized.sub_variant_name = raw.Sub_Variant_Name;
  }
  if (normalized.is_new_phenomenon == null && typeof raw?.Is_New_Phenomenon === "boolean") {
    normalized.is_new_phenomenon = raw.Is_New_Phenomenon;
  }
  if (!normalized.phenomenon_description && raw?.Phenomenon_Description) {
    normalized.phenomenon_description = raw.Phenomenon_Description;
  }

  if (!normalized.sub_variant_name && !normalized.phenomenon_description && normalized.is_new_phenomenon == null) {
    return { discovery: null };
  }

  return { discovery: normalized };
}
