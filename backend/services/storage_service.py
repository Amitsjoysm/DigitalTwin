import aiohttp
import os
import logging

logger = logging.getLogger(__name__)

class StorageService:
    """Service for uploading files to Newport AI storage"""
    
    def __init__(self):
        self.api_key = os.environ.get('NEWPORT_API_KEY')
        self.base_url = "https://api.newportai.com/api"
    
    async def get_upload_policy(self) -> dict:
        """Get upload policy from Newport AI"""
        url = f"{self.base_url}/upload/policy"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get('code') == 0:
                            return {
                                "success": True,
                                "data": result.get('data', {})
                            }
                        else:
                            return {
                                "success": False,
                                "error": result.get('message', 'Unknown error')
                            }
                    else:
                        return {
                            "success": False,
                            "error": f"API request failed: {resp.status}"
                        }
        except Exception as e:
            logger.error(f"Get upload policy exception: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def upload_file(self, file_path: str, content_type: str = "image/jpeg") -> dict:
        """
        Upload file to Newport AI storage
        Returns public URL of uploaded file
        """
        # First get upload policy
        policy_result = await self.get_upload_policy()
        
        if not policy_result.get('success'):
            return policy_result
        
        policy_data = policy_result['data']
        upload_url = policy_data.get('uploadUrl')
        
        if not upload_url:
            return {
                "success": False,
                "error": "No upload URL in policy"
            }
        
        # Upload file
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Extract file name from path
            file_name = os.path.basename(file_path)
            
            form_data = aiohttp.FormData()
            
            # Add policy fields if provided
            for key, value in policy_data.items():
                if key not in ['uploadUrl']:
                    form_data.add_field(key, str(value))
            
            # Add file
            form_data.add_field('file', file_data, 
                              filename=file_name,
                              content_type=content_type)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(upload_url, data=form_data) as resp:
                    if resp.status in [200, 201]:
                        result = await resp.json()
                        
                        # Get the public URL from response
                        file_url = result.get('url') or result.get('fileUrl') or result.get('data', {}).get('url')
                        
                        if file_url:
                            logger.info(f"File uploaded successfully: {file_url}")
                            return {
                                "success": True,
                                "url": file_url
                            }
                        else:
                            # If no URL in response, construct it from policy
                            base_url = policy_data.get('baseUrl', '')
                            key = policy_data.get('key', file_name)
                            file_url = f"{base_url}/{key}" if base_url else None
                            
                            return {
                                "success": True,
                                "url": file_url or upload_url,
                                "response": result
                            }
                    else:
                        error_text = await resp.text()
                        logger.error(f"Upload failed: {resp.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"Upload failed: {resp.status}"
                        }
        except Exception as e:
            logger.error(f"File upload exception: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

storage_service = StorageService()
