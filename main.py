from pipelines.core import run_pipeline


if __name__ == "__main__":
    mode = input("輸入模式: (1) 單一URL / (2) 多條URL列表 [1/2]：").strip()

    if mode == "2":
        print("請輸入多條 URL，每行一條，輸入空行結束：")
        urls = []
        while True:
            line = input().strip()
            if not line:
                break
            # 自動 threads.com → threads.net
            if "threads.com" in line:
                line = line.replace("threads.com", "threads.net")
                print(f"🔁 偵測到 threads.com，已自動改成：{line}")
            urls.append(line)

        for url in urls:
            print("\n==============================")
            print(f"正在處理: {url}")
            run_pipeline(url, ingest_source="A")
        print("\n🎉 批次處理完成。")
    else:
        url = input("請輸入 Threads URL：").strip()

        # 自動 threads.com → threads.net
        if "threads.com" in url:
            url = url.replace("threads.com", "threads.net")
            print(f"🔁 偵測到 threads.com，已自動改成：{url}")

        run_pipeline(url, ingest_source="A")
