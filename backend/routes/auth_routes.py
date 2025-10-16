from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.user import UserCreate, UserLogin, User, UserResponse
from services.auth_service import auth_service
from repositories.user_repository import UserRepository
from server import db

router = APIRouter()
security = HTTPBearer()
user_repo = UserRepository(db)

@router.post("/register", response_model=dict)
async def register(user_data: UserCreate):
    """Register a new user"""
    # Check if user already exists
    existing_user = await user_repo.find_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = auth_service.hash_password(user_data.password)
    
    # Create user
    user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password
    )
    
    await user_repo.create(user)
    
    # Create access token
    access_token = auth_service.create_access_token({"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            avatar_id=user.avatar_id,
            onboarding_completed=user.onboarding_completed,
            personality=user.personality,
            preferences=user.preferences
        )
    }

@router.post("/login", response_model=dict)
async def login(credentials: UserLogin):
    """Login user"""
    # Find user
    user = await user_repo.find_by_email(credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not auth_service.verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Create access token
    access_token = auth_service.create_access_token({"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            avatar_id=user.avatar_id,
            onboarding_completed=user.onboarding_completed,
            personality=user.personality,
            preferences=user.preferences
        )
    }

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Dependency to get current user from JWT token"""
    token = credentials.credentials
    payload = auth_service.verify_token(token)
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user = await user_repo.find_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        avatar_id=current_user.avatar_id,
        onboarding_completed=current_user.onboarding_completed,
        personality=current_user.personality,
        preferences=current_user.preferences
    )