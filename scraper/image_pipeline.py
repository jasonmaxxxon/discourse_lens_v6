import os
import pathlib
from typing import Any, Dict, List

# Link-only mode: no download, no OCR. Env flags default to off.
_OCR_ENV = os.environ.get("DLENS_ENABLE_OCR", "").strip().lower()
_DL_ENV = os.environ.get("DLENS_DOWNLOAD_IMAGES", "").strip().lower()
OCR_ENABLED = _OCR_ENV in {"1", "true", "yes", "on"} and False  # force disabled by default
DOWNLOAD_ENABLED = _DL_ENV in {"1", "true", "yes", "on"} and False

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
IMAGES_DIR = ROOT_DIR / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def process_images_for_post(
    post_id: str,
    images: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Link-only mode: do not download or OCR. Pass through URLs for proxying.
    """
    processed: List[Dict[str, Any]] = []
    for idx, img in enumerate(images, start=1):
        src = img.get("src") or img.get("original_src") or ""
        original_src = img.get("original_src") or src
        enriched: Dict[str, Any] = {
            "image_id": f"img{idx}",
            "src": src,
            "original_src": original_src,
            "alt": img.get("alt") or "",
            "proxy_url": "",
            "local_path": "",
            "scene_label": None,
            "full_text": None,
            "has_contextual_text": None,
            "text_blocks": [],
            "filters_applied": [],
            "low_confidence_regions": [],
            "ocr_error": "",
        }
        if "cdn_url" in img:
            enriched["cdn_url"] = img.get("cdn_url")
        if "proxy_url" in img:
            enriched["proxy_url"] = img.get("proxy_url") or enriched["proxy_url"]
        processed.append(enriched)
    print("OCR disabled, link-only images passthrough")
    return processed
