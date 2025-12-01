from bs4 import BeautifulSoup
import re

# UI 垃圾字，不能當作者 / user / 內容
UI_TOKENS = {
    "follow",
    "following",
    "more",
    "top",
    "translate",
    "verified",
    "edited",
    "author",
    "liked by original author",
}

# 留言 / 主文 footer 區的 token
FOOTER_TOKENS = {"translate", "like", "reply", "repost", "share"}

# 時間格式：2d, 17h, 5m, 3w
TIME_PATTERN = re.compile(r"^\d+\s*[smhdw]$")


def parse_number(text: str) -> int:
    """
    安全解析 like / view / reply / repost / share 數：
    - 支援: '1', '12', '1.2K', '3.4M'
    - 忽略: 沒數字的字串
    """
    if not text:
        return 0

    clean = text.replace(",", "").upper()
    m = re.search(r"([\d\.]+)\s*([KM]?)", clean)
    if not m:
        return 0

    num = float(m.group(1))
    suffix = m.group(2)

    if suffix == "K":
        num *= 1000
    elif suffix == "M":
        num *= 1_000_000

    return int(num)


def extract_block_user(lines) -> str:
    """
    從一個 block（主文 / 留言）裡抽出 user：
    - 跳過 Follow / More / Translate 等 UI
    - 跳過時間 2d / 17h
    - 跳過 Verified / Edited / Author / Liked by original author
    """
    for line in lines:
        candidate = line.strip()
        if not candidate:
            continue
        lower = candidate.lower()
        if lower in UI_TOKENS:
            continue
        if TIME_PATTERN.match(lower):
            continue
        # 有些會是 'ukiii.zzzzz · Author'，簡單切掉後半
        if "·" in candidate:
            candidate = candidate.split("·", 1)[0].strip()
        return candidate
    return ""


def extract_block_likes(lines) -> int:
    """
    從 block 的行裡找 Like 數：
    - 找到第一個 'Like' 行 → 下一行當作數字
    """
    for i, line in enumerate(lines):
        if line.strip().lower() == "like" and i + 1 < len(lines):
            return parse_number(lines[i + 1])
    return 0


def extract_block_body(lines) -> str:
    """
    從 block（主文 / 留言）中抽出「純內容」：
    - 如果有 'More'：從 'More' 的下一行開始
    - 沒有 'More'：從第一個非 UI / 非時間行開始
    - 在遇到 Translate / Like / Reply / Repost / Share 時結束
    """
    start_idx = 0

    # 先找 'More'
    found_more = False
    for i, line in enumerate(lines):
        if line.strip().lower() == "more":
            start_idx = i + 1
            found_more = True
            break

    # 沒有 'More' 的情況：從第一個非 UI / 非時間行開始
    if not found_more:
        for i, line in enumerate(lines):
            candidate = line.strip()
            if not candidate:
                continue
            lower = candidate.lower()
            if lower in UI_TOKENS:
                continue
            if TIME_PATTERN.match(lower):
                continue
            start_idx = i
            break

    body_lines = []
    for line in lines[start_idx:]:
        lower = line.strip().lower()
        if lower in FOOTER_TOKENS:
            break
        body_lines.append(line)

    return "\n".join(body_lines).strip()


def extract_metrics_from_lines(lines) -> dict:
    """
    從主文 lines 裡抽出:
    - likes
    - reply_count
    - repost_count
    - share_count
    """
    likes = reply_count = repost_count = share_count = 0

    for i, line in enumerate(lines):
        lower = line.strip().lower()
        # Like
        if lower == "like" and i + 1 < len(lines):
            likes = parse_number(lines[i + 1])
        # Reply / Replies
        if lower in ("reply", "replies") and i + 1 < len(lines):
            reply_count = parse_number(lines[i + 1])
        # Repost
        if lower == "repost" and i + 1 < len(lines):
            repost_count = parse_number(lines[i + 1])
        # Share
        if lower == "share" and i + 1 < len(lines):
            share_count = parse_number(lines[i + 1])

    return {
        "likes": likes,
        "reply_count": reply_count,
        "repost_count": repost_count,
        "share_count": share_count,
    }


def _parse_single_html(html: str, url: str) -> dict:
    """
    單次 HTML → 結構化資料。
    用來支援：
      1) 初始畫面 (Top comments snapshot)
      2) 深度捲動後畫面
    """
    soup = BeautifulSoup(html, "html.parser")

    data = {
        "url": url,
        "author": "",
        "post_text": "",
        "post_text_raw": "",
        "metrics": {
            "likes": 0,
            "views": 0,
            "reply_count": 0,
            "repost_count": 0,
            "share_count": 0,
        },
        "images": [],
        "comments": [],
    }

    posts = soup.find_all("div", {"data-pressable-container": "true"})
    if not posts:
        return data

    # 主文
    main_post = posts[0]
    full_text = main_post.get_text("\n", strip=True)
    data["post_text_raw"] = full_text
    lines = full_text.split("\n")

    # 圖片
    for img in main_post.find_all("img"):
        alt = img.get("alt", "") or ""
        if "profile picture" in alt.lower():
            continue
        src = img.get("src", "").strip()
        if not src:
            srcset = img.get("srcset", "")
            if srcset:
                src = srcset.split(" ", 1)[0].strip()
        if not src:
            continue
        if "s150x150" in src:
            continue
        data["images"].append({"src": src, "alt": alt})

    # 作者 + 主文內容 + 互動數
    data["author"] = extract_block_user(lines)
    data["post_text"] = extract_block_body(lines)

    m = extract_metrics_from_lines(lines)
    data["metrics"]["likes"] = m["likes"]
    data["metrics"]["reply_count"] = m["reply_count"]
    data["metrics"]["repost_count"] = m["repost_count"]
    data["metrics"]["share_count"] = m["share_count"]

    # Views
    views = 0
    for text_node in soup.stripped_strings:
        low = text_node.lower()
        # 避免吃到 "View 3 more replies"
        if "views" in low and "reply" not in low and "view more" not in low:
            views = parse_number(text_node)
            break
    data["metrics"]["views"] = views

    # 留言區：posts[1:] 每一個都是一個留言 block
    for block in posts[1:]:
        raw_block = block.get_text("\n", strip=True)
        if not raw_block:
            continue

        block_lines = raw_block.split("\n")
        c_user = extract_block_user(block_lines)
        c_likes = extract_block_likes(block_lines)
        c_body = extract_block_body(block_lines)

        if not c_user and not c_body:
            continue

        data["comments"].append(
            {
                "user": c_user,
                "text": c_body,
                "likes": c_likes,
                "raw": raw_block,
            }
        )

    return data


def extract_data_from_html(html_or_bundle, url: str) -> dict:
    """
    將 Threads 單帖的 HTML 解析成結構化 dict。
    支援兩種輸入：
      1) 舊版：單一 HTML 字串
      2) 新版：{"initial_html": ..., "scrolled_html": ...}

    新版策略：
      - initial_html：畫面剛載入時的 DOM → 一定包含 UI 顯示的 Top comments
      - scrolled_html：深度捲動後的 DOM → 載入更多留言
      - 兩者的 comments 會合併去重，並標記 from_top_snapshot=True/False
      - comments_by_likes：根據 likes 排序好的視圖，用於「高讚好留言 Top 5」
    """
    if isinstance(html_or_bundle, dict):
        initial_html = html_or_bundle.get("initial_html") or ""
        scrolled_html = html_or_bundle.get("scrolled_html") or ""
    else:
        # 向下兼容：只給一份 HTML 的舊用法
        initial_html = ""
        scrolled_html = html_or_bundle or ""

    # 先用「優先 scrolled_html，沒有就用 initial_html」當主資料
    main_html = scrolled_html or initial_html
    base = _parse_single_html(main_html, url)

    # 從深度捲動後 HTML 抓到的留言
    comments_scrolled = list(base.get("comments", []))

    # 再從 initial_html 再解析一次，專門抓「剛開頁時的 Top comments」
    comments_initial = []
    if initial_html:
        top_struct = _parse_single_html(initial_html, url)
        comments_initial = top_struct.get("comments", [])

        # 若 main_html 其實就是 initial_html（沒有 scrolled_html），則不需要再合併一次
        if not scrolled_html:
            comments_scrolled = []

    # 合併兩邊留言，去重，並標示來源
    merged_comments = []
    seen_keys = set()

    for src_list, is_top in ((comments_initial, True), (comments_scrolled, False)):
        for c in src_list:
            key = (c.get("user", ""), c.get("text", ""))
            if key in seen_keys:
                continue
            seen_keys.add(key)
            c["from_top_snapshot"] = is_top
            merged_comments.append(c)

    base["comments"] = merged_comments

    # 重新計算「抓到的實際留言數」與按讚排序視圖
    comments_sorted = sorted(
        merged_comments,
        key=lambda c: c.get("likes", 0),
        reverse=True,
    )
    base["comments_by_likes"] = comments_sorted

    # reply_count 至少不會小於實際抓到的留言樣本數
    base["metrics"]["reply_count"] = max(
        base["metrics"].get("reply_count", 0),
        len(merged_comments),
    )

    return base
