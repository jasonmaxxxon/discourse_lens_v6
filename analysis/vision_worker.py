"""
Background vision worker for enriching Threads images via Gemini 2.5 Flash.
- Fetch posts whose images lack scene_label (prioritizing newest).
- Stealth download images to bypass 403 Forbidden.
- Analyze via Gemini 2.5 Flash.
- Write enriched data back to Supabase.
"""

import json
import os
import tempfile
import time
import traceback
import logging
from typing import Any, Dict, List, Optional

import google.generativeai as genai
import requests
from dotenv import load_dotenv
from supabase import Client, create_client

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("VisionWorker")

# Load Environment Variables
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY]):
    logger.error("Missing required environment variables.")
    exit(1)

# Initialize Clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_API_KEY)

# ✅ CONFIGURATION: Use the model confirmed in your list
MODEL_NAME = "gemini-2.5-flash"
RATE_LIMIT_SECONDS = 2.0

SYSTEM_PROMPT = """
You are a research assistant for a Discourse Analysis project.
Analyze this image specifically for social narrative construction.
Return a raw JSON object (no markdown) with these keys:
- `scene_label` (enum): 'meme', 'news_screenshot', 'social_post_screenshot', 'infographic', 'photo', 'selfie', 'food', 'scenery', 'other'.
- `full_text` (str): Verbatim OCR of all visible text.
- `context_desc` (str): A concise, objective description of the image content.
- `visual_rhetoric` (str): Key visual elements used for persuasion (e.g., 'High contrast red text', 'Crying emoji').
"""

def fetch_pending_posts(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch posts whose first image has no scene_label.
    Strategy: Order by created_at DESC to process freshest links first.
    """
    try:
        resp = (
            supabase.table("threads_posts")
            .select("id, images, url, created_at")
            .order("created_at", desc=True)  # Prioritize newest posts
            .limit(50)
            .execute()
        )
        rows = resp.data or []
        pending: List[Dict[str, Any]] = []
        
        for row in rows:
            imgs = row.get("images") or []
            if not imgs:
                continue
            
            # Check the first image to see if analysis is needed
            first = imgs[0] or {}
            label = first.get("scene_label")
            
            # Process if label is None (new)
            # You can also add 'or label == "analysis_failed"' if you want to retry failed ones
            if label is None:
                pending.append(row)
            
            if len(pending) >= limit:
                break
        return pending
    except Exception as e:
        logger.error(f"DB Fetch Error: {e}")
        return []

def download_image_to_temp(url: str) -> Optional[str]:
    """
    Download image with browser-like headers to a temp file to avoid 403.
    Returns temp file path or None on failure.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://www.threads.net/",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
    }
    
    try:
        logger.info(f"⬇️ Downloading: {url[:60]}...")
        resp = requests.get(url, headers=headers, stream=True, timeout=15)
        
        # Check for Soft Block (Meta sending HTML login page)
        ctype = resp.headers.get("Content-Type", "").lower()
        if "text/html" in ctype:
            logger.warning(f"❌ Soft Blocked (Meta sent HTML). URL: {url}")
            return None
            
        if resp.status_code != 200:
            logger.warning(f"❌ HTTP Error {resp.status_code}")
            return None

        # Write to temp file
        fd, temp_path = tempfile.mkstemp(suffix=".jpg")
        with os.fdopen(fd, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return temp_path
    except Exception as e:
        logger.error(f"⚠️ Download Exception: {e}")
        return None

def analyze_image_with_gemini(image_url: str) -> Dict[str, Any]:
    """
    Orchestrates: Download -> Upload to Gemini -> Generate -> Cleanup
    """
    temp_path = download_image_to_temp(image_url)
    if not temp_path:
        return {
            "scene_label": "analysis_failed",
            "error": "download_failed_or_403",
        }

    myfile = None
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        
        logger.info(f"🧠 Sending to Gemini ({MODEL_NAME})...")
        myfile = genai.upload_file(temp_path)
        
        result = model.generate_content(
            [myfile, SYSTEM_PROMPT],
            generation_config={"response_mime_type": "application/json"},
        )
        
        text = result.text or "{}"
        parsed = json.loads(text)
        
        return {
            "scene_label": parsed.get("scene_label") or "other",
            "full_text": parsed.get("full_text") or "",
            "context_desc": parsed.get("context_desc") or "",
            "visual_rhetoric": parsed.get("visual_rhetoric") or "",
        }

    except Exception as e:
        logger.error(f"🔥 Gemini Error: {e}")
        # traceback.print_exc() # Uncomment for deep debugging
        return {
            "scene_label": "analysis_failed",
            "error": str(e),
        }
    finally:
        # Cleanup Cloud
        if myfile:
            try:
                myfile.delete()
            except Exception:
                pass
        # Cleanup Local
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass

def process_queue():
    logger.info("🔍 Checking for pending posts...")
    posts = fetch_pending_posts(limit=10)
    
    if not posts:
        logger.info("💤 No pending posts found.")
        return

    logger.info(f"🚀 Found {len(posts)} posts to analyze.")

    for post in posts:
        post_id = post.get("id")
        images = post.get("images") or []
        updated_images: List[Dict[str, Any]] = []
        any_change = False

        logger.info(f"Processing Post {post_id} ({len(images)} images)...")

        for img in images:
            # Skip if already analyzed (and not failed)
            current_label = img.get("scene_label")
            if current_label and current_label != "analysis_failed":
                updated_images.append(img)
                continue

            # ✅ URL Priority: cdn_url > original_src > src
            src = img.get("cdn_url") or img.get("original_src") or img.get("src")
            
            # Safety check: ignore local paths or empty strings
            if not src or not src.startswith("http"):
                logger.warning("   ⚠️ No valid remote URL found for image.")
                enriched = img.copy()
                enriched["scene_label"] = "analysis_failed"
                enriched["error"] = "missing_remote_url"
                updated_images.append(enriched)
                any_change = True
                continue

            # Analyze
            gem_res = analyze_image_with_gemini(src)
            
            enriched = img.copy()
            enriched.update(gem_res)
            updated_images.append(enriched)
            any_change = True
            
            logger.info(f"   ✅ Analyzed: {enriched.get('scene_label')}")
            
            # Rate Limit Protection
            time.sleep(RATE_LIMIT_SECONDS)

        if any_change:
            try:
                supabase.table("threads_posts").update({"images": updated_images}).eq("id", post_id).execute()
                logger.info(f"💾 [Saved] Post {post_id} updated successfully.")
            except Exception as e:
                logger.error(f"❌ Failed to update DB for {post_id}: {e}")
        else:
            logger.info(f"   No changes for Post {post_id}.")

if __name__ == "__main__":
    process_queue()