#!/usr/bin/env python3
"""
Test Newport AI API endpoints directly
"""

import asyncio
import aiohttp
import os

API_KEY = "eba23df301a841f493c60ec872ee39a9"

async def test_newport_endpoints():
    """Test various Newport AI endpoints to understand the API structure"""
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: TTS Pro API
        print("🎵 Testing TTS Pro API...")
        tts_url = "https://api.newportai.com/api/async/do_tts_pro"
        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "audioId": "en-US-1",
            "text": "Hello world",
            "lan": "en"
        }
        
        try:
            async with session.post(tts_url, json=payload, headers=headers) as resp:
                print(f"TTS Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    print(f"TTS Response: {data}")
                    task_id = data.get('data', {}).get('taskId')
                    if task_id:
                        print(f"Task ID: {task_id}")
                        
                        # Test 2: Try different polling endpoints
                        polling_endpoints = [
                            "https://api.newportai.com/api/getAsyncResult",
                            "https://api.newportai.com/api/async/results",
                            "https://api.newportai.com/api/results",
                            "https://api.newportai.com/api/async/status",
                            "https://api.newportai.com/api/status",
                            f"https://api.newportai.com/api/async/results/{task_id}",
                            f"https://api.newportai.com/api/results/{task_id}",
                        ]
                        
                        for endpoint in polling_endpoints:
                            print(f"\n🔍 Testing polling endpoint: {endpoint}")
                            
                            if "results" in endpoint and task_id not in endpoint:
                                # POST with taskId in body
                                poll_payload = {"taskId": task_id}
                                async with session.post(endpoint, json=poll_payload, headers=headers) as poll_resp:
                                    print(f"  POST Status: {poll_resp.status}")
                                    if poll_resp.status != 404:
                                        text = await poll_resp.text()
                                        print(f"  Response: {text[:200]}...")
                            else:
                                # GET request
                                async with session.get(endpoint, headers=headers) as poll_resp:
                                    print(f"  GET Status: {poll_resp.status}")
                                    if poll_resp.status != 404:
                                        text = await poll_resp.text()
                                        print(f"  Response: {text[:200]}...")
                else:
                    error_text = await resp.text()
                    print(f"TTS Error: {error_text}")
        except Exception as e:
            print(f"TTS Exception: {str(e)}")
        
        # Test 3: Try to get API documentation or available endpoints
        print(f"\n📚 Testing API info endpoints...")
        info_endpoints = [
            "https://api.newportai.com/api",
            "https://api.newportai.com/api/info",
            "https://api.newportai.com/api/version",
            "https://api.newportai.com/docs",
        ]
        
        for endpoint in info_endpoints:
            try:
                async with session.get(endpoint, headers=headers) as resp:
                    print(f"{endpoint}: {resp.status}")
                    if resp.status == 200:
                        text = await resp.text()
                        print(f"  Response: {text[:200]}...")
            except Exception as e:
                print(f"{endpoint}: Exception - {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_newport_endpoints())