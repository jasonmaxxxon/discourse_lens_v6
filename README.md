# DiscourseLens V6 — The Social Intelligence Radar

> **Status:** V6 (Foundation Phase)
> **Checkpoint:** `checkpoint/2025-12-30`
> **Architecture:** Industrial-Grade / SoT-Driven

DiscourseLens 是一個將社群雜訊轉化為結構化資產的 **「社會情報雷達 (Social Intelligence Radar)」**。
不同於傳統輿情工具僅停留在關鍵字或情緒分析，本系統基於 **「敘事物理學 (Narrative Physics)」**，利用 LLM (Gemini 2.5) 與確定性演算法 (Quant Engine) 解構話語背後的戰略意圖與傳播結構。

---

## 🏗 System Architecture (系統架構)

本系統採用 **FastAPI + React + Supabase** 的現代化分離架構，並嚴格遵循「單一真值來源 (Source of Truth, SoT)」原則。

### 1. The Core (Backend)
- **Framework:** FastAPI (`webapp/app.py`)
- **Job Engine:** Supabase-backed JobManager (`job_batches` / `job_items`).
  - *Note:* In-memory job stores are **DEPRECATED**.
- **Analyst Layer:** Fuses crawler data (Physics) with LLM interpretations (Semantics).
- **Vision:** Two-Stage Pipeline (VisionGate -> Classification -> OCR/Extraction).

### 2. The Interface (Frontend)
- **Framework:** Vite + React + Tailwind (`dlcs-ui/`).
- **Primary Console:** `/pipeline/a` (Single Page Monitor).
- **Narrative View:** `/narrative/:postId` (Deep Analysis Report).

### 3. Data Governance (SoT Rules)
| Data Entity | Source of Truth (SoT) | Description |
| :--- | :--- | :--- |
| **Jobs** | `public.job_batches` | 進度追蹤的唯一依據。UI 透過 Polling 此表更新。 |
| **Comments** | `public.threads_comments` | 留言搜尋、聚類與分析的實體層。 |
| **Analysis** | `threads_posts.analysis_json` | 必須經由 `build_and_validate_analysis_json` 驗證寫入。 |
| **Vision** | `threads_posts.vision_*` | 圖片元數據與 OCR 結果。 |

---

## 🚀 Pipelines

系統核心由三條管線驅動 (`pipelines/core.py`)：

* **Pipeline A (Deep Probe):** 單一貼文深度掃描。包含 VisionGate 圖片分析、留言採樣、戰術識別 (L2) 與敘事解讀 (L3)。
* **Pipeline B (Keyword Radar):** 關鍵字批量監控。支援 `ingest` (僅入庫) 與 `analyze` (全量分析) 模式。
* **Pipeline C (Profile Matrix):** 特定帳號時間軸監控。

---

## 🛠 Installation & Setup

### Prerequisites
* Python 3.10+
* Node.js 18+
* Supabase Project (PostgreSQL + Vector)

### 1. Backend Setup
```bash
# 1. 建立虛擬環境
python3 -m venv .venv
source .venv/bin/activate

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 配置環境變數
cp .env.example .env
# 編輯 .env 填入 SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY

# 4. 配置 Threads 憑證
# 將您的 cookie JSON 放入 auth_threads.json (請勿提交此檔案!)
