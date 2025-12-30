import uuid
import logging
from typing import Optional
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, field_validator

load_dotenv()

from database.store import supabase

# 修正 Import路徑：指向 routers 資料夾
from webapp.routers.api import router as api_router
from webapp.routers import jobs  # [NEW] 引入新的 Jobs Router

from webapp.services import job_store
from webapp.services import pipeline_runner as runner
from webapp.services.job_manager import JobManager
from webapp.schemas.jobs import JobCreate
from webapp.services import ops_pipeline_a_bridge

logger = logging.getLogger("dl")

app = FastAPI()

# 設定 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# [Existing] 掛載原本的 API Router
app.include_router(api_router, prefix="/api")

# [NEW] 掛載 Batch Jobs Router (CDX-091)
app.include_router(jobs.router, prefix="/api/jobs", tags=["Batch Jobs"])

templates = Jinja2Templates(directory="webapp/templates")

def create_app() -> FastAPI:
    """
    Return the configured FastAPI application.
    """
    return app

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    return JSONResponse(
        {
            "detail": "Unhandled exception",
            "error_type": type(exc).__name__,
            "error": str(exc),
        },
        status_code=500,
    )


def normalize_like_counts(comments: list) -> list:
    """
    Ensure every comment has an integer like_count, falling back to 'likes'.
    Mutates the list in place and also returns it.
    """
    if not comments:
        return comments
    for c in comments:
        if not isinstance(c, dict):
            continue
        val = c.get("like_count")
        if val is None:
            val = c.get("likes", 0)
        try:
            c["like_count"] = int(val)
        except Exception:
            c["like_count"] = 0
    return comments


# --- API Schemas ---


class AcademicReference(BaseModel):
    author: str
    year: str
    note: str


class SectionOne(BaseModel):
    executive_summary: str
    phenomenon_spotlight: str
    l1_analysis: str
    l2_analysis: str
    l3_analysis: str
    faction_analysis: str
    strategic_implication: str
    author_influence: str | None = None
    academic_references: list[AcademicReference] | None = None


class AnalysisMeta(BaseModel):
    Post_ID: str
    Timestamp: str
    High_Impact: bool


class QuantifiableTags(BaseModel):
    Sector_ID: str
    Primary_Emotion: str
    Strategy_Code: str
    Civil_Score: int
    Homogeneity_Score: float
    Author_Influence: str


class PostStats(BaseModel):
    Likes: int
    Replies: int
    Views: int


class ClusterInsight(BaseModel):
    name: str
    summary: str
    pct: float | None = None


class DiscoveryChannel(BaseModel):
    Sub_Variant_Name: str
    Is_New_Phenomenon: bool
    Phenomenon_Description: str


class StrategySnippetModel(BaseModel):
    name: str
    intensity: float
    description: str
    example: str
    citation: str


class ToneFingerprintModel(BaseModel):
    assertiveness: float
    cynicism: float
    playfulness: float
    contempt: float
    description: str
    example: str


class FactionSummaryModel(BaseModel):
    label: str
    dominant: bool | None = None
    summary: str
    bullets: list[str]


class CommentSampleModel(BaseModel):
    author: str
    text: str
    likes: int
    faction: str | None = None
    tags: list[str] | None = None


class NarrativeShiftNodeModel(BaseModel):
    stage: str
    label: str


class SectionTwo(BaseModel):
    analysis_meta: AnalysisMeta
    quantifiable_tags: QuantifiableTags
    post_stats: PostStats
    cluster_insights: dict[str, ClusterInsight]
    discovery_channel: DiscoveryChannel


class PostAnalysisResponse(BaseModel):
    section1: SectionOne
    section2: SectionTwo
    strategies: list[StrategySnippetModel]
    tone: ToneFingerprintModel
    factions: list[FactionSummaryModel]
    comment_samples: list[CommentSampleModel]
    narrative_shift: list[NarrativeShiftNodeModel]


class RawAnalysisResponse(BaseModel):
    post_id: str
    full_report_markdown: str


class PostListItem(BaseModel):
    id: str
    snippet: str
    created_at: str | None = None
    author: str | None = None
    like_count: int | None = None
    reply_count: int | None = None
    view_count: int | None = None
    has_analysis: bool = False
    analysis_is_valid: bool | None = None
    analysis_version: str | None = None
    analysis_build_id: str | None = None
    archive_captured_at: str | None = None
    archive_build_id: str | None = None
    has_archive: bool | None = None
    ai_tags: list[str] | None = None
    phenomenon_id: str | None = None
    phenomenon_status: str | None = None
    phenomenon_case_id: str | None = None
    phenomenon_name: str | None = None


class JobPostResult(BaseModel):
    post_id: Optional[str] = None
    has_analysis: Optional[bool] = None
    analysis_is_valid: Optional[bool] = None
    analysis_version: Optional[str] = None
    analysis_build_id: Optional[str] = None
    invalid_reason: Optional[str] = None
    archive_captured_at: Optional[str] = None
    archive_build_id: Optional[str] = None

    @field_validator("post_id", mode="before")
    def _coerce_post_id(cls, v):
        if v is None:
            return v
        return str(v)


class JobResult(BaseModel):
    status: str
    pipeline: str
    job_id: str
    mode: Optional[str] = None
    post_id: Optional[str] = None
    posts: Optional[List[JobPostResult]] = None
    summary: Optional[str] = None
    logs: Optional[List[str]] = None
    error_stage: Optional[str] = None
    error_message: Optional[str] = None

    @field_validator("post_id", mode="before")
    def _coerce_post_id(cls, v):
        if v is None:
            return v
        return str(v)


SAMPLE_ANALYSIS = PostAnalysisResponse(
    section1=SectionOne(
        executive_summary="貼文在表面祝賀中隱藏反諷，留言區迅速轉為犬儒嘲諷，主要關切選舉的工具性與制度可信度。",
        phenomenon_spotlight="從『被選上就領薪水』的戲謔出發，快速引發對整個制度的認受性質疑。",
        l1_analysis="語氣帶有戲謔式斷言，表面提問實則貶抑，常用反問與冷笑詞彙。",
        l2_analysis="主策略為 Moral Framing + Cynical Detachment，透過道德對比顯得當選人不配。",
        l3_analysis="兩大派系：犬儒批評者佔多數且高互動；務實憂慮者聲量小但想提醒實務責任。",
        faction_analysis="犬儒派掌握頭部讚數，將話題導向制度荒謬；務實派則在尾段補充，未能帶動共鳴。",
        strategic_implication="此場域呈現低風險的日常化抵抗，對制度信任度與官方敘事造成慢性侵蝕。",
        author_influence="Medium",
        academic_references=[
            AcademicReference(author="Searle", year="1969", note="Illocutionary acts framing the mock praise."),
            AcademicReference(author="Fairclough", year="1995", note="Discourse practice revealing institutional legitimacy struggles."),
            AcademicReference(author="Scott", year="1985", note="Weapons of the Weak: quotidian resistance via sarcasm."),
        ],
    ),
    section2=SectionTwo(
        analysis_meta=AnalysisMeta(Post_ID="187", Timestamp="2025-12-08T21:52:19.462118", High_Impact=False),
        quantifiable_tags=QuantifiableTags(
            Sector_ID="Sector_A",
            Primary_Emotion="Cynicism",
            Strategy_Code="MORAL_FRAMING",
            Civil_Score=4,
            Homogeneity_Score=0.87,
            Author_Influence="Medium",
        ),
        post_stats=PostStats(Likes=0, Replies=0, Views=81000),
        cluster_insights={
            "0": ClusterInsight(
                name="務實憂慮者",
                summary="表達對當選人僅為薪酬而任職、未必履行職責的直接擔憂。",
                pct=0.107,
            ),
            "1": ClusterInsight(
                name="犬儒批評者",
                summary="透過辛辣嘲諷與戲謔，質疑整個選舉制度的認受性及當選人的能力。",
                pct=0.714,
            ),
        },
        discovery_channel=DiscoveryChannel(
            Sub_Variant_Name="Transactional_Devaluation",
            Is_New_Phenomenon=False,
            Phenomenon_Description=
            "The act of reframing a political achievement as purely transactional, eroding its legitimacy and symbolic power.",
        ),
    ),
    strategies=[
        StrategySnippetModel(
            name="Moral Framing",
            intensity=0.8,
            description="對比『領薪水』與『應有責任』以凸顯道德落差。",
            example="冇心做嘢都可以攞人工？",
            citation="Fairclough 1995",
        ),
        StrategySnippetModel(
            name="Cynical Detachment",
            intensity=0.9,
            description="以玩笑形式切斷對政治承諾的信任。",
            example="領完薪水走人啦，做咩仲裝認真？",
            citation="Scott 1985",
        ),
        StrategySnippetModel(
            name="Playful Irony",
            intensity=0.6,
            description="用輕快口吻包裝嘲諷以降低風險。",
            example="咁都得？真係天下武功唯快不破。",
            citation="Martin & White 2005",
        ),
    ],
    tone=ToneFingerprintModel(
        assertiveness=0.72,
        cynicism=0.88,
        playfulness=0.64,
        contempt=0.55,
        description="戲謔式斷言，表面提問、實為貶抑，帶有冷感旁觀。",
        example="選到就有人工，做唔做到唔緊要啦。",
    ),
    factions=[
        FactionSummaryModel(
            label="犬儒批評者",
            dominant=True,
            summary="以辛辣嘲諷質疑制度及當選人。",
            bullets=["高互動量、掌握頭部按讚", "擅用戲謔與貶抑", "將焦點轉向制度荒謬"],
        ),
        FactionSummaryModel(
            label="務實憂慮者",
            dominant=False,
            summary="強調履職與公共責任，聲量偏小。",
            bullets=["關注實際執行", "用平實語氣提醒責任", "互動量較低"],
        ),
    ],
    comment_samples=[
        CommentSampleModel(
            author="@hau__cho",
            text="咁都叫成功？領薪水先係重點啦。",
            likes=1200,
            faction="犬儒批評者",
            tags=["Cynicism", "Irony"],
        ),
        CommentSampleModel(
            author="@pragmatichk",
            text="希望唔好淨係簽到，真係要做嘢。",
            likes=320,
            faction="務實憂慮者",
            tags=["Concern", "Duty"],
        ),
        CommentSampleModel(
            author="@lol_but_true",
            text="咁既制度仲講專業？笑死。",
            likes=850,
            faction="犬儒批評者",
            tags=["Sarcasm"],
        ),
    ],
    narrative_shift=[
        NarrativeShiftNodeModel(stage="Post", label="Public service / 政治理想"),
        NarrativeShiftNodeModel(stage="Head", label="功能性嘲諷"),
        NarrativeShiftNodeModel(stage="Mid", label="犬儒批評擴散"),
        NarrativeShiftNodeModel(stage="Tail", label="制度失望 / 無力感"),
    ],
)

def make_logger(job_id: str):
    def _logger(msg: str):
        job = JOBS.get(job_id)
        if not job:
            return
        job["logs"].append(msg)
        print(f"[{job_id[:8]}] {msg}")

    return _logger


def generate_battlefield_chart_html(comments, cluster_summary=None):
    if not comments:
        return "<div>No Data</div>"
    try:
        df = pd.DataFrame(comments)
    except Exception:
        return "<div>Data format error</div>"
    if "quant_x" not in df.columns or "quant_y" not in df.columns:
        return "<div>No Coordinates</div>"

    def _like_count(val):
        try:
            return int(val)
        except Exception:
            return 0

    label_map = {}
    if cluster_summary and isinstance(cluster_summary, dict):
        clusters = cluster_summary.get("clusters") or {}
        if isinstance(clusters, dict):
            for cid_key, info in clusters.items():
                if not isinstance(info, dict):
                    continue
                label = info.get("name") or f"Cluster {cid_key}"
                try:
                    cid_int = int(cid_key)
                except Exception:
                    cid_int = cid_key
                label_map[str(cid_key)] = label
                label_map[cid_int] = label

    def _label_for_cluster(cid):
        try:
            cid_int = int(cid)
        except Exception:
            cid_int = -1
        if cid_int == -1:
            return "Noise"
        return label_map.get(cid_int) or label_map.get(str(cid_int)) or f"Cluster {cid_int}"

    df["quant_cluster_id"] = df.get("quant_cluster_id", pd.Series([-1] * len(df)))
    df["ClusterLabel"] = df["quant_cluster_id"].apply(_label_for_cluster)
    df["like_count"] = df.get("like_count", df.get("likes", pd.Series([0] * len(df)))).apply(_like_count)
    df["like_count"] = pd.to_numeric(df["like_count"], errors="coerce").fillna(0)
    df["hover_user"] = df.get("user", pd.Series(["Unknown"] * len(df)))
    df["hover_likes"] = df["like_count"]
    df["hover_text"] = df.get("text", pd.Series([""] * len(df))).apply(lambda t: str(t)[:80])
    df["Label"] = df["ClusterLabel"]
    df["label"] = df["ClusterLabel"]
    df["cluster_id"] = df["quant_cluster_id"]

    df["size_val"] = df["like_count"].apply(lambda v: max(np.log1p(max(v, 0)) * 6.0, 6.0))

    fig = px.scatter(
        df,
        x="quant_x",
        y="quant_y",
        color="label",
        size="size_val",
        hover_name="hover_user",
        hover_data={"text": True, "like_count": True, "cluster_id": True, "label": True},
        size_max=40,
        title="Semantic Battlefield (輿論地形圖)",
        template="plotly_dark",
        height=400,
    )
    if not df.empty:
        max_size = float(df["size_val"].max())
        sizeref = max_size / (40.0 ** 2) if max_size > 0 else 1.0
        fig.update_traces(
            marker=dict(
                sizemode="area",
                sizeref=sizeref,
                opacity=0.7,
            )
        )
    fig.update_xaxes(title_text="Semantic Dimension 1")
    fig.update_yaxes(title_text="Semantic Dimension 2")
    fig.update_layout(
        legend_title="派系 (Faction)",
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
    )

    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn")



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


@app.post("/run/a")
async def run_pipeline_a(
    request: Request,
    background_tasks: BackgroundTasks,
    url: str = Form(...),
):
    """
    Launch Pipeline A and Redirect to Logistics Dashboard.
    """
    manager = JobManager()

    # 1. Create Job Header
    job_in = JobCreate(
        pipeline_type="A",
        mode="analyze",
        input_config={"url": url, "source": "/run/a"},
    )
    job_id = await manager.create_job(job_in)
    logger.info(f"[/run/a] Created Job: {job_id} for URL: {url}")

    # 2. Insert the Single Item
    item_data = [
        {
            "job_id": job_id,
            "target_id": url,
            "status": "pending",
            "stage": "init",
        }
    ]
    insert_resp = await manager._table_insert("job_items", item_data)
    logger.info(f"[/run/a] Inserted 1 job_item for {job_id}")

    # Hard-assert items exist
    items_after, _items_degraded = await manager.get_job_items(job_id, limit=2)
    if not items_after:
        logger.error(f"[/run/a] OPS_ITEM_MISSING job_id={job_id} url={url} resp={insert_resp}")
        raise HTTPException(status_code=500, detail="Failed to register job items")

    # 3. Update Job Header Status
    await manager.mark_job_processing(job_id, total_count=1)
    logger.info(f"[/run/a] Set status=processing for {job_id}")

    # 4. Dispatch Bridge Task
    background_tasks.add_task(ops_pipeline_a_bridge.run_pipeline_a_with_ops, job_id, url)

    # 5. Redirect to Dashboard with Job ID
    return RedirectResponse(url=f"/ops/jobs?job_id={job_id}", status_code=303)


@app.post("/run/b", response_class=HTMLResponse)
def run_pipeline_b(
    request: Request,
    background_tasks: BackgroundTasks,
    keyword: str = Form(...),
    max_posts: int = Form(50),
    mode: str = Form("ingest"),
    reprocess_policy: str = Form("skip_if_exists"),
):
    job_store.cleanup_jobs()
    job_id = str(uuid.uuid4())
    job_store.create_job(
        job_id,
        "B",
        mode,
        {
            "posts": [],
            "summary": "",
        },
    )
    background_tasks.add_task(runner.run_pipeline_b_job, job_id, keyword, max_posts, mode, reprocess_policy)
    job = job_store.get_job(job_id) or {}

    return templates.TemplateResponse(
        "status.html",
        {
            "request": request,
            "job_id": job_id,
            "status": job.get("status"),
            "logs": job.get("logs", []),
            "post": None,
            "posts": job.get("posts", []),
            "pipeline": "B",
            "summary": job.get("summary", ""),
        },
    )


@app.post("/run/c", response_class=HTMLResponse)
def run_pipeline_c(
    request: Request,
    background_tasks: BackgroundTasks,
    max_posts: int = Form(50),
    threshold: int = Form(0),
    mode: str = Form("ingest"),
):
    job_store.cleanup_jobs()
    job_id = str(uuid.uuid4())
    job_store.create_job(
        job_id,
        "C",
        mode,
        {
            "posts": [],
            "summary": "",
        },
    )
    background_tasks.add_task(runner.run_pipeline_c_job, job_id, max_posts, threshold, mode)
    job = job_store.get_job(job_id) or {}

    return templates.TemplateResponse(
        "status.html",
        {
            "request": request,
            "job_id": job_id,
            "status": job.get("status"),
            "logs": job.get("logs", []),
            "post": None,
            "posts": job.get("posts", []),
            "pipeline": "C",
            "summary": job.get("summary", ""),
        },
    )


@app.get("/status/{job_id}", response_class=HTMLResponse)
def get_status(request: Request, job_id: str):
    """
    Pipeline A 的「實時狀態 + Threads 模擬 UI」畫面。
    meta refresh 會每 2 秒打一次這個 endpoint。
    """
    job_store.cleanup_jobs()
    job = job_store.get_job(job_id)
    if not job:
        return templates.TemplateResponse(
            "status.html",
            {
                "request": request,
                "job_id": job_id,
                "status": "not_found",
                "logs": [],
                "post": None,
                "posts": [],
                "pipeline": "A",
                "summary": "",
            },
        )
    pipeline = job.get("pipeline", "A")
    ctx = {
        "request": request,
        "job_id": job_id,
        "status": job.get("status"),
        "logs": job.get("logs", []),
        "pipeline": pipeline,
        "posts": job.get("posts", []),
        "summary": job.get("summary", ""),
        "ai_analysis": job.get("ai_analysis"),
    }

    if pipeline == "A":
        post = job.get("post")
        if post and post.get("url"):
            try:
                resp = (
                    supabase.table("threads_posts")
                    .select("images, ai_tags, full_report, quant_summary, raw_comments, view_count, cluster_summary")
                    .eq("url", post.get("url"))
                    .execute()
                )
                if resp.data:
                    db_row = resp.data[0]
                    post["images"] = db_row.get("images") or []
                    post["ai_tags"] = db_row.get("ai_tags")
                    post["full_report"] = db_row.get("full_report")
                    post["quant_summary"] = db_row.get("quant_summary")
                    comments = db_row.get("raw_comments") or post.get("comments") or []
                    comments = normalize_like_counts(comments)
                    post["comments"] = comments
                    post["view_count"] = db_row.get("view_count") or post.get("view_count") or post.get("metrics", {}).get("views")
                    post["cluster_summary"] = db_row.get("cluster_summary") or {}
                    job_store.set_job_result(job_id, {"post": post})
            except Exception as e:
                print(f"⚠️ 無法從 DB 補 images/ai_tags/full_report/quant_summary/raw_comments：{e}")
                if post and post.get("comments"):
                    post["comments"] = normalize_like_counts(post["comments"])
        images_len = len(post.get("images") or []) if post else 0
        print(f"[status] job_id={job_id} images={images_len}")
        if post and post.get("comments"):
            post["comments"] = normalize_like_counts(post["comments"])
        ctx["post"] = post
        ctx["chart_html"] = generate_battlefield_chart_html(post.get("comments") or [], post.get("cluster_summary")) if post else "<div>No Data</div>"
    else:
        ctx["posts"] = job.get("posts", [])
        ctx["post"] = None
        ctx["chart_html"] = "<div></div>"
    return templates.TemplateResponse("status.html", ctx)


@app.get("/proxy_image")
def proxy_image(url: str):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, stream=True, timeout=5)
        if resp.status_code != 200:
            return Response(status_code=404)
        content_type = resp.headers.get("Content-Type", "image/jpeg")
        return StreamingResponse(resp.iter_content(chunk_size=8192), media_type=content_type)
    except Exception:
        return Response(status_code=404)
