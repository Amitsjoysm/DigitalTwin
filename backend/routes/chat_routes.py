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
    """Send a message and get AI response with video"""
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
    
    # Generate video with Newport AI
    video_task_id = None
    if current_user.avatar_id:
        try:
            # Get avatar data
            avatar = await avatar_repo.find_by_id(current_user.avatar_id)
            if avatar and avatar.image_url:
                # Step 1: Convert text to speech (use cloned voice if available)
                logger.info(f"Generating TTS for message: {response_text[:50]}...")
                
                if current_user.voice_id:
                    # Use cloned voice
                    logger.info(f"Using cloned voice: {current_user.voice_id}")
                    tts_result = await tts_service.text_to_speech_with_clone(
                        text=response_text,
                        clone_id=current_user.voice_id
                    )
                else:
                    # Use default voice
                    logger.info("Using default voice (no clone available)")
                    tts_result = await tts_service.text_to_speech(response_text)
                
                if tts_result.get('success'):
                    tts_task_id = tts_result['task_id']
                    
                    # Poll for TTS completion (max 30 seconds)
                    audio_url = None
                    for _ in range(30):
                        await asyncio.sleep(1)
                        tts_status = await tts_service.check_tts_status(tts_task_id)
                        if tts_status['status'] == 'completed':
                            audio_url = tts_status['audio_url']
                            break
                        elif tts_status['status'] == 'failed':
                            logger.error(f"TTS failed: {tts_status.get('error')}")
                            break
                    
                    if audio_url:
                        # Step 2: Generate video with DreamAvatar
                        logger.info("Generating video with DreamAvatar...")
                        video_result = await video_service.generate_video_from_image(
                            image_url=avatar.image_url,
                            audio_url=audio_url,
                            prompt=f"{current_user.name} talking naturally"
                        )
                        
                        if video_result.get('success'):
                            video_task_id = video_result['task_id']
                            logger.info(f"Video generation task created: {video_task_id}")
                        else:
                            logger.error(f"Video generation failed: {video_result.get('error')}")
                    else:
                        logger.error("TTS did not complete in time")
                else:
                    logger.error(f"TTS failed: {tts_result.get('error')}")
            else:
                logger.warning(f"No avatar image found for user {current_user.id}")
        except Exception as e:
            logger.error(f"Error generating video: {str(e)}")
    
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
        "video_task_id": video_task_id,
        "knowledge_used": len(knowledge_results) > 0
    }

@router.get("/video-status/{task_id}")
async def get_video_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get video generation status from Newport AI"""
    result = await video_service.check_task_status(task_id)
    return result