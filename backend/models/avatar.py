from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, timezone
import uuid

class Avatar(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    video_path: str
    training_status: str = "pending"  # pending, processing, completed, failed
    newport_avatar_id: Optional[str] = None
    thumbnail_url: Optional[str] = None
    training_duration: Optional[float] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AvatarCreate(BaseModel):
    video_path: str

class AvatarResponse(BaseModel):
    id: str
    user_id: str
    training_status: str
    thumbnail_url: Optional[str] = None
    created_at: datetime