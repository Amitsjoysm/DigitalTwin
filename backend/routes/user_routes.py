from fastapi import APIRouter, Depends, HTTPException, status
from models.user import User, UserResponse
from routes.auth_routes import get_current_user
from repositories.user_repository import UserRepository
from server import db
from typing import Dict

router = APIRouter()
user_repo = UserRepository(db)

@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get user profile"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        avatar_id=current_user.avatar_id,
        onboarding_completed=current_user.onboarding_completed,
        personality=current_user.personality,
        preferences=current_user.preferences
    )

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    update_data: Dict,
    current_user: User = Depends(get_current_user)
):
    """Update user profile"""
    # Filter allowed fields
    allowed_fields = ['name', 'personality', 'preferences', 'onboarding_completed']
    filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}
    
    if not filtered_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    # Update user
    await user_repo.update(current_user.id, filtered_data)
    
    # Fetch updated user
    updated_user = await user_repo.find_by_id(current_user.id)
    
    return UserResponse(
        id=updated_user.id,
        email=updated_user.email,
        name=updated_user.name,
        avatar_id=updated_user.avatar_id,
        onboarding_completed=updated_user.onboarding_completed,
        personality=updated_user.personality,
        preferences=updated_user.preferences
    )