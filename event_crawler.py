from __future__ import annotations

import datetime
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from playwright.sync_api import sync_playwright

from pipelines.core import run_pipeline
from scraper.fetcher import normalize_url
from scraper.parser import parse_number

AUTH_FILE = "auth_threads.json"


@dataclass
class DiscoveredPost:
    url: str
    snippet: str
    likes: Optional[int] = None
    age_label: Optional[str] = None


def rank_posts(posts: List[DiscoveredPost]) -> List[DiscoveredPost]:
    return sorted(posts, key=lambda p: (p.likes or 0), reverse=True)


def _extract_likes_from_text(text: str) -> Optional[int]:
    if not text:
        return None
    m = re.search(r"([\d\.,]+\s*[KMkm]?)\s*(?:likes?|讚)", text)
    if not m:
        return None
    return parse_number(m.group(1))


def _extract_age_label(text: str) -> Optional[str]:
    if not text:
        return None
    m = re.search(r"\b\d+\s*[smhdw]\b", text)
    return m.group(0) if m else None


def _clean_snippet(text: str) -> str:
    if not text:
        return ""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    snippet = " ".join(lines)
    return snippet[:500]


def _harvest_posts(page, seen: Dict[str, DiscoveredPost]):
    anchors = page.query_selector_all('a[href*="/post/"]')
    for anchor in anchors:
        href = anchor.get_attribute("href") or ""
        if "/post/" not in href:
            continue

        if href.startswith("http"):
            url = normalize_url(href.split("?")[0])
        else:
            url = normalize_url(f"https://www.threads.net{href.split('?')[0]}")

        if url in seen:
            continue

        snippet_text = ""
        likes = None
        age_label = None

        try:
            container = anchor.query_selector("xpath=../..") or anchor
            container_text = container.text_content() or ""
            snippet_text = _clean_snippet(container_text)
            likes = _extract_likes_from_text(container_text)
            age_label = _extract_age_label(container_text)
        except Exception:
            snippet_text = ""

        seen[url] = DiscoveredPost(url=url, snippet=snippet_text, likes=likes, age_label=age_label)


def discover_thread_urls(keyword: str, max_posts: int) -> List[DiscoveredPost]:
    if not os.path.exists(AUTH_FILE):
        raise FileNotFoundError("⚠️ 找不到 auth_threads.json，請先執行 scraper/login.py。")

    headless_flag = os.environ.get("DLENS_HEADLESS", "1") != "0"
    collected: Dict[str, DiscoveredPost] = {}
    target = max_posts

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless_flag)
        context = browser.new_context(storage_state=AUTH_FILE)
        page = context.new_page()

        print(f"🔍 使用關鍵字搜尋：{keyword}")
        page.goto("https://www.threads.net/search", timeout=60000, wait_until="load")
        page.wait_for_load_state("networkidle")
        time.sleep(1.5)

        search_box = None
        try:
            search_box = page.get_by_placeholder("Search").first
            search_box.fill(keyword)
        except Exception:
            try:
                search_box = page.locator('input[type="search"]').first
                search_box.fill(keyword)
            except Exception:
                pass

        if search_box:
            search_box.press("Enter")
        else:
            # fallback: type and press enter on page
            page.keyboard.type(keyword)
            page.keyboard.press("Enter")

        page.wait_for_timeout(1500)
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        print("📄 搜尋結果頁已載入，開始捲動...")

        stable_rounds = 0
        last_height = 0
        loop = 0
        while len(collected) < target and stable_rounds < 4:
            loop += 1
            _harvest_posts(page, collected)
            print(f"🔗 目前已收集 {len(collected)} 條貼文 URL...")

            page.mouse.wheel(0, 2800)
            page.wait_for_timeout(1200)
            height = page.evaluate("document.body.scrollHeight")
            if height == last_height:
                stable_rounds += 1
            else:
                stable_rounds = 0
            last_height = height

        print(f"✅ URL 發現完成，最終取得 {len(collected)} 條（限制：{max_posts}）")
        browser.close()

    posts_list = list(collected.values())
    if len(posts_list) > max_posts:
        posts_list = posts_list[:max_posts]
    return posts_list


def ingest_posts(posts: List[DiscoveredPost]):
    total = len(posts)
    for idx, p in enumerate(posts, start=1):
        print("\n==============================")
        print(f"[{idx}/{total}] 正在處理: {p.url}")
        run_pipeline(p.url, ingest_source="B")
    print(f"\n🎉 事件爬蟲完成，本次共成功處理 {total} 條貼文")


def save_hotlist(posts: List[DiscoveredPost], keyword: str) -> str:
    os.makedirs("hotlists", exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"hotlists/hotlist_{ts}.json"

    data = []
    for p in posts:
        data.append(
            {
                "url": p.url,
                "snippet": p.snippet,
                "likes": p.likes,
                "age_label": p.age_label,
                "keyword": keyword,
                "created_at": datetime.datetime.now().isoformat(),
            }
        )

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"💾 已儲存 hotlist 至 {filename}")
    return filename


def main():
    keyword = input("請輸入關鍵字（例：宏福苑 / 大火 / 公屋）：").strip()
    if not keyword:
        print("⚠️ 關鍵字不可為空")
        return

    max_posts_raw = input("最多抓多少篇貼文？[預設 50]：").strip()
    try:
        max_posts = int(max_posts_raw) if max_posts_raw else 50
    except ValueError:
        max_posts = 50

    mode = input(
        "輸出模式： (1) 立即 ingest 至 Supabase / (2) 先輸出 hotlist.json 再手動 ingest [1/2]："
    ).strip()
    if mode not in ("1", "2"):
        mode = "1"

    discovered = discover_thread_urls(keyword, max_posts * 2)
    filtered = discovered
    ranked = rank_posts(filtered)
    final_posts = ranked[:max_posts]

    print(f"✅ 最終選定 {len(final_posts)} 條貼文（max={max_posts}）")

    if mode == "2":
        save_hotlist(final_posts, keyword)
    else:
        ingest_posts(final_posts)


if __name__ == "__main__":
    main()
