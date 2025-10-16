from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from redis import Redis
from rq import Queue

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Redis connection for caching and job queue
redis_client = Redis(
    host=os.environ.get('REDIS_HOST', 'localhost'),
    port=int(os.environ.get('REDIS_PORT', 6379)),
    db=0,
    decode_responses=True
)

# RQ Queue for background jobs
job_queue = Queue('digital_self', connection=redis_client)

# Create the main app
app = FastAPI(title="Digital Self Platform API")
api_router = APIRouter(prefix="/api")

# Mount uploads directory for serving files
UPLOAD_DIR = Path(os.environ.get('UPLOAD_DIR', '/app/backend/uploads'))
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)

# Custom file serving with proper MIME types
from fastapi.responses import FileResponse
import mimetypes

@app.get("/uploads/{filename}")
async def serve_uploaded_file(filename: str):
    """Serve uploaded files with correct MIME types"""
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Get MIME type
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if not mime_type:
        # Default MIME types for common file extensions
        if filename.lower().endswith('.wav'):
            mime_type = 'audio/wav'
        elif filename.lower().endswith('.webm'):
            mime_type = 'audio/webm'
        elif filename.lower().endswith('.mp3'):
            mime_type = 'audio/mpeg'
        elif filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
            mime_type = 'image/jpeg'
        elif filename.lower().endswith('.png'):
            mime_type = 'image/png'
        else:
            mime_type = 'application/octet-stream'
    
    return FileResponse(
        path=str(file_path),
        media_type=mime_type,
        filename=filename
    )

# Import and register route modules
from routes.auth_routes import router as auth_router
from routes.user_routes import router as user_router
from routes.avatar_routes import router as avatar_router
from routes.voice_routes import router as voice_router
from routes.conversation_routes import router as conversation_router
from routes.knowledge_routes import router as knowledge_router
from routes.chat_routes import router as chat_router

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(user_router, prefix="/users", tags=["Users"])
api_router.include_router(avatar_router, prefix="/avatars", tags=["Avatars"])
api_router.include_router(voice_router, prefix="/voices", tags=["Voice Cloning"])
api_router.include_router(conversation_router, prefix="/conversations", tags=["Conversations"])
api_router.include_router(knowledge_router, prefix="/knowledge", tags=["Knowledge Base"])
api_router.include_router(chat_router, prefix="/chat", tags=["Chat"])

@api_router.get("/")
async def root():
    return {"message": "Digital Self Platform API", "version": "1.0.0"}

@api_router.get("/health")
async def health_check():
    try:
        # Check MongoDB
        await db.command("ping")
        # Check Redis
        redis_client.ping()
        return {
            "status": "healthy",
            "mongodb": "connected",
            "redis": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown():
    client.close()
    redis_client.close()