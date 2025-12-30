import logging
import os
from typing import List

import google.generativeai as genai
from dotenv import load_dotenv

logger = logging.getLogger("Embeddings")

load_dotenv()

EMBED_MODEL = "models/text-embedding-004"
EMBED_DIM = 768


def embed_text(text: str) -> List[float]:
    """
    Return a 768-d embedding using Google Generative AI.
    Hard-fails on missing key or dimension mismatch.
    """
    if not text:
        raise ValueError("embed_text: empty text provided")

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("embed_text: missing GEMINI_API_KEY/GOOGLE_API_KEY")

    genai.configure(api_key=api_key)
    try:
        res = genai.embed_content(
            model=EMBED_MODEL,
            content=text,
        )
        vec = res.get("embedding") if isinstance(res, dict) else getattr(res, "embedding", None)
        if vec is None:
            raise ValueError("embed_text: embedding missing in response")
        if len(vec) != EMBED_DIM:
            raise ValueError(f"embed_text: dimension mismatch expected {EMBED_DIM} got {len(vec)}")
        logger.info(f"[Embeddings] model={EMBED_MODEL} dim={len(vec)} sample={vec[:5]}")
        return [float(x) for x in vec]
    except Exception as e:
        logger.error(f"embed_text failed: {e}")
        raise


def embedding_hash(vec: List[float]) -> str:
    import hashlib

    m = hashlib.sha256()
    for v in vec:
        m.update(f"{v:.6f}".encode("utf-8"))
    return m.hexdigest()
