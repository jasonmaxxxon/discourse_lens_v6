from typing import Callable, Optional

from database.store import save_thread
from scraper.fetcher import fetch_page_html
from scraper.parser import extract_data_from_html


def _log(msg: str, logger: Optional[Callable[[str], None]] = None):
    print(msg)
    if logger:
        logger(msg)


def run_pipeline(
    url: str,
    ingest_source: str | None = None,
    return_data: bool = False,
    logger: Optional[Callable[[str], None]] = None,
):
    _log("\n🚀 Pipeline started.", logger)

    # Step 1: fetch HTML（現在會拿到 initial_html + scrolled_html）
    html_bundle = fetch_page_html(url)
    if not html_bundle or (
        not html_bundle.get("initial_html") and not html_bundle.get("scrolled_html")
    ):
        _log("❌ 無法抓取 HTML", logger)
        return None

    _log("🧩 HTML OK，開始解析...", logger)

    # Step 2: parse（會幫你合併「初始畫面 Top comments」+「深度捲動留言」）
    data = extract_data_from_html(html_bundle, url)

    # Step 3: result preview
    _log("\n===== 結果預覽 =====", logger)
    _log(f"作者: {data['author']}", logger)
    _log(f"主文（乾淨）: {data['post_text'][:200]} ...", logger)
    _log(f"Like: {data['metrics']['likes']}", logger)
    _log(f"Views: {data['metrics']['views']}", logger)
    _log(f"Reply 總數 (UI): {data['metrics']['reply_count']}", logger)
    _log(f"Repost 總數 (UI): {data['metrics']['repost_count']}", logger)
    _log(f"Share 總數 (UI): {data['metrics']['share_count']}", logger)
    _log(f"實際抓到留言樣本: {len(data['comments'])}", logger)
    _log("====================", logger)

    # Step 4: save to DB
    try:
        save_thread(data, ingest_source=ingest_source)
    except TypeError:
        save_thread(data)

    # 印留言列表
    _log("\n===== 留言 Sample =====", logger)
    for idx, c in enumerate(data["comments"], start=1):
        _log(f"\n--- Comment #{idx} ---", logger)
        _log(f"User: {c['user']}", logger)
        _log(f"Likes: {c['likes']}", logger)
        _log(f"Text: {c['text']}", logger)
    _log("======================\n", logger)

    if return_data:
        return data

    return None
