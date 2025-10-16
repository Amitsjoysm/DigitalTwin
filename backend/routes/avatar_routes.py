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
import cv2
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
avatar_repo = AvatarRepository(db)
user_repo = UserRepository(db)

UPLOAD_DIR = Path(os.environ.get('UPLOAD_DIR', '/app/backend/uploads'))
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)

def extract_frame_from_video(video_path: str, output_path: str) -> bool:
    """Extract a frame from video to use as avatar image"""
    try:
        cap = cv2.VideoCapture(video_path)
        
        # Get total frames
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Extract frame from middle of video
        middle_frame = total_frames // 2
        cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
        
        ret, frame = cap.read()
        if ret:
            cv2.imwrite(output_path, frame)
            cap.release()
            return True
        
        cap.release()
        return False
    except Exception as e:
        logger.error(f"Error extracting frame: {str(e)}")
        return False

@router.post("/upload", response_model=AvatarResponse)
async def upload_avatar_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload avatar training video and extract image for DreamAvatar"""
    # Validate file type
    if not file.content_type.startswith('video/') and not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a video or image"
        )
    
    # Save file
    file_extension = file.filename.split('.')[-1]
    file_name = f"{uuid.uuid4()}.{file_extension}"
    file_path = UPLOAD_DIR / file_name
    
    with open(file_path, 'wb') as f:
        content = await file.read()
        f.write(content)
    
    # Extract image if video
    image_url = None
    if file.content_type.startswith('video/'):
        image_name = f"{uuid.uuid4()}.jpg"
        image_path = UPLOAD_DIR / image_name
        if extract_frame_from_video(str(file_path), str(image_path)):
            # In production, upload to CDN/S3 and get public URL
            # For now, use local path
            image_url = f"/uploads/{image_name}"
            logger.info(f"Extracted frame from video: {image_url}")
    else:
        # If image uploaded directly
        image_url = f"/uploads/{file_name}"
    
    # Create avatar record
    avatar = Avatar(
        user_id=current_user.id,
        video_path=str(file_path) if file.content_type.startswith('video/') else None,
        image_url=image_url,
        training_status="completed"  # No training needed for DreamAvatar
    )
    
    await avatar_repo.create(avatar)
    
    # Update user with avatar_id
    await user_repo.update(current_user.id, {"avatar_id": avatar.id})
    
    return AvatarResponse(
        id=avatar.id,
        user_id=avatar.user_id,
        training_status=avatar.training_status,
        thumbnail_url=avatar.thumbnail_url,
        image_url=avatar.image_url,
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