from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, Dict, List
from datetime import datetime, timezone
import uuid

class PersonalityTraits(BaseModel):
    formality: int = Field(default=5, ge=1, le=10)
    enthusiasm: int = Field(default=5, ge=1, le=10)
    verbosity: int = Field(default=5, ge=1, le=10)
    humor: int = Field(default=5, ge=1, le=10)
    traits: List[str] = []

class UserPreferences(BaseModel):
    voice_speed: float = Field(default=1.0, ge=0.5, le=2.0)
    video_quality: str = Field(default="720p")
    context_window: int = Field(default=20)

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    hashed_password: str
    avatar_id: Optional[str] = None
    voice_id: Optional[str] = None
    personality: PersonalityTraits = Field(default_factory=PersonalityTraits)
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    onboarding_completed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    avatar_id: Optional[str] = None
    onboarding_completed: bool
    personality: PersonalityTraits
    preferences: UserPreferences