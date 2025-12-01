from playwright.sync_api import sync_playwright
import time
import os

AUTH_FILE = "auth_threads.json"


def deep_scroll_comments(page, max_loops: int = 15, target_comment_blocks: int = 80):
    """
    深度捲動頁面並嘗試展開更多留言 / 回覆。
    - 透過滑鼠滾動向下載入更多內容
    - 嘗試點擊 "View more replies" / "View more" / "Show replies"
    - 若 scrollHeight 多次未變化則提前停止
    - 若留言 block 數量已達 target_comment_blocks 也會提前停止
    """
    stable_count = 0
    last_height = 0
    expand_texts = ["View more replies", "View more", "Show replies"]

    for _ in range(max_loops):
        # 向下捲動一大段
        page.mouse.wheel(0, 3000)
        page.wait_for_timeout(1500)

        # 嘗試展開「更多留言 / 更多回覆」
        for text in expand_texts:
            try:
                for btn in page.get_by_text(text, exact=False).all():
                    btn.click(timeout=2000)
                    page.wait_for_timeout(500)
            except Exception:
                # 找不到就算，繼續下一輪
                pass

        # 檢查目前留言 block 數量（第一個通常是主文，所以減 1）
        blocks = page.query_selector_all('div[data-pressable-container="true"]')
        if len(blocks) - 1 >= target_comment_blocks:
            break

        # 檢查 scrollHeight 是否還有變化
        height = page.evaluate("document.body.scrollHeight")
        if height == last_height:
            stable_count += 1
        else:
            stable_count = 0
        last_height = height

        if stable_count >= 3:
            break


def normalize_url(url: str) -> str:
    # 如果是 threads.com，就自動改成 threads.net
    if "threads.com" in url:
        new_url = url.replace("threads.com", "threads.net")
        print(f"🔁 偵測到 threads.com，已自動改成：{new_url}")
        return new_url
    return url


def fetch_page_html(url: str, target_comment_blocks: int = 80) -> dict:
    """
    打開 Threads 貼文並返回「兩份」HTML：
    - initial_html  : 只等首次載入完成，尚未深度捲動 → 一定包含畫面上第一批 Top comments
    - scrolled_html : 經過 deep_scroll_comments 後的完整 DOM → 用來抓更多留言樣本

    回傳格式：
    {
        "initial_html": "<html ...>...</html>",
        "scrolled_html": "<html ...>...</html>",
    }
    """

    if not os.path.exists(AUTH_FILE):
        raise FileNotFoundError("⚠️ 找不到 auth_threads.json，請先執行 login.py。")

    url = normalize_url(url)
    initial_html = ""
    scrolled_html = ""

    headless_flag = os.environ.get("DLENS_HEADLESS", "1") != "0"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless_flag)
        context = browser.new_context(storage_state=AUTH_FILE)
        page = context.new_page()

        try:
            print(f"🕸️ 正在載入 {url} ...")
            response = page.goto(url, timeout=60000, wait_until="load")

            if response is None:
                print("⚠️ 沒有拿到任何 HTTP 回應 (response is None)")
                browser.close()
                return {"initial_html": "", "scrolled_html": ""}

            status = response.status
            print(f"📡 HTTP 狀態碼：{status}")

            if status < 200 or status >= 300:
                print("❌ 非 2xx 回應（可能是 404/403/500 等），無法抓取此頁。")
                browser.close()
                return {"initial_html": "", "scrolled_html": ""}

            # 等待網路穩定，先抓「初始畫面」HTML → 這一刻的 Top comments 一定在 DOM 裡
            page.wait_for_load_state("networkidle")
            time.sleep(3)
            initial_html = page.content()
            print(f"✅ 初始 HTML 抓取完成，長度：{len(initial_html)} 字元")

            # 深度捲動載入更多留言 & 展開「View more replies」
            print("🔁 深度捲動留言區...")
            deep_scroll_comments(page, target_comment_blocks=target_comment_blocks)

            # 深度捲動後，為了保證 Top comments 仍然在 DOM 中，再把畫面捲回最上方
            page.evaluate("window.scrollTo(0, 0);")
            page.wait_for_timeout(1500)

            scrolled_html = page.content()
            print(f"✅ 深度捲動後 HTML 抓取完成，長度：{len(scrolled_html)} 字元")

        except Exception as e:
            print(f"❌ Fetch Error: {e}")
        finally:
            browser.close()

    return {"initial_html": initial_html, "scrolled_html": scrolled_html}
