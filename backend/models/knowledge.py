from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone
import uuid

class KnowledgeEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    source: str  # upload, url, conversation, manual
    title: str
    content: str
    embedding_id: Optional[str] = None
    file_path: Optional[str] = None
    tags: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class KnowledgeCreate(BaseModel):
    source: str
    title: str
    content: str
    tags: List[str] = []

class KnowledgeResponse(BaseModel):
    id: str
    user_id: str
    source: str
    title: str
    tags: List[str]
    created_at: datetime