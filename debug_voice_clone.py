#!/usr/bin/env python3
"""
Debug Voice Clone API - Test Newport AI directly
"""

import asyncio
import aiohttp
import os

NEWPORT_API_KEY = "eba23df301a841f493c60ec872ee39a9"
BASE_URL = "https://api.newportai.com/api"

async def test_newport_voice_clone_direct():
    """Test Newport AI Voice Clone API directly"""
    print("🔍 Testing Newport AI Voice Clone API directly...")
    
    # Use a public test audio URL
    test_voice_url = "https://component-review-2.preview.emergentagent.com/uploads/530f3dc2-3e97-489e-b523-a9048f534e59.wav"
    
    headers = {
        'Authorization': f'Bearer {NEWPORT_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "voiceUrl": test_voice_url
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"📤 Sending voice clone request to: {BASE_URL}/async/voice_clone")
            print(f"📤 Voice URL: {test_voice_url}")
            print(f"📤 Payload: {payload}")
            
            async with session.post(f"{BASE_URL}/async/voice_clone", 
                                  json=payload, headers=headers) as resp:
                print(f"📥 Response status: {resp.status}")
                
                if resp.status == 200:
                    result = await resp.json()
                    print(f"📥 Response: {result}")
                    
                    if result.get('code') == 0:
                        task_id = result['data']['taskId']
                        print(f"✅ Voice clone task created: {task_id}")
                        
                        # Now test polling
                        await test_newport_polling(task_id)
                        
                    else:
                        print(f"❌ Voice clone API error: {result}")
                else:
                    error_text = await resp.text()
                    print(f"❌ Voice clone request failed: {resp.status} - {error_text}")
                    
    except Exception as e:
        print(f"❌ Voice clone exception: {str(e)}")

async def test_newport_polling(task_id):
    """Test Newport AI polling"""
    print(f"\n🔍 Testing Newport AI polling for task: {task_id}")
    
    headers = {
        'Authorization': f'Bearer {NEWPORT_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "taskId": task_id
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            for attempt in range(5):  # Test 5 times
                print(f"   Polling attempt {attempt + 1}/5...")
                
                async with session.post("https://api.newportai.com/api/getAsyncResult", 
                                      json=payload, headers=headers) as resp:
                    print(f"   Response status: {resp.status}")
                    
                    if resp.status == 200:
                        result = await resp.json()
                        print(f"   Response: {result}")
                        
                        if result.get('code') == 0:
                            data = result.get('data', {})
                            task = data.get('task', {})
                            status_code = task.get('status')
                            
                            status_map = {1: "pending", 2: "processing", 3: "completed", 4: "failed"}
                            status = status_map.get(status_code, "unknown")
                            
                            print(f"   Task status: {status} (code: {status_code})")
                            
                            if status == "completed":
                                if 'cloneId' in data:
                                    print(f"✅ Voice clone completed: {data['cloneId']}")
                                    return
                                else:
                                    print("❌ Completed but no cloneId found")
                                    return
                            elif status == "failed":
                                print("❌ Voice clone failed")
                                return
                        else:
                            print(f"   API error: {result}")
                    else:
                        error_text = await resp.text()
                        print(f"   Polling failed: {resp.status} - {error_text}")
                
                await asyncio.sleep(3)  # Wait 3 seconds between polls
                
    except Exception as e:
        print(f"❌ Polling exception: {str(e)}")

async def test_voice_url_accessibility():
    """Test if the voice URL is accessible"""
    print("\n🔍 Testing voice URL accessibility...")
    
    voice_url = "https://component-review-2.preview.emergentagent.com/uploads/530f3dc2-3e97-489e-b523-a9048f534e59.wav"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(voice_url) as resp:
                print(f"📥 Voice URL status: {resp.status}")
                
                if resp.status == 200:
                    content_type = resp.headers.get('content-type', 'unknown')
                    content_length = resp.headers.get('content-length', 'unknown')
                    print(f"✅ Voice URL accessible")
                    print(f"   Content-Type: {content_type}")
                    print(f"   Content-Length: {content_length}")
                else:
                    print(f"❌ Voice URL not accessible: {resp.status}")
                    
    except Exception as e:
        print(f"❌ Voice URL test exception: {str(e)}")

async def main():
    """Main debug runner"""
    print("🚀 Starting Newport AI Voice Clone Debug")
    print("=" * 60)
    
    await test_voice_url_accessibility()
    await test_newport_voice_clone_direct()

if __name__ == "__main__":
    asyncio.run(main())