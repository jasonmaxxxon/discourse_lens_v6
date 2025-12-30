import hashlib
import os
import logging
import re
from collections import Counter
from typing import List, Dict, Any, Optional, Sequence, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger("QuantEngine")
PERSIST_ASSIGNMENTS = os.getenv("DL_PERSIST_ASSIGNMENTS", "0") == "1"

_embedder = None


def get_embedder():
    global _embedder
    if _embedder is None:
        logger.info("Loading SentenceTransformer: paraphrase-multilingual-MiniLM-L12-v2")
        _embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    return _embedder


def _get_like_count(comment: Dict[str, Any]) -> int:
    try:
        return int(comment.get("like_count") or comment.get("likes") or 0)
    except Exception:
        return 0


def _normalize_text(val: str) -> str:
    return " ".join((val or "").split()).strip()


def _deterministic_comment_id(post_id: Optional[str | int], comment: Dict[str, Any]) -> str:
    """
    Mirror database.store._fallback_comment_id to keep cluster assignment ids aligned with DB rows.
    """
    for key in ("id", "source_comment_id", "comment_id"):
        val = comment.get(key)
        if val:
            return str(val)
    author = str(comment.get("author_handle") or comment.get("user") or comment.get("author") or "")
    text = _normalize_text(str(comment.get("text") or ""))
    raw = f"{post_id}:{author}:{text}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _top_keywords(texts: Sequence[str], top_n: int = 6) -> List[str]:
    tokens: List[str] = []
    for t in texts:
        if not t:
            continue
        found = re.findall(r"[A-Za-z0-9#@']{3,}", t.lower())
        tokens.extend(found)
    counter = Counter(tokens)
    return [w for w, _ in counter.most_common(top_n)]


def _centroid(vectors: Sequence[np.ndarray]) -> Optional[List[float]]:
    if not vectors:
        return None
    try:
        stacked = np.vstack(vectors)
        mean_vec = np.mean(stacked, axis=0)
        return [float(x) for x in mean_vec.tolist()]
    except Exception:
        return None


def _cluster_id(post_id: str | int | None, cluster_key: int | str) -> str:
    return f"{post_id}::c{cluster_key}"


def perform_structure_mapping(comments_list: List[Dict[str, Any]], post_id: Optional[str | int] = None):
    """
    L0.5 Quantitative Structure Mapper.
    Enriches comments with quant fields, optionally persists cluster SoT, and returns clustering/similarity stats.
    """
    if not comments_list:
        logger.warning("No comments for quant analysis.")
        return None

    MIN_LEN = 5
    valid_indices = []
    valid_texts = []
    for idx, c in enumerate(comments_list):
        if "like_count" not in c:
            try:
                c["like_count"] = int(c.get("likes", 0))
            except Exception:
                c["like_count"] = 0
        text = (c.get("text") or "").strip()
        if len(text) >= MIN_LEN:
            valid_indices.append(idx)
            valid_texts.append(text)

    if not valid_texts:
        logger.warning("Valid semantic comments too few after filtering.")
        return None

    try:
        embedder = get_embedder()
        embeddings = embedder.encode(valid_texts)
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return None

    # Dimensionality reduction with deterministic fallbacks
    count = len(valid_texts)
    if count == 1:
        coords = np.array([[0.0, 0.0]])
    elif 2 <= count < 5:
        coords = np.array([[float(i), 0.0] for i in range(count)])
    else:
        try:
            pca = PCA(n_components=2)
            coords = pca.fit_transform(embeddings)
        except Exception as e:
            logger.warning(f"PCA failed, using fallback coords: {e}")
            coords = np.array([[float(i), 0.0] for i in range(count)])

    # Clustering with rules
    if count < 3:
        labels = np.zeros(count, dtype=int)
        n_clusters = 1
    else:
        if 3 <= count <= 10:
            n_clusters = 2
        else:
            n_clusters = max(2, min(4, count // 8 or 2))
        try:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
            labels = kmeans.fit_predict(embeddings)
        except Exception as e:
            logger.warning(f"KMeans failed, fallback single cluster: {e}")
            labels = np.zeros(count, dtype=int)
            n_clusters = 1

    # Echo / template-like detection
    echo_indices = set()
    high_sim_pairs_count = 0
    if count >= 2:
        try:
            sim_mat = cosine_similarity(embeddings)
            for i in range(count):
                for j in range(i + 1, count):
                    is_high_sim = sim_mat[i, j] > 0.94
                    is_long_enough = len(valid_texts[i]) >= 8
                    user_i = comments_list[valid_indices[i]].get("user")
                    user_j = comments_list[valid_indices[j]].get("user")
                    is_diff_user = user_i and user_j and user_i != user_j
                    if is_high_sim and is_long_enough and is_diff_user:
                        echo_indices.add(valid_indices[i])
                        echo_indices.add(valid_indices[j])
                        high_sim_pairs_count += 1
        except Exception as e:
            logger.warning(f"Echo similarity computation failed: {e}")

    # Backfill quant fields
    for c in comments_list:
        c.setdefault("quant_cluster_id", -1)
        c.setdefault("quant_x", 0.0)
        c.setdefault("quant_y", 0.0)
        c.setdefault("is_template_like", False)

    for i, orig_idx in enumerate(valid_indices):
        cluster_id = int(labels[i]) if isinstance(labels[i], (int, np.integer)) else 0
        comments_list[orig_idx]["quant_cluster_id"] = cluster_id
        comments_list[orig_idx]["quant_x"] = round(float(coords[i][0]), 4) if coords.shape[1] > 0 else 0.0
        comments_list[orig_idx]["quant_y"] = round(float(coords[i][1]), 4) if coords.shape[1] > 1 else 0.0
        comments_list[orig_idx]["is_template_like"] = orig_idx in echo_indices

    cluster_stats: Dict[Any, int] = {}
    for lab in labels:
        lab_int = int(lab) if isinstance(lab, (int, np.integer)) else -1
        cluster_stats[lab_int] = cluster_stats.get(lab_int, 0) + 1

    # [NEW] Math Homogeneity (dominance ratio)
    total_clustered = sum(cluster_stats.values())
    if total_clustered > 0:
        dominant_count = max(cluster_stats.values())
        math_homogeneity = round(dominant_count / total_clustered, 2)
    else:
        math_homogeneity = 1.0
    clusters_payload: List[Dict[str, Any]] = []
    assignments: List[Dict[str, Any]] = []
    cluster_labels: Dict[int, str] = {}

    try:
        label_to_members: Dict[int, List[Tuple[int, int]]] = {}
        for idx, lab in enumerate(labels):
            lab_int = int(lab) if isinstance(lab, (int, np.integer)) else 0
            label_to_members.setdefault(lab_int, []).append((idx, valid_indices[idx]))

        for lab_int, members in label_to_members.items():
            member_texts = [comments_list[orig_idx].get("text") or "" for _, orig_idx in members]
            member_embeddings = [embeddings[i] for i, _ in members if embeddings is not None]
            top_ids_sorted = sorted(
                members,
                key=lambda pair: _get_like_count(comments_list[pair[1]]),
                reverse=True,
            )
            top_comment_ids = [
                _deterministic_comment_id(post_id, comments_list[orig_idx])
                for _, orig_idx in top_ids_sorted
            ]
            keywords = _top_keywords(member_texts)
            centroid_embedding = _centroid(member_embeddings)
            label = f"Cluster {lab_int}"
            cluster_labels[lab_int] = label
            clusters_payload.append(
                {
                    "cluster_key": lab_int,
                    "label": label,
                    "summary": None,
                    "size": len(members),
                    "keywords": keywords,
                    "top_comment_ids": top_comment_ids[:5],
                    "centroid_embedding_384": centroid_embedding,
                }
            )
    except Exception as cluster_err:
        logger.warning(f"Failed to assemble cluster payloads: {cluster_err}")

    # Build assignments (idempotent-friendly payload for DB)
    for c in comments_list:
        key_raw = c.get("quant_cluster_id")
        try:
            key_int = int(key_raw)
        except Exception:
            continue
        if key_int < 0:
            continue
        assignment_cluster_id = _cluster_id(post_id, key_int) if post_id is not None else None
        comment_id = _deterministic_comment_id(post_id, c)
        label = cluster_labels.get(key_int)
        assignments.append(
            {
                "comment_id": comment_id,
                "cluster_key": key_int,
                "cluster_label": label,
                "cluster_id": assignment_cluster_id,
            }
        )
        if assignment_cluster_id:
            c["cluster_id"] = assignment_cluster_id
        if label:
            c["cluster_label"] = label

    persistence = {
        "clusters": {"ok": False, "skipped": True},
        "assignments": {"ok": False, "skipped": True},
    }

    if post_id is not None and clusters_payload:
        try:
            post_id_for_db = post_id
            try:
                post_id_for_db = int(post_id)
            except Exception:
                post_id_for_db = post_id

            from database.store import (
                apply_comment_cluster_assignments,
                upsert_comment_clusters,
            )

            cluster_res = upsert_comment_clusters(post_id_for_db, clusters_payload)
            persistence["clusters"] = cluster_res

            if PERSIST_ASSIGNMENTS:
                assign_res = apply_comment_cluster_assignments(post_id_for_db, assignments)
            else:
                assign_res = {"ok": False, "skipped": True, "reason": "DL_PERSIST_ASSIGNMENTS=0"}
            persistence["assignments"] = assign_res

            logger.info(
                f"[QuantEngine] persistence summary post={post_id} "
                f"clusters_attempted={len(clusters_payload)} clusters_ok={cluster_res.get('ok')} "
                f"assignments_attempted={len(assignments)} assignments_ok={assign_res.get('ok')} skipped_assignments={assign_res.get('skipped')}"
            )
            if not cluster_res.get("ok") or (PERSIST_ASSIGNMENTS and not assign_res.get("ok")):
                logger.warning(
                    f"[QuantEngine] Cluster persistence degraded post={post_id} "
                    f"clusters_ok={cluster_res.get('ok')} assignments_ok={assign_res.get('ok')}"
                )
        except Exception as persist_err:
            logger.warning(f"[QuantEngine] Cluster persistence failed for post {post_id}: {persist_err}")
            persistence["clusters"] = {"ok": False, "skipped": False, "error": str(persist_err)}
            persistence["assignments"] = {"ok": False, "skipped": not PERSIST_ASSIGNMENTS, "error": str(persist_err)}

    return {
        "node_data": comments_list,
        "cluster_stats": cluster_stats,
        "high_sim_pairs": high_sim_pairs_count,
        "math_homogeneity": math_homogeneity,
        "clusters": clusters_payload,
        "assignments": assignments,
        "clusters_ref": {"k": len(clusters_payload), "n_clusters": n_clusters},
        "persistence": persistence,
    }
