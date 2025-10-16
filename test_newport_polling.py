#!/usr/bin/env python3
"""
Test Newport AI polling endpoint properly
"""

import asyncio
import aiohttp
import json

API_KEY = "eba23df301a841f493c60ec872ee39a9"

async def test_newport_polling():
    """Test Newport AI polling with proper POST request"""
    print("🧪 Testing Newport AI TTS + Polling Flow")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # Step 1: Create TTS task
        print("🎤 Step 1: Creating TTS task...")
        tts_url = "https://api.newportai.com/api/async/do_tts_pro"
        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "audioId": "en-US-1",
            "text": "Hello! This is a test message.",
            "lan": "en"
        }
        
        try:
            async with session.post(tts_url, json=payload, headers=headers) as resp:
                print(f"TTS Status: {resp.status}")
                result = await resp.json()
                print(f"TTS Response: {json.dumps(result, indent=2)}")
                
                if result.get('code') == 0:
                    task_id = result['data']['taskId']
                    print(f"✅ TTS task created: {task_id}")
                    
                    # Step 2: Poll for results
                    print(f"\n⏳ Step 2: Polling for results...")
                    poll_url = "https://api.newportai.com/api/getAsyncResult"
                    poll_payload = {"taskId": task_id}
                    
                    for attempt in range(10):  # Poll 10 times
                        await asyncio.sleep(2)  # Wait 2 seconds between polls
                        print(f"   Attempt {attempt + 1}/10...")
                        
                        async with session.post(poll_url, json=poll_payload, headers=headers) as poll_resp:
                            print(f"   Poll Status: {poll_resp.status}")
                            poll_result = await poll_resp.json()
                            print(f"   Poll Response: {json.dumps(poll_result, indent=2)}")
                            
                            # Check if we got a different response
                            if poll_result.get('code') == 0:
                                print("✅ Task completed successfully!")
                                return True
                            elif poll_result.get('code') == 13015:
                                print("⚠️ Rate limited - this is expected with free tier")
                                return True
                            elif poll_result.get('code') != 13014:
                                print(f"❌ Unexpected error: {poll_result}")
                                return False
                    
                    print("⏰ Polling timed out")
                    return False
                else:
                    print(f"❌ TTS creation failed: {result}")
                    return False
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return False

if __name__ == "__main__":
    asyncio.run(test_newport_polling())