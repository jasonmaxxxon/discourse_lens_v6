import { AnalysisJson } from "../types/analysis";

export interface QuantLabel {
  value: number | null;
  label: string;
}

export interface UseQuantDiagnosticsResult {
  sectorId: string | null;
  primaryEmotion: string | null;
  strategyCode: string | null;
  civil: QuantLabel;
  homogeneity: QuantLabel;
  authorInfluence: string | null;
  isNewPhenomenon: boolean;
  highImpact: boolean;
}

export function useQuantDiagnostics(analysis?: AnalysisJson | null): UseQuantDiagnosticsResult {
  const metrics = analysis?.metrics ?? {};
  const tags = analysis?.raw_json?.Quantifiable_Tags ?? {};

  const sectorId = metrics.sector_id ?? tags.Sector_ID ?? null;
  const primaryEmotion = metrics.primary_emotion ?? tags.Primary_Emotion ?? null;
  const strategyCode = metrics.strategy_code ?? tags.Strategy_Code ?? null;
  const authorInfluence = metrics.author_influence ?? tags.Author_Influence ?? null;
  const isNewPhenomenon = Boolean(
    metrics.is_new_phenomenon ?? analysis?.raw_json?.Discovery_Channel?.Is_New_Phenomenon
  );

  const civilScore =
    metrics.civil_score ?? (typeof tags.Civil_Score === "number" ? tags.Civil_Score : null);

  let civilLabel = "N/A";
  if (civilScore != null) {
    if (civilScore <= 3) civilLabel = "Toxic｜高度敵意";
    else if (civilScore >= 8) civilLabel = "Deliberative｜高質討論";
    else civilLabel = "Heated｜激烈但仍具溝通";
  }

  const homoScore =
    metrics.homogeneity_score ?? (typeof tags.Homogeneity_Score === "number" ? tags.Homogeneity_Score : null);

  let homoLabel = "N/A";
  if (homoScore != null) {
    if (homoScore >= 0.8) homoLabel = "Echo Chamber｜高共識迴聲室";
    else if (homoScore >= 0.4) homoLabel = "Polarized｜兩極分化戰場";
    else homoLabel = "Fragmented｜多元碎片討論";
  }

  return {
    sectorId,
    primaryEmotion,
    strategyCode,
    civil: { value: civilScore ?? null, label: civilLabel },
    homogeneity: { value: homoScore ?? null, label: homoLabel },
    authorInfluence,
    isNewPhenomenon,
    highImpact: Boolean(metrics.high_impact ?? analysis?.raw_json?.Analysis_Meta?.High_Impact),
  };
}
