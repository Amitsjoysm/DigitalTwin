import aiohttp
import os
from typing import Optional
from redis import Redis
import logging
import asyncio

logger = logging.getLogger(__name__)

class VideoService:
    """Service for Newport AI video generation using DreamAvatar 3.0 Fast API"""
    
    def __init__(self):
        self.api_key = os.environ.get('NEWPORT_API_KEY')
        self.base_url = "https://api.newportai.com/api/async"
        self.redis = Redis(
            host=os.environ.get('REDIS_HOST', 'localhost'),
            port=int(os.environ.get('REDIS_PORT', 6379)),
            db=0,
            decode_responses=True
        )
    
    async def generate_video_from_image(
        self,
        image_url: str,
        audio_url: str,
        prompt: str = "a person talking naturally",
        resolution: str = "480p"
    ) -> dict:
        """
        Generate talking video using DreamAvatar 3.0 Fast
        Returns task_id for polling
        """
        url = f"{self.base_url}/dreamavatar/image_to_video/3.0fast"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "audio": audio_url,
            "image": image_url,
            "prompt": prompt,
            "resolution": resolution
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get('code') == 0:
                            task_id = result['data']['taskId']
                            # Store task info in Redis for tracking
                            self.redis.setex(
                                f"newport_task:{task_id}",
                                3600,  # 1 hour expiry
                                "pending"
                            )
                            logger.info(f"Newport AI video generation started: {task_id}")
                            return {
                                "success": True,
                                "task_id": task_id,
                                "status": "pending"
                            }
                        else:
                            logger.error(f"Newport AI error: {result}")
                            return {
                                "success": False,
                                "error": result.get('message', 'Unknown error')
                            }
                    else:
                        error_text = await resp.text()
                        logger.error(f"Newport AI request failed: {resp.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"API request failed: {resp.status}"
                        }
        except Exception as e:
            logger.error(f"Newport AI exception: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_lipsync_video(
        self,
        video_url: str,
        audio_url: str,
        enhance: bool = True
    ) -> dict:
        """
        Generate lip-synced video using LipSync API
        Returns task_id for polling
        """
        url = f"{self.base_url}/lipsync"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "srcVideoUrl": video_url,
            "audioUrl": audio_url,
            "videoParams": {
                "video_width": 0,  # Keep original width
                "video_height": 0,  # Keep original height
                "video_enhance": 1 if enhance else 0
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get('code') == 0:
                            task_id = result['data']['taskId']
                            self.redis.setex(f"newport_task:{task_id}", 3600, "pending")
                            logger.info(f"Newport AI lipsync started: {task_id}")
                            return {
                                "success": True,
                                "task_id": task_id,
                                "status": "pending"
                            }
                        else:
                            return {
                                "success": False,
                                "error": result.get('message', 'Unknown error')
                            }
                    else:
                        error_text = await resp.text()
                        return {
                            "success": False,
                            "error": f"API request failed: {resp.status}"
                        }
        except Exception as e:
            logger.error(f"Newport AI lipsync exception: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_task_status(self, task_id: str) -> dict:
        """
        Poll Newport AI for task status
        """
        url = "https://api.newportai.com/api/getAsyncResult"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "taskId": task_id
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get('code') == 0:
                            data = result.get('data', {})
                            task = data.get('task', {})
                            status_code = task.get('status')
                            
                            # Status codes: 1=pending, 2=processing, 3=completed, 4=failed
                            status_map = {
                                1: "pending",
                                2: "processing",
                                3: "completed",
                                4: "failed"
                            }
                            
                            status = status_map.get(status_code, "unknown")
                            
                            # Update Redis cache
                            self.redis.setex(f"newport_task:{task_id}", 3600, status)
                            
                            response = {
                                "task_id": task_id,
                                "status": status,
                                "video_url": None
                            }
                            
                            if status == "completed" and 'videos' in data:
                                videos = data['videos']
                                if videos and len(videos) > 0:
                                    response['video_url'] = videos[0].get('videoUrl')
                                    logger.info(f"Video generation completed: {task_id}")
                            
                            return response
                        else:
                            return {
                                "task_id": task_id,
                                "status": "failed",
                                "error": result.get('message', 'Unknown error')
                            }
                    else:
                        return {
                            "task_id": task_id,
                            "status": "failed",
                            "error": f"Status check failed: {resp.status}"
                        }
        except Exception as e:
            logger.error(f"Status check exception: {str(e)}")
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e)
            }

video_service = VideoService()