from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, conint, confloat, validator


class Metrics(BaseModel):
    likes: conint(ge=0) = 0
    views: Optional[conint(ge=0)] = None
    replies: Optional[conint(ge=0)] = None


class ToneProfile(BaseModel):
    primary: Optional[str] = None
    cynicism: Optional[confloat(ge=0, le=1)] = None
    hope: Optional[confloat(ge=0, le=1)] = None
    outrage: Optional[confloat(ge=0, le=1)] = None
    notes: Optional[str] = None


class SegmentSample(BaseModel):
    comment_id: Optional[str] = None
    user: Optional[str] = None
    text: str = ""
    likes: Optional[int] = None


class Segment(BaseModel):
    label: str
    share: Optional[confloat(ge=0, le=1)] = None
    samples: List[SegmentSample] = Field(default_factory=list)
    linguistic_features: List[str] = Field(default_factory=list)


class NarrativeStack(BaseModel):
    l1: Optional[str] = None
    l2: Optional[str] = None
    l3: Optional[str] = None


class Phenomenon(BaseModel):
    id: Optional[str] = None
    status: Optional[str] = None  # pending | matched | minted | failed
    name: Optional[str] = None
    description: Optional[str] = None
    ai_image: Optional[str] = None


class DangerBlock(BaseModel):
    bot_homogeneity_score: Optional[confloat(ge=0, le=1)] = None
    notes: Optional[str] = None


class PostBlock(BaseModel):
    post_id: str
    author: Optional[str] = None
    text: Optional[str] = None
    link: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    timestamp: Optional[datetime] = None
    metrics: Metrics

    @validator("timestamp", pre=True)
    def _parse_ts(cls, v):
        if v is None or isinstance(v, datetime):
            return v
        try:
            return datetime.fromisoformat(str(v))
        except Exception:
            return None


class SummaryCompat(BaseModel):
    one_line: Optional[str] = None
    narrative_type: Optional[str] = None


class BattlefieldCompat(BaseModel):
    factions: List[Segment] = Field(default_factory=list)


class AnalysisV4(BaseModel):
    post: PostBlock
    phenomenon: Phenomenon
    emotional_pulse: ToneProfile
    segments: List[Segment] = Field(default_factory=list)
    narrative_stack: NarrativeStack
    danger: Optional[DangerBlock] = None
    full_report: Optional[str] = None
    # Compatibility fields for existing UI adapters
    summary: Optional[SummaryCompat] = None
    battlefield: Optional[BattlefieldCompat] = None

    class Config:
        extra = "ignore"
