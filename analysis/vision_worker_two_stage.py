import json
import logging
import os
import tempfile
import time
from typing import Any, Dict, List, Optional

import google.generativeai as genai
import requests

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.environ.get("VISION_MODEL_NAME") or "gemini-2.5-flash"
DEFAULT_RATE_LIMIT_SECONDS = float(os.environ.get("VISION_RATE_LIMIT_SECONDS") or 2.0)

V1_PROMPT = """
Analyze this image. Return a STRICT JSON object with no markdown:
{
  "has_text": boolean,
  "is_screenshot": boolean,
  "category": "news_doc" | "social_screenshot" | "meme" | "selfie" | "product" | "scene" | "other",
  "text_density": "none" | "low" | "medium" | "high",
  "notes": "short summary < 12 words"
}
"""

V2_PROMPT = """
Perform full extraction on this image. Return STRICT JSON (no markdown):
{
  "extracted_text": "Full readable text (verbatim)",
  "text_blocks": [{"text": "...", "role": "headline|body|caption|other", "confidence": 0.0}],
  "context_desc": "Objective description (2-3 sentences).",
  "visual_rhetoric": "Key visual persuasion elements (1-2 sentences)."
}
"""


class TwoStageVisionWorker:
    def __init__(
        self,
        *,
        gemini_api_key: str,
        model_name: str = DEFAULT_MODEL,
        rate_limit_seconds: float = DEFAULT_RATE_LIMIT_SECONDS,
    ) -> None:
        self.model_name = model_name
        self.rate_limit_seconds = rate_limit_seconds
        genai.configure(api_key=gemini_api_key)

    def run_v1(self, image_url: str) -> Dict[str, Any]:
        return self._run(image_url=image_url, prompt=V1_PROMPT)

    def run_v2(self, image_url: str) -> Dict[str, Any]:
        return self._run(image_url=image_url, prompt=V2_PROMPT)

    def _run(self, *, image_url: str, prompt: str) -> Dict[str, Any]:
        temp_path = self._download_image_to_temp(image_url)
        if not temp_path:
            return {"error": "download_failed_or_403"}

        myfile = None
        try:
            model = genai.GenerativeModel(self.model_name)
            myfile = genai.upload_file(temp_path)
            result = model.generate_content(
                [myfile, prompt],
                generation_config={"response_mime_type": "application/json"},
            )
            text = result.text or "{}"
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {"error": "non_dict_json"}
        except Exception as e:
            logger.exception(f"[Vision] Gemini failed: {e}")
            return {"error": str(e)}
        finally:
            if myfile:
                try:
                    myfile.delete()
                except Exception:
                    pass
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass
            time.sleep(self.rate_limit_seconds)

    def _download_image_to_temp(self, url: str) -> Optional[str]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": "https://www.threads.net/",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        }
        try:
            resp = requests.get(url, headers=headers, stream=True, timeout=15)
            ctype = (resp.headers.get("Content-Type") or "").lower()
            if "text/html" in ctype:
                logger.warning(f"[Vision] Soft blocked (HTML). url={url}")
                return None
            if resp.status_code != 200:
                logger.warning(f"[Vision] HTTP {resp.status_code}. url={url}")
                return None

            fd, temp_path = tempfile.mkstemp(suffix=".jpg")
            with os.fdopen(fd, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return temp_path
        except Exception as e:
            logger.warning(f"[Vision] download exception: {e}")
            return None
