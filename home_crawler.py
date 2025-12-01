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
class HomePost:
    url: str
    snippet: str
    likes: Optional[int] = None
    reply_count: int = 0
    age_label: Optional[str] = None


def _clean_snippet(text: str) -> str:
    if not text:
        return ""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    snippet = " ".join(lines)
    return snippet[:500]


def _extract_likes_from_text(text: str) -> Optional[int]:
    if not text:
        return None
    m = re.search(r"([\d\.,]+\s*[KMkm]?)\s*(?:likes?|讚)", text)
    if not m:
        return None
    return parse_number(m.group(1))


def _extract_reply_count_from_text(text: str) -> Optional[int]:
    if not text:
        return None
    m = re.search(r"([\d\.,]+\s*[KMkm]?)\s*(?:repl(?:y|ies)|comments?|回覆|留言)", text, re.IGNORECASE)
    if not m:
        return None
    return parse_number(m.group(1))


def _extract_age_label(text: str) -> Optional[str]:
    if not text:
        return None
    m = re.search(r"\b\d+\s*[smhdw]\b", text)
    return m.group(0) if m else None


def _harvest_home_posts(page, seen: Dict[str, HomePost]):
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
        reply_count = 0
        age_label = None

        try:
            container = anchor.query_selector("xpath=../..") or anchor
            container_text = container.text_content() or ""
            snippet_text = _clean_snippet(container_text)
            likes = _extract_likes_from_text(container_text)
            reply_count = _extract_reply_count_from_text(container_text) or 0
            age_label = _extract_age_label(container_text)
        except Exception:
            snippet_text = ""

        seen[url] = HomePost(url=url, snippet=snippet_text, likes=likes, reply_count=reply_count, age_label=age_label)


def collect_home_posts(max_posts: int) -> List[HomePost]:
    if not os.path.exists(AUTH_FILE):
        raise FileNotFoundError("⚠️ 找不到 auth_threads.json，請先執行 scraper/login.py。")

    headless_flag = os.environ.get("DLENS_HEADLESS", "1") != "0"
    collected: Dict[str, HomePost] = {}
    target = max_posts

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless_flag)
        context = browser.new_context(storage_state=AUTH_FILE)
        page = context.new_page()

        print("🏠 正在開啟 Threads Home timeline ...")
        page.goto("https://www.threads.net/", timeout=60000, wait_until="load")
        page.wait_for_load_state("networkidle")
        time.sleep(1.5)

        print("📄 Home 頁面已載入，開始捲動...")

        stable_rounds = 0
        last_height = 0
        loop = 0
        while len(collected) < target and stable_rounds < 4:
            loop += 1
            _harvest_home_posts(page, collected)
            print(f"🔗 目前已收集 {len(collected)} 條貼文 URL...")

            page.mouse.wheel(0, 2800)
            page.wait_for_timeout(1200)
            height = page.evaluate("document.body.scrollHeight")
            if height == last_height:
                stable_rounds += 1
            else:
                stable_rounds = 0
            last_height = height

        print(f"✅ Home URL 抽樣完成，最終取得 {len(collected)} 條（限制：{max_posts}）")
        browser.close()

    posts_list = list(collected.values())
    if len(posts_list) > max_posts:
        posts_list = posts_list[:max_posts]
    return posts_list


def filter_posts_by_threshold(posts: List[HomePost], threshold: int) -> List[HomePost]:
    if threshold <= 0:
        return posts
    kept = []
    for p in posts:
        replies = p.reply_count
        likes = p.likes
        if replies is not None and replies >= threshold:
            kept.append(p)
        elif replies is None and likes is not None and likes >= threshold:
            kept.append(p)
        elif replies == 0 and likes is not None and likes >= threshold:
            kept.append(p)
    return kept


def ingest_home_posts(posts: List[HomePost]):
    total = len(posts)
    for idx, p in enumerate(posts, start=1):
        print("\n==============================")
        print(f"[{idx}/{total}] 正在處理: {p.url}")
        try:
            run_pipeline(p.url, ingest_source="C")
        except Exception as e:
            print(f"⚠️ 處理 {p.url} 時發生錯誤：{e}")
    print(f"\n🎉 Home 抽樣處理完成，本次共成功處理 {total} 條貼文")


def save_home_hotlist(posts: List[HomePost]) -> str:
    os.makedirs("hotlists", exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"hotlists/home_hotlist_{ts}.json"

    data = []
    for p in posts:
        data.append(
            {
                "url": p.url,
                "snippet": p.snippet,
                "likes": p.likes,
                "reply_count": p.reply_count,
                "age_label": p.age_label,
                "created_at": datetime.datetime.now().isoformat(),
            }
        )

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"💾 已儲存 hotlist 至 {filename}")
    return filename


def _input_with_default(prompt: str, default: str) -> str:
    raw = input(prompt).strip()
    return raw if raw else default


def main():
    max_posts_raw = _input_with_default("最多抓多少篇貼文？[預設 50]：", "50")
    try:
        max_posts = int(max_posts_raw)
    except ValueError:
        max_posts = 50

    threshold_raw = _input_with_default("留言數（或 likes）門檻？[預設 0]：", "0")
    try:
        threshold = int(threshold_raw)
    except ValueError:
        threshold = 0

    mode_raw = _input_with_default("輸出模式： (1) 立即 ingest 至 Supabase / (2) 先輸出 hotlist.json 再手動 ingest [1/2]：", "1")
    mode = mode_raw.strip()
    if mode not in {"1", "2"}:
        mode = "1"

    posts = collect_home_posts(max_posts)
    print(f"📥 Home 抽樣完成，共取得 {len(posts)} 條貼文")

    filtered = filter_posts_by_threshold(posts, threshold)
    print(f"✅ 通過留言/likes 門檻的貼文：{len(filtered)} / {len(posts)}")

    if mode == "2":
        path = save_home_hotlist(filtered)
        print(f"🚦 已輸出 hotlist.json：{path}，可稍後再執行 ingest")
        return

    ingest_home_posts(filtered)
    print(f"✅ 已 ingest {len(filtered)} 篇貼文")


if __name__ == "__main__":
    main()
