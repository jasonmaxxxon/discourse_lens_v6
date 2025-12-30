import hashlib
import unicodedata
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

# --- Constants (versioned for determinism) ---
FINGERPRINT_VERSION = "v1"
MATCH_RULESET_VERSION = "v1"
REGISTRY_VERSION = "v1"
TRIGGER_MAX_LEN = 2400
ARTIFACT_MAX_LEN = 2400
REACTION_MAX_LEN = 3200
TOP_M_CLUSTER_SAMPLES = 3  # used in cluster_signature_hash
TOP_K_GLOBAL_REACTIONS = 5
NAMESPACE_UUID = "6a7a3bf7-5a3f-4d66-b78e-2d7c9f5b7c7b"  # invariant, do not change


def normalize_text(text: Optional[str], max_len: Optional[int] = None) -> str:
    """
    Apply strict normalization required by CDX-044.1:
    - Unicode NFC
    - Strip BOM
    - Collapse all whitespace to single spaces
    - Trim
    - Lowercase
    - Optional truncation to max_len (in characters)
    Emoji and punctuation are preserved.
    """
    if not text:
        return ""
    normalized = unicodedata.normalize("NFC", text.replace("\ufeff", ""))
    normalized = re.sub(r"\s+", " ", normalized).strip().lower()
    if max_len is not None and max_len > 0 and len(normalized) > max_len:
        normalized = normalized[:max_len]
    return normalized


def _coerce_int(val: Any) -> int:
    try:
        return int(val)
    except Exception:
        return 0


def _cluster_size(info: Dict[str, Any]) -> float:
    if info is None:
        return 0.0
    for key in ("size", "count"):
        if info.get(key) is not None:
            try:
                return float(info[key])
            except Exception:
                return 0.0
    share = info.get("share") or info.get("pct") or info.get("percentage")
    try:
        return float(share or 0.0)
    except Exception:
        return 0.0


def cluster_signature_hash(samples: Sequence[Dict[str, Any]], top_m: int = TOP_M_CLUSTER_SAMPLES) -> str:
    """
    Deterministic sha256 hash based on topM samples by like_count (desc), then text.
    """
    ordered = sorted(
        (s for s in samples if isinstance(s, dict)),
        key=lambda s: (-_coerce_int(s.get("like_count") or s.get("likes") or 0), normalize_text(str(s.get("text", ""))))
    )
    chosen = ordered[:top_m]
    joined = "\n".join(normalize_text(str(s.get("text", ""))) for s in chosen if s.get("text"))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def order_clusters(cluster_summary: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Order clusters deterministically:
    1) cluster_size DESC
    2) cluster_signature_hash ASC
    """
    clusters = cluster_summary or {}
    items: List[Tuple[str, Dict[str, Any]]] = []
    for cid, info in clusters.items():
        if not isinstance(info, dict):
            continue
        sig = cluster_signature_hash(info.get("samples") or [])
        items.append((str(cid), {**info, "_sig": sig}))
    items.sort(key=lambda kv: (-_cluster_size(kv[1]), kv[1]["_sig"]))
    return items


def select_reaction_samples(cluster_summary: Dict[str, Any], comments: Sequence[Dict[str, Any]]) -> List[str]:
    """
    Deterministically pick reaction samples:
    - top1 per ordered cluster (by like_count desc)
    - plus global topK comments by like_count desc
    - dedup by normalized text
    """
    ordered_clusters = order_clusters(cluster_summary)
    picked: List[str] = []
    seen = set()

    for _, info in ordered_clusters:
        samples = info.get("samples") or []
        if not isinstance(samples, list) or not samples:
            continue
        top = max(samples, key=lambda s: (_coerce_int(s.get("like_count") or s.get("likes")), normalize_text(str(s.get("text", "")))))
        norm = normalize_text(str(top.get("text", "")))
        if norm and norm not in seen:
            seen.add(norm)
            picked.append(norm)

    global_sorted = sorted(
        (c for c in comments if isinstance(c, dict)),
        key=lambda c: (-_coerce_int(c.get("like_count") or c.get("likes")), normalize_text(str(c.get("text", ""))))
    )
    for c in global_sorted:
        if len(picked) >= len(ordered_clusters) + TOP_K_GLOBAL_REACTIONS:
            break
        norm = normalize_text(str(c.get("text", "")))
        if norm and norm not in seen:
            seen.add(norm)
            picked.append(norm)

    return picked


@dataclass
class EvidenceBundle:
    fingerprint: str
    case_id: str
    trigger: str
    artifact: str
    reactions: List[str]
    version: str = FINGERPRINT_VERSION


def build_evidence_bundle(
    post_text: Optional[str],
    ocr_full_text: Optional[str],
    comments: Sequence[Dict[str, Any]],
    cluster_summary: Optional[Dict[str, Any]] = None,
    images: Optional[Sequence[Dict[str, Any]]] = None,
) -> EvidenceBundle:
    trigger = normalize_text(post_text, TRIGGER_MAX_LEN)
    # Aggregate all OCR text deterministically using stable image order.
    ocr_parts: List[str] = []
    if images:
        for img in images:
            if not isinstance(img, dict):
                continue
            raw_txt = (
                img.get("full_text")
                or img.get("ocr_full_text")
                or img.get("text")
                or img.get("ocr")
            )
            if raw_txt:
                ocr_parts.append(str(raw_txt))
    artifact_source = "\n".join(ocr_parts) if ocr_parts else (ocr_full_text or "")
    artifact = normalize_text(artifact_source, ARTIFACT_MAX_LEN)
    reactions = select_reaction_samples(cluster_summary or {}, comments)
    reactions = [normalize_text(r, REACTION_MAX_LEN) for r in reactions if r]
    joined_reactions = "\n".join(reactions)

    template = f"""TRIGGER:
{trigger}

ARTIFACT:
{artifact}

REACTIONS:
{joined_reactions}
"""
    fingerprint = template.strip()
    case_id = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()
    return EvidenceBundle(
        fingerprint=fingerprint,
        case_id=case_id,
        trigger=trigger,
        artifact=artifact,
        reactions=reactions,
    )
