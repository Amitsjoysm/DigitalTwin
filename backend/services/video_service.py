import aiohttp
import os
from typing import Optional
from rq import Queue
from redis import Redis

class VideoService:
    """Service for Newport AI video generation (Single Responsibility)"""
    
    def __init__(self):
        self.api_key = os.environ.get('NEWPORT_API_KEY')
        self.base_url = "https://api.newportai.com"
        self.redis = Redis(
            host=os.environ.get('REDIS_HOST', 'localhost'),
            port=int(os.environ.get('REDIS_PORT', 6379)),
            db=0
        )
        self.queue = Queue('video_generation', connection=self.redis)
    
    async def train_avatar(self, video_path: str, user_id: str) -> dict:
        """Train avatar with Newport AI - background job"""
        # This would be enqueued as a background job
        job = self.queue.enqueue(
            'workers.video_worker.train_avatar_job',
            video_path,
            user_id,
            self.api_key
        )
        return {"job_id": job.id, "status": "queued"}
    
    async def generate_video(
        self,
        avatar_id: str,
        text: str,
        audio_url: Optional[str] = None,
        emotion: str = "neutral"
    ) -> dict:
        """Generate video with avatar speaking - background job"""
        job = self.queue.enqueue(
            'workers.video_worker.generate_video_job',
            avatar_id,
            text,
            audio_url,
            emotion,
            self.api_key
        )
        return {"job_id": job.id, "status": "queued"}
    
    async def check_job_status(self, job_id: str) -> dict:
        """Check status of background job"""
        from rq.job import Job
        try:
            job = Job.fetch(job_id, connection=self.redis)
            return {
                "job_id": job_id,
                "status": job.get_status(),
                "result": job.result if job.is_finished else None,
                "error": str(job.exc_info) if job.is_failed else None
            }
        except Exception as e:
            return {"job_id": job_id, "status": "not_found", "error": str(e)}

video_service = VideoService()