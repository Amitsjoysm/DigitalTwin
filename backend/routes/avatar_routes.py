from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from models.user import User
from models.avatar import Avatar, AvatarCreate, AvatarResponse
from routes.auth_routes import get_current_user
from repositories.avatar_repository import AvatarRepository
from repositories.user_repository import UserRepository
from services.video_service import video_service
from server import db
import os
import uuid
from pathlib import Path

router = APIRouter()
avatar_repo = AvatarRepository(db)
user_repo = UserRepository(db)

UPLOAD_DIR = Path(os.environ.get('UPLOAD_DIR', '/app/backend/uploads'))
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)

@router.post("/upload", response_model=AvatarResponse)
async def upload_avatar_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload avatar training video"""
    # Validate file type
    if not file.content_type.startswith('video/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a video"
        )
    
    # Save file
    file_extension = file.filename.split('.')[-1]
    file_name = f"{uuid.uuid4()}.{file_extension}"
    file_path = UPLOAD_DIR / file_name
    
    with open(file_path, 'wb') as f:
        content = await file.read()
        f.write(content)
    
    # Create avatar record
    avatar = Avatar(
        user_id=current_user.id,
        video_path=str(file_path),
        training_status="pending"
    )
    
    await avatar_repo.create(avatar)
    
    # Start training job
    job_result = await video_service.train_avatar(str(file_path), current_user.id)
    
    # Update user with avatar_id
    await user_repo.update(current_user.id, {"avatar_id": avatar.id})
    
    return AvatarResponse(
        id=avatar.id,
        user_id=avatar.user_id,
        training_status=avatar.training_status,
        thumbnail_url=avatar.thumbnail_url,
        created_at=avatar.created_at
    )

@router.get("/status/{avatar_id}", response_model=AvatarResponse)
async def get_avatar_status(
    avatar_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get avatar training status"""
    avatar = await avatar_repo.find_by_id(avatar_id)
    
    if not avatar or avatar.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    
    return AvatarResponse(
        id=avatar.id,
        user_id=avatar.user_id,
        training_status=avatar.training_status,
        thumbnail_url=avatar.thumbnail_url,
        created_at=avatar.created_at
    )

@router.get("/my-avatar", response_model=AvatarResponse)
async def get_my_avatar(current_user: User = Depends(get_current_user)):
    """Get user's avatar"""
    avatar = await avatar_repo.find_by_user(current_user.id)
    
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    
    return AvatarResponse(
        id=avatar.id,
        user_id=avatar.user_id,
        training_status=avatar.training_status,
        thumbnail_url=avatar.thumbnail_url,
        created_at=avatar.created_at
    )