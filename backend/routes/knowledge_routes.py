from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from models.user import User
from models.knowledge import KnowledgeEntry, KnowledgeCreate, KnowledgeResponse
from routes.auth_routes import get_current_user
from repositories.knowledge_repository import KnowledgeRepository
from services.knowledge_service import knowledge_service
from server import db
from typing import List
import PyPDF2
import os
from pathlib import Path

router = APIRouter()
knowledge_repo = KnowledgeRepository(db)

UPLOAD_DIR = Path(os.environ.get('UPLOAD_DIR', '/app/backend/uploads'))
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)

@router.post("/", response_model=KnowledgeResponse)
async def create_knowledge(
    knowledge_data: KnowledgeCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new knowledge entry"""
    knowledge = KnowledgeEntry(
        user_id=current_user.id,
        source=knowledge_data.source,
        title=knowledge_data.title,
        content=knowledge_data.content,
        tags=knowledge_data.tags
    )
    
    # Add to vector database
    embedding_id = await knowledge_service.add_knowledge(
        current_user.id,
        knowledge_data.content,
        {"title": knowledge_data.title, "source": knowledge_data.source}
    )
    
    knowledge.embedding_id = embedding_id
    await knowledge_repo.create(knowledge)
    
    return KnowledgeResponse(
        id=knowledge.id,
        user_id=knowledge.user_id,
        source=knowledge.source,
        title=knowledge.title,
        tags=knowledge.tags,
        created_at=knowledge.created_at
    )

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload and process document"""
    # Read file content
    content = await file.read()
    
    # Extract text based on file type
    if file.filename.endswith('.pdf'):
        import io
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
    elif file.filename.endswith('.txt'):
        text = content.decode('utf-8')
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type"
        )
    
    # Create knowledge entry
    knowledge = KnowledgeEntry(
        user_id=current_user.id,
        source="upload",
        title=file.filename,
        content=text,
        tags=[]
    )
    
    # Add to vector database
    embedding_id = await knowledge_service.add_knowledge(
        current_user.id,
        text,
        {"title": file.filename, "source": "upload"}
    )
    
    knowledge.embedding_id = embedding_id
    await knowledge_repo.create(knowledge)
    
    return KnowledgeResponse(
        id=knowledge.id,
        user_id=knowledge.user_id,
        source=knowledge.source,
        title=knowledge.title,
        tags=knowledge.tags,
        created_at=knowledge.created_at
    )

@router.get("/", response_model=List[KnowledgeResponse])
async def get_knowledge(
    current_user: User = Depends(get_current_user),
    limit: int = 100
):
    """Get user's knowledge entries"""
    entries = await knowledge_repo.find_by_user(current_user.id, limit)
    
    return [
        KnowledgeResponse(
            id=entry.id,
            user_id=entry.user_id,
            source=entry.source,
            title=entry.title,
            tags=entry.tags,
            created_at=entry.created_at
        )
        for entry in entries
    ]

@router.delete("/{knowledge_id}")
async def delete_knowledge(
    knowledge_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a knowledge entry"""
    knowledge = await knowledge_repo.find_by_id(knowledge_id)
    
    if not knowledge or knowledge.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge not found"
        )
    
    # Delete from vector database
    if knowledge.embedding_id:
        await knowledge_service.delete_knowledge(current_user.id, knowledge.embedding_id)
    
    # Delete from MongoDB
    await knowledge_repo.delete(knowledge_id)
    
    return {"message": "Knowledge deleted successfully"}