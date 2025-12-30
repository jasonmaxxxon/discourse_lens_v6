from typing import Dict, List, Optional
import sys
import time
import logging

import cv2
import numpy as np
from paddleocr import PaddleOCR

logger = logging.getLogger(__name__)

_ocr: Optional[PaddleOCR] = None


def get_ocr() -> PaddleOCR:
    """
    Lazy singleton PaddleOCR loader.
    Design principle (Image Layer v2, Step 1):
    - Only download + OCR + structure bbox/confidence.
    - Leave semantics (scene_label/relevance/etc.) to downstream steps.
    """
    global _ocr
    if _ocr is None:
        _ocr = PaddleOCR(use_angle_cls=True, lang="ch")
    return _ocr


def _prepare_image(path: str) -> Optional[np.ndarray]:
    img = cv2.imread(path)
    if img is None:
        return None
    h, w = img.shape[:2]
    min_edge = min(h, w)
    # Upscale small images to help OCR on compressed screenshots.
    if min_edge < 600 and min_edge > 0:
        scale = 600 / min_edge
        new_w, new_h = int(w * scale), int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    # Convert to RGB for PaddleOCR
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def _call_ocr_with_fallback(ocr: PaddleOCR, img: np.ndarray):
    """
    Try cls=True first; if PaddleOCR version rejects cls, retry without it.
    """
    try:
        return ocr.ocr(img, cls=True)
    except TypeError as te:
        msg = str(te)
        if "unexpected keyword argument 'cls'" in msg or "got an unexpected keyword argument 'cls'" in msg:
            return ocr.ocr(img)
        raise


def run_ocr(image_path: str) -> Dict[str, object]:
    """
    Run OCR on a local image path and return standardized blocks:
    - text_blocks: [{"text", "bbox": {x,y,w,h}, "ocr_confidence", "relevance":"unknown"}]
    - full_text: concatenated text
    - error: string if OCR failed
    Never raises; errors are reported via the "error" field.
    """
    ocr = get_ocr()
    img = _prepare_image(image_path)
    if img is None:
        return {"text_blocks": [], "full_text": "", "error": "image_load_failed", "has_contextual_text": False}

    def parse_result(result) -> Dict[str, object]:
        if not result:
            return {"text_blocks": [], "full_text": "", "has_contextual_text": False}

        # Preview first item for debugging without spamming logs
        try:
            logger.debug("OCR raw result preview: %r", result[:1])
        except Exception:
            pass

        text_blocks: List[Dict[str, object]] = []
        lines: List[str] = []

        try:
            for line in result:
                blocks = line if isinstance(line, list) else [line]
                for item in blocks:
                    try:
                        item_len = len(item)
                        box = text = conf = None
                        if item_len == 2:
                            box = item[0]
                            payload = item[1]
                            if isinstance(payload, (list, tuple)) and len(payload) >= 2:
                                text, conf = payload[0], payload[1]
                        elif item_len == 3:
                            box, text, conf = item[0], item[1], item[2]
                        else:
                            logger.debug("OCR item unexpected length: %s", item_len)
                            continue

                        if box is None or text is None or conf is None:
                            continue

                        xs = [p[0] for p in box]
                        ys = [p[1] for p in box]
                        x_min, y_min = int(min(xs)), int(min(ys))
                        x_max, y_max = int(max(xs)), int(max(ys))
                        w, h = x_max - x_min, y_max - y_min
                        text_blocks.append(
                            {
                                "text": text,
                                "bbox": {"x": x_min, "y": y_min, "w": w, "h": h},
                                "ocr_confidence": float(conf),
                                "relevance": "unknown",
                            }
                        )
                        if text:
                            lines.append(str(text))
                    except Exception as item_err:
                        logger.debug("OCR item parse error: %s", item_err)
                        continue
        except Exception as e:
            return {"text_blocks": [], "full_text": "", "has_contextual_text": False, "error": str(e)}

        full_text = "\n".join(lines).strip()
        return {
            "text_blocks": text_blocks,
            "full_text": full_text,
            "has_contextual_text": bool(text_blocks),
        }

    try:
        result = _call_ocr_with_fallback(ocr, img)
        parsed = parse_result(result)
        blocks = parsed.get("text_blocks", [])
        avg_conf = (
            sum(b.get("ocr_confidence", 0.0) for b in blocks) / len(blocks)
            if blocks
            else 0.0
        )
        if blocks and avg_conf < 0.3:
            # Fallback: retry without angle classification
            result2 = ocr.ocr(img)
            parsed = parse_result(result2)
        return parsed
    except Exception as e:
        return {
            "text_blocks": [],
            "full_text": "",
            "has_contextual_text": False,
            "error": str(e),
        }


def smoke_test(image_path: str) -> None:
    """
    Manual smoke test: run OCR on a single image and log summary.
    """
    start = time.perf_counter()
    res = run_ocr(image_path)
    elapsed = time.perf_counter() - start
    text = res.get("full_text", "")
    blocks = res.get("text_blocks", []) or []
    err = res.get("error")
    preview_lines = []
    for b in blocks[:3]:
        preview_lines.append(str(b.get("text", ""))[:80].replace("\n", " "))
    preview = " | ".join(preview_lines)
    print(f"[SMOKE] blocks={len(blocks)} preview='{preview}' error={err} time={elapsed:.2f}s")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m ocr.engine <image_path>")
        sys.exit(1)
    smoke_test(sys.argv[1])
