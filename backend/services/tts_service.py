import aiohttp
import os
import logging

logger = logging.getLogger(__name__)

class TTSService:
    """Service for Newport AI Text-to-Speech with Voice Cloning"""
    
    def __init__(self):
        self.api_key = os.environ.get('NEWPORT_API_KEY')
        self.base_url = "https://api.newportai.com/api/async"
    
    async def clone_voice(self, voice_url: str) -> dict:
        """
        Clone voice using Newport AI Voice Clone API
        Returns cloneId for use with Do TTS Clone
        """
        url = f"{self.base_url}/voice_clone"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "voiceUrl": voice_url
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get('code') == 0:
                            task_id = result['data']['taskId']
                            logger.info(f"Voice clone task started: {task_id}")
                            return {
                                "success": True,
                                "task_id": task_id,
                                "status": "pending"
                            }
                        else:
                            logger.error(f"Voice clone error: {result}")
                            return {
                                "success": False,
                                "error": result.get('message', 'Unknown error')
                            }
                    else:
                        error_text = await resp.text()
                        logger.error(f"Voice clone request failed: {resp.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"API request failed: {resp.status}"
                        }
        except Exception as e:
            logger.error(f"Voice clone exception: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_voice_clone_status(self, task_id: str) -> dict:
        """
        Poll Newport AI for voice clone task status
        Returns cloneId when completed
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
                            
                            response = {
                                "task_id": task_id,
                                "status": status,
                                "clone_id": None
                            }
                            
                            if status == "completed" and 'cloneId' in data:
                                response['clone_id'] = data['cloneId']
                                logger.info(f"Voice clone completed: {data['cloneId']}")
                            elif status == "failed":
                                response['error'] = "Voice clone failed"
                            
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
            logger.error(f"Voice clone status check exception: {str(e)}")
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e)
            }
    
    async def text_to_speech_with_clone(
        self,
        text: str,
        clone_id: str,
        language: str = "en"
    ) -> dict:
        """
        Convert text to speech using cloned voice with Do TTS Clone API
        Returns task_id for polling
        """
        url = f"{self.base_url}/do_tts_clone"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "cloneId": clone_id,
            "text": text,
            "lan": language
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get('code') == 0:
                            task_id = result['data']['taskId']
                            logger.info(f"TTS Clone generation started: {task_id}")
                            return {
                                "success": True,
                                "task_id": task_id,
                                "status": "pending"
                            }
                        else:
                            logger.error(f"TTS Clone error: {result}")
                            return {
                                "success": False,
                                "error": result.get('message', 'Unknown error')
                            }
                    else:
                        error_text = await resp.text()
                        logger.error(f"TTS Clone request failed: {resp.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"API request failed: {resp.status}"
                        }
        except Exception as e:
            logger.error(f"TTS Clone exception: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def text_to_speech(
        self,
        text: str,
        audio_id: str = "en-US-1",  # Default voice
        language: str = "en"
    ) -> dict:
        """
        Convert text to speech using Newport AI TTS Pro
        Returns task_id for polling
        """
        url = f"{self.base_url}/do_tts_pro"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "audioId": audio_id,
            "text": text,
            "lan": language
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get('code') == 0:
                            task_id = result['data']['taskId']
                            logger.info(f"TTS generation started: {task_id}")
                            return {
                                "success": True,
                                "task_id": task_id,
                                "status": "pending"
                            }
                        else:
                            logger.error(f"TTS error: {result}")
                            return {
                                "success": False,
                                "error": result.get('message', 'Unknown error')
                            }
                    else:
                        error_text = await resp.text()
                        logger.error(f"TTS request failed: {resp.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"API request failed: {resp.status}"
                        }
        except Exception as e:
            logger.error(f"TTS exception: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_tts_status(self, task_id: str) -> dict:
        """
        Poll Newport AI for TTS task status
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
                            
                            response = {
                                "task_id": task_id,
                                "status": status,
                                "audio_url": None
                            }
                            
                            if status == "completed" and 'audios' in data:
                                audios = data['audios']
                                if audios and len(audios) > 0:
                                    response['audio_url'] = audios[0].get('audioUrl')
                                    logger.info(f"TTS generation completed: {task_id}")
                            
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
            logger.error(f"TTS status check exception: {str(e)}")
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e)
            }

tts_service = TTSService()
