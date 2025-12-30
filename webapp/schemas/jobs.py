from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any, Dict, List
from datetime import datetime
from uuid import UUID

class JobCreate(BaseModel):
    pipeline_type: str = Field(..., description="Pipeline type: 'B', 'C', etc.")
    mode: str = Field(default="ingest", description="'ingest', 'analyze', 'full'")
    input_config: Dict[str, Any] = Field(..., description="Config (e.g. {'keyword': 'foo'})")

class JobItemPreview(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    target_id: str
    status: str
    stage: str
    result_post_id: Optional[str] = None
    error_log: Optional[str] = None
    updated_at: datetime

class JobStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    status: str
    pipeline_type: str
    mode: str
    # Metrics
    total_count: int
    processed_count: int
    success_count: int
    failed_count: int
    # Timestamps
    created_at: datetime
    updated_at: datetime
    finished_at: Optional[datetime] = None
    # Meta
    input_config: Dict[str, Any]
    error_summary: Optional[str] = None
    # Forensics (Optional for list view, populated for detail view)
    items: Optional[List[JobItemPreview]] = []
