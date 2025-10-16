from fastapi import APIRouter, Depends, HTTPException, status
from models.user import User
from models.conversation import Conversation, ConversationCreate, ConversationResponse, Message
from routes.auth_routes import get_current_user
from repositories.conversation_repository import ConversationRepository
from server import db
from typing import List

router = APIRouter()
conversation_repo = ConversationRepository(db)

@router.post("/", response_model=ConversationResponse)
async def create_conversation(
    conv_data: ConversationCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new conversation"""
    conversation = Conversation(
        user_id=current_user.id,
        title=conv_data.title
    )
    
    await conversation_repo.create(conversation)
    
    return ConversationResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        message_count=conversation.message_count,
        started_at=conversation.started_at,
        last_message_at=conversation.last_message_at,
        tags=conversation.tags
    )

@router.get("/", response_model=List[ConversationResponse])
async def get_conversations(
    current_user: User = Depends(get_current_user),
    limit: int = 50
):
    """Get user's conversations"""
    conversations = await conversation_repo.find_by_user(current_user.id, limit)
    
    return [
        ConversationResponse(
            id=conv.id,
            user_id=conv.user_id,
            title=conv.title,
            message_count=conv.message_count,
            started_at=conv.started_at,
            last_message_at=conv.last_message_at,
            tags=conv.tags
        )
        for conv in conversations
    ]

@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get conversation details"""
    conversation = await conversation_repo.find_by_id(conversation_id)
    
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return conversation

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a conversation"""
    conversation = await conversation_repo.find_by_id(conversation_id)
    
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    await conversation_repo.delete(conversation_id)
    
    return {"message": "Conversation deleted successfully"}