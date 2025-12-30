from analysis.phenomenon_fingerprint import (
    build_evidence_bundle,
    cluster_signature_hash,
    normalize_text,
    order_clusters,
    select_reaction_samples,
    FINGERPRINT_VERSION,
    MATCH_RULESET_VERSION,
    NAMESPACE_UUID,
    TOP_K_GLOBAL_REACTIONS,
)


def test_normalize_text_rules():
    raw = "  Héllo \nWorld\t😊  "
    assert normalize_text(raw) == "héllo world 😊"
    assert normalize_text(raw, max_len=5) == "héllo"


def test_cluster_signature_and_ordering_is_deterministic():
    clusters = {
        "1": {"count": 3, "samples": [{"text": "aaa", "like_count": 1}, {"text": "bbb", "like_count": 5}]},
        "2": {"count": 3, "samples": [{"text": "ccc", "like_count": 2}]},
        "3": {"count": 1, "samples": [{"text": "ddd", "like_count": 10}]},
    }
    ordered_first = order_clusters(clusters)
    ordered_second = order_clusters(clusters)
    assert ordered_first == ordered_second
    # Clusters 1 and 2 share same size, so signature hash decides order deterministically
    assert cluster_signature_hash(clusters["1"]["samples"]) != cluster_signature_hash(clusters["2"]["samples"])


def test_build_evidence_bundle_case_id_stable():
    comments = [
        {"text": "first", "like_count": 10},
        {"text": "second", "like_count": 5},
    ]
    images = [{"full_text": "OCR"}, {"text": "other"}]
    bundle1 = build_evidence_bundle("POST", None, comments, {"0": {"count": 2, "samples": comments}}, images=images)
    bundle2 = build_evidence_bundle("POST", None, comments, {"0": {"count": 2, "samples": comments}}, images=list(images))
    assert bundle1.case_id == bundle2.case_id
    assert bundle1.fingerprint == bundle2.fingerprint
    assert bundle1.version == FINGERPRINT_VERSION


def test_reaction_sampling_includes_cluster_heads_and_global_topk():
    clusters = {
        "0": {"count": 3, "samples": [{"text": "cluster head", "like_count": 2}]},
    }
    comments = [
        {"text": "cluster head", "like_count": 2},  # duplicate should be deduped
        {"text": "global top", "like_count": 99},
    ]
    reactions = select_reaction_samples(clusters, comments)
    assert "cluster head" in reactions
    assert "global top" in reactions


def test_cluster_permutation_invariance():
    base_clusters = {
        "a": {"count": 2, "samples": [{"text": "alpha", "like_count": 3}]},
        "b": {"count": 1, "samples": [{"text": "beta", "like_count": 2}]},
    }
    permuted = {"b": base_clusters["b"], "a": base_clusters["a"]}
    bundle1 = build_evidence_bundle("trigger", None, [], base_clusters)
    bundle2 = build_evidence_bundle("trigger", None, [], permuted)
    assert bundle1.case_id == bundle2.case_id


def test_reaction_cap_respected():
    clusters = {
        "0": {"count": 1, "samples": [{"text": "c0", "like_count": 1}]},
        "1": {"count": 1, "samples": [{"text": "c1", "like_count": 1}]},
    }
    comments = [{"text": f"g{i}", "like_count": 100 - i} for i in range(20)]
    reactions = select_reaction_samples(clusters, comments)
    assert len(reactions) <= len(clusters) + TOP_K_GLOBAL_REACTIONS
