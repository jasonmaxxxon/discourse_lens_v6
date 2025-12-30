export type SplitReport = {
  introAndPhenomenon: string;
  toneAndStrategy: string;
  battlefieldAndImplication: string;
  jsonBlock: string;
};

function safeSlice(text: string, start: number, end?: number): string {
  const safeStart = Math.max(0, start);
  if (end !== undefined && end < safeStart) return "";
  return end !== undefined ? text.slice(safeStart, end) : text.slice(safeStart);
}

export function splitReport(markdown: string): SplitReport {
  if (!markdown) {
    return {
      introAndPhenomenon: "",
      toneAndStrategy: "",
      battlefieldAndImplication: "",
      jsonBlock: "",
    };
  }

  const lower = markdown.toLowerCase();
  const idxL1 = lower.indexOf("l1 & l2");
  const idxL3 = lower.indexOf("l3 ");
  const idxSection2 = lower.indexOf("section 2");

  // Find last fenced json block
  const fenceIdx = lower.lastIndexOf("```json");
  const fenceEndIdx = lower.lastIndexOf("```", markdown.length - 1);

  const introEnd = idxL1 >= 0 ? idxL1 : markdown.length;
  const toneEnd = idxL3 >= 0 ? idxL3 : idxSection2 >= 0 ? idxSection2 : markdown.length;
  const battlefieldEnd = idxSection2 >= 0 ? idxSection2 : markdown.length;

  const introAndPhenomenon = safeSlice(markdown, 0, introEnd).trim();
  const toneAndStrategy = safeSlice(markdown, idxL1 >= 0 ? idxL1 : introEnd, toneEnd).trim();
  const battlefieldAndImplication = safeSlice(markdown, idxL3 >= 0 ? idxL3 : toneEnd, battlefieldEnd).trim();

  let jsonBlock = "";
  if (fenceIdx >= 0) {
    const endIdx = fenceEndIdx > fenceIdx ? fenceEndIdx + 3 : markdown.length;
    jsonBlock = safeSlice(markdown, fenceIdx, endIdx).trim();
  }

  return {
    introAndPhenomenon,
    toneAndStrategy,
    battlefieldAndImplication,
    jsonBlock,
  };
}
