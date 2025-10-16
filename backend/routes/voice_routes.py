from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from models.user import User
from routes.auth_routes import get_current_user
from repositories.user_repository import UserRepository
from services.tts_service import tts_service
from services.storage_service import storage_service
from server import db
import os
import uuid
from pathlib import Path
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
user_repo = UserRepository(db)

UPLOAD_DIR = Path(os.environ.get('UPLOAD_DIR', '/app/backend/uploads'))
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)

@router.post("/upload")
async def upload_voice_sample(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload voice sample and clone voice with Newport AI
    Returns task_id for polling
    """
    # Validate file type
    if not file.content_type.startswith('audio/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an audio file"
        )
    
    # Save file locally first
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'webm'
    file_name = f"{uuid.uuid4()}.{file_extension}"
    file_path = UPLOAD_DIR / file_name
    
    try:
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Voice file saved locally: {file_path}")
        
        # Create public URL for the voice file
        voice_url = f"https://component-review-2.preview.emergentagent.com/uploads/{file_name}"
        logger.info(f"Voice URL: {voice_url}")
        
        # Clone voice with Newport AI
        clone_result = await tts_service.clone_voice(voice_url)
        
        if not clone_result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Voice clone failed: {clone_result.get('error')}"
            )
        
        task_id = clone_result['task_id']
        logger.info(f"Voice clone task started: {task_id}")
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "Voice cloning started. Poll /voices/clone-status/{task_id} for result."
        }
        
    except Exception as e:
        logger.error(f"Voice upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload voice: {str(e)}"
        )

@router.get("/clone-status/{task_id}")
async def get_voice_clone_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Poll voice clone task status
    When completed, automatically updates user's voice_id with cloneId
    """
    try:
        result = await tts_service.check_voice_clone_status(task_id)
        
        # If completed, update user's voice_id
        if result['status'] == 'completed' and result.get('clone_id'):
            clone_id = result['clone_id']
            await user_repo.update(current_user.id, {"voice_id": clone_id})
            logger.info(f"User {current_user.id} voice cloned: {clone_id}")
            
            return {
                "status": "completed",
                "clone_id": clone_id,
                "message": "Voice cloned successfully! Your digital self will now use your voice."
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Voice clone status error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check status: {str(e)}"
        )

@router.get("/my-voice")
async def get_my_voice(current_user: User = Depends(get_current_user)):
    """Get user's cloned voice ID"""
    if not current_user.voice_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No cloned voice found. Please upload a voice sample first."
        )
    
    return {
        "voice_id": current_user.voice_id,
        "message": "Voice clone ready"
    }
