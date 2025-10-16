from fastapi import APIRouter, Depends, HTTPException, status
from models.user import User
from models.conversation import MessageCreate, Message
from routes.auth_routes import get_current_user
from repositories.conversation_repository import ConversationRepository
from repositories.user_repository import UserRepository
from repositories.avatar_repository import AvatarRepository
from services.llm_service import llm_service
from services.knowledge_service import knowledge_service
from services.video_service import video_service
from services.tts_service import tts_service
from services.cache_service import cache_service
from server import db
import time
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()
conversation_repo = ConversationRepository(db)
user_repo = UserRepository(db)
avatar_repo = AvatarRepository(db)

@router.post("/send")
async def send_message(
    conversation_id: str,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user)
):
    """Send a message and get response"""
    start_time = time.time()
    
    # Get conversation
    conversation = await conversation_repo.find_by_id(conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Create user message
    user_message = Message(
        role="user",
        content=message_data.content
    )
    await conversation_repo.add_message(conversation_id, user_message)
    
    # Search knowledge base for relevant context
    knowledge_results = await knowledge_service.search_knowledge(
        current_user.id,
        message_data.content,
        top_k=3
    )
    
    rag_context = "\n".join([r["content"] for r in knowledge_results]) if knowledge_results else ""
    
    # Generate personality prompt
    user_data = {
        "name": current_user.name,
        "personality": current_user.personality.model_dump()
    }
    personality_prompt = llm_service.generate_personality_prompt(user_data)
    
    if rag_context:
        personality_prompt += f"\n\nRelevant context from your knowledge base:\n{rag_context}"
    
    # Get recent messages for context
    recent_messages = conversation.messages[-10:] if len(conversation.messages) > 0 else []
    message_history = [
        {"role": msg.role, "content": msg.content}
        for msg in recent_messages
    ]
    message_history.append({"role": "user", "content": message_data.content})
    
    # Generate LLM response
    response_text = await llm_service.generate_response(
        message_history,
        personality_prompt
    )
    
    # Generate video (background job)
    video_job = None
    if current_user.avatar_id:
        video_job = await video_service.generate_video(
            current_user.avatar_id,
            response_text,
            emotion="neutral"
        )
    
    # Create assistant message
    response_time_ms = int((time.time() - start_time) * 1000)
    assistant_message = Message(
        role="assistant",
        content=response_text,
        response_time_ms=response_time_ms
    )
    await conversation_repo.add_message(conversation_id, assistant_message)
    
    return {
        "message": assistant_message,
        "video_job_id": video_job["job_id"] if video_job else None,
        "knowledge_used": len(knowledge_results) > 0
    }

@router.get("/video-status/{job_id}")
async def get_video_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get video generation status"""
    result = await video_service.check_job_status(job_id)
    return result