from analysis.build_analysis_json import build_analysis_json


def test_metrics_prioritize_crawler():
    post = {"id": "p1", "like_count": 1700, "view_count": 51500, "reply_count": 12}
    llm = {"Post_Stats": {"Likes": 0, "Views": 10, "Replies": 1}}
    result = build_analysis_json(post, llm)
    assert result.post.metrics.likes == 1700
    assert result.post.metrics.views == 51500
    assert result.post.metrics.replies == 12


def test_segment_share_normalized():
    post = {"id": "p1", "like_count": 1}
    llm = {}
    cluster = {"clusters": [{"label": "A", "pct": 55, "samples": []}]}
    result = build_analysis_json(post, llm, cluster)
    assert result.segments[0].share == 0.55


def test_missing_optional_fields():
    post = {"id": "p1", "like_count": 0}
    llm = {}
    result = build_analysis_json(post, llm)
    assert result.segments == []
    assert result.emotional_pulse.cynicism is None
