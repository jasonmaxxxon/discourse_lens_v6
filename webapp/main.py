import uuid
from typing import Optional, Callable, List

from fastapi import BackgroundTasks, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from pipelines.core import run_pipeline
from event_crawler import discover_thread_urls, rank_posts, save_hotlist, ingest_posts
from home_crawler import (
    collect_home_posts,
    filter_posts_by_threshold,
    save_home_hotlist,
    ingest_home_posts,
)

app = FastAPI()
templates = Jinja2Templates(directory="webapp/templates")
JOBS: dict[str, dict] = {}

def make_logger(job_id: str):
    def _logger(msg: str):
        job = JOBS.get(job_id)
        if not job:
            return
        job["logs"].append(msg)

    return _logger


def run_pipeline_a_job(job_id: str, url: str):
    logger = make_logger(job_id)
    try:
        JOBS[job_id]["status"] = "running"
        logger(f"🧵 Pipeline A 任務開始，URL = {url}")
        data = run_pipeline(url, ingest_source="A", return_data=True, logger=logger)
        JOBS[job_id]["post"] = data
        JOBS[job_id]["status"] = "done"
        logger("✅ Pipeline A 任務完成")
    except Exception as e:
        JOBS[job_id]["status"] = "error"
        logger(f"❌ Pipeline A 任務失敗：{e!r}")


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    """
    主控制台畫面：只給 Pipeline B / C 用，Pipeline A 由 /status/{job_id} 顯示結果。
    """
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "result": "",
            "post": None,
            "pipeline": None,
        },
    )


@app.get("/run/a", response_class=HTMLResponse)
def run_pipeline_a_get(request: Request):
    """
    防止瀏覽器對 /run/a 發 GET 時出現 405。
    例如：使用者重新整理頁面或某些 redirect 情況。
    """
    return RedirectResponse(url="/")


@app.post("/run/a", response_class=HTMLResponse)
def run_pipeline_a(
    request: Request,
    background_tasks: BackgroundTasks,
    url: str = Form(...),
):
    """
    啟動 Pipeline A：開一個 background job 抓 Threads，
    立刻回傳 /status 畫面，右側會實時更新狀態與 Logs。
    """
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {"status": "pending", "logs": [], "post": None}
    background_tasks.add_task(run_pipeline_a_job, job_id, url)

    return templates.TemplateResponse(
        "status.html",
        {
            "request": request,
            "job_id": job_id,
            "status": JOBS[job_id]["status"],
            "logs": JOBS[job_id]["logs"],
            "post": JOBS[job_id]["post"],
        },
    )


@app.post("/run/b", response_class=HTMLResponse)
def run_pipeline_b(
    request: Request,
    keyword: str = Form(...),
    max_posts: int = Form(50),
    mode: str = Form("ingest"),
):
    discovered = discover_thread_urls(keyword, max_posts * 2)
    ranked = rank_posts(discovered)
    selected = ranked[:max_posts]

    if mode == "hotlist":
        filepath = save_hotlist(selected, keyword)
        result = f"Pipeline B 完成，hotlist 已輸出：{filepath}"
    else:
        ingest_posts(selected)
        result = f"Pipeline B 完成，{len(selected)} 篇已 ingest。"

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "result": result,
            "post": None,
            "pipeline": "B",
        },
    )


@app.post("/run/c", response_class=HTMLResponse)
def run_pipeline_c(
    request: Request,
    max_posts: int = Form(50),
    threshold: int = Form(0),
    mode: str = Form("ingest"),
):
    posts = collect_home_posts(max_posts)
    filtered = filter_posts_by_threshold(posts, threshold)

    if mode == "hotlist":
        filepath = save_home_hotlist(filtered)
        result = f"Pipeline C 完成，hotlist 已輸出：{filepath}"
    else:
        ingest_home_posts(filtered)
        result = f"Pipeline C 完成，{len(filtered)} 篇已 ingest。"

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "result": result,
            "post": None,
            "pipeline": "C",
        },
    )


@app.get("/status/{job_id}", response_class=HTMLResponse)
def get_status(request: Request, job_id: str):
    """
    Pipeline A 的「實時狀態 + Threads 模擬 UI」畫面。
    meta refresh 會每 2 秒打一次這個 endpoint。
    """
    job = JOBS.get(job_id)
    if not job:
        return templates.TemplateResponse(
            "status.html",
            {
                "request": request,
                "job_id": job_id,
                "status": "not_found",
                "logs": [],
                "post": None,
            },
        )

    return templates.TemplateResponse(
        "status.html",
        {
            "request": request,
            "job_id": job_id,
            "status": job["status"],
            "logs": job["logs"],
            "post": job["post"],
        },
    )
