import logging
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class VisionGateDecision:
    run_v1: bool
    score: float
    reasons: List[str]
    metrics_reliable: bool
    sim_post_comments: Optional[float] = None

    def to_db_fields(self, vision_mode: str, stage_ran: str = "none") -> Dict[str, Any]:
        return {
            "vision_mode": vision_mode,
            "vision_need_score": float(self.score),
            "vision_reasons": self.reasons,
            "vision_stage_ran": stage_ran,
            "vision_sim_post_comments": self.sim_post_comments,
            "vision_metrics_reliable": bool(self.metrics_reliable),
        }


class VisionGate:
    """
    Regex-free gating:
    - Structural: silent post with images
    - Impact: only if metrics reliable
    - Comment poverty: avg comment length too short
    - (Optional) semantic divergence: if embeddings provided
    """

    def evaluate(
        self,
        *,
        post_id: str,
        images_count: int,
        post_text: str,
        comments: List[Dict[str, Any]],
        vision_mode: str = "auto",  # off|auto|force
        metrics: Optional[Dict[str, Any]] = None,
        post_embedding: Optional[List[float]] = None,
        top_comment_embeddings: Optional[List[List[float]]] = None,
        threshold: float = 2.0,
    ) -> VisionGateDecision:
        metrics = metrics or {}
        post_text = post_text or ""
        comments = comments or []
        metrics_reliable = bool(metrics.get("metrics_reliable", False))

        # HARD GATES
        if vision_mode == "off" or images_count <= 0:
            logger.info(f"[VisionGate] post={post_id} decision=SKIP mode={vision_mode} img={images_count}")
            return VisionGateDecision(run_v1=False, score=0.0, reasons=["NoImagesOrOff"], metrics_reliable=metrics_reliable)

        if vision_mode == "force":
            logger.info(f"[VisionGate] post={post_id} decision=FORCE")
            return VisionGateDecision(run_v1=True, score=999.0, reasons=["ForceMode"], metrics_reliable=metrics_reliable)

        score = 0.0
        reasons: List[str] = []

        # W1: Silent Post (images + short text)
        if images_count > 0 and len(post_text.strip()) < 80:
            score += 2.0
            reasons.append("SilentPost(<80)")

        # W2: Comment Poverty (avg length too short OR too many empty)
        texts = [str(c.get("text") or "").strip() for c in comments]
        nonempty = [t for t in texts if t]
        if nonempty:
            avg_len = sum(len(t) for t in nonempty) / max(1, len(nonempty))
            nonempty_ratio = len(nonempty) / max(1.0, float(len(texts)))
            if avg_len < 12:
                score += 1.0
                reasons.append(f"ShortComments(avg<{12})")
            if nonempty_ratio < 0.70:
                score += 0.5
                reasons.append("ManyEmptyComments(<70% nonempty)")
        else:
            score += 1.0
            reasons.append("NoReadableComments")

        # W3: Impact (only when reliable)
        if metrics_reliable:
            view_count = int(metrics.get("view_count") or 0)
            like_count = int(metrics.get("like_count") or 0)
            reply_count = int(metrics.get("reply_count") or 0)
            if view_count > 50000 or like_count > 300 or reply_count > 120:
                score += 1.5
                reasons.append("HighImpact")

        # W4: Semantic divergence (optional)
        sim = None
        if post_embedding and top_comment_embeddings:
            try:
                mean_vec = self._mean_vec(top_comment_embeddings)
                sim = self._cosine(post_embedding, mean_vec)
                if sim < 0.30:
                    score += 2.0
                    reasons.append(f"SemanticDivergence(sim<{0.30:.2f})")
            except Exception as e:
                logger.warning(f"[VisionGate] post={post_id} embedding divergence failed: {e}")

        run_v1 = score >= threshold
        logger.info(f"[VisionGate] post={post_id} score={score:.2f} run_v1={run_v1} reasons={reasons} sim={sim}")
        return VisionGateDecision(run_v1=run_v1, score=score, reasons=reasons, metrics_reliable=metrics_reliable, sim_post_comments=sim)

    def _mean_vec(self, vecs: List[List[float]]) -> List[float]:
        dim = len(vecs[0])
        out = [0.0] * dim
        for v in vecs:
            for i, x in enumerate(v):
                out[i] += float(x)
        n = float(len(vecs))
        return [x / n for x in out]

    def _cosine(self, a: List[float], b: List[float]) -> float:
        dot = 0.0
        na = 0.0
        nb = 0.0
        for x, y in zip(a, b):
            x = float(x)
            y = float(y)
            dot += x * y
            na += x * x
            nb += y * y
        if na <= 0.0 or nb <= 0.0:
            return 0.0
        return dot / (math.sqrt(na) * math.sqrt(nb))
