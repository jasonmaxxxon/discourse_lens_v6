"""App configuration loader (env only, no side-effects).
This mirrors existing env usage without altering defaults.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Expose commonly used settings; callers still free to read os.environ
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
VISION_MODE = os.environ.get("VISION_MODE")
VISION_STAGE_CAP = os.environ.get("VISION_STAGE_CAP")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

__all__ = [
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "VISION_MODE",
    "VISION_STAGE_CAP",
    "GEMINI_API_KEY",
]
