#!/usr/bin/env python3
"""
Test if Newport AI TTS is actually synchronous
"""

import asyncio
import aiohttp
import time

API_KEY = "eba23df301a841f493c60ec872ee39a9"

async def test_tts_sync():
    """Test if TTS API is synchronous and returns results immediately"""
    
    async with aiohttp.ClientSession() as session:
        
        print("🎵 Testing TTS Pro API for synchronous response...")
        tts_url = "https://api.newportai.com/api/async/do_tts_pro"
        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "audioId": "en-US-1",
            "text": "Hello world test",
            "lan": "en"
        }
        
        start_time = time.time()
        
        try:
            async with session.post(tts_url, json=payload, headers=headers) as resp:
                end_time = time.time()
                duration = end_time - start_time
                
                print(f"TTS Status: {resp.status}")
                print(f"Response time: {duration:.2f} seconds")
                
                if resp.status == 200:
                    data = await resp.json()
                    print(f"Full TTS Response: {data}")
                    
                    # Check if there's already an audio URL in the response
                    if 'data' in data:
                        data_section = data['data']
                        print(f"Data section: {data_section}")
                        
                        # Look for audio URL or result
                        if 'audioUrl' in data_section:
                            print(f"✅ Audio URL found immediately: {data_section['audioUrl']}")
                        elif 'result' in data_section:
                            print(f"✅ Result found: {data_section['result']}")
                        else:
                            task_id = data_section.get('taskId')
                            print(f"Task ID: {task_id}")
                            
                            # Try waiting and calling the same endpoint again
                            print("\n⏳ Waiting 5 seconds and trying again...")
                            await asyncio.sleep(5)
                            
                            async with session.post(tts_url, json=payload, headers=headers) as resp2:
                                if resp2.status == 200:
                                    data2 = await resp2.json()
                                    print(f"Second call response: {data2}")
                else:
                    error_text = await resp.text()
                    print(f"TTS Error: {error_text}")
        except Exception as e:
            print(f"TTS Exception: {str(e)}")

        # Test DreamAvatar API as well
        print(f"\n🎬 Testing DreamAvatar API...")
        dream_url = "https://api.newportai.com/api/async/dreamavatar/image_to_video/3.0fast"
        
        # Use a test image URL
        dream_payload = {
            "audio": "https://example.com/test.mp3",  # This will fail but let's see the response
            "image": "https://example.com/test.jpg",
            "prompt": "a person talking naturally",
            "resolution": "480p"
        }
        
        try:
            async with session.post(dream_url, json=dream_payload, headers=headers) as resp:
                print(f"DreamAvatar Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    print(f"DreamAvatar Response: {data}")
                else:
                    error_text = await resp.text()
                    print(f"DreamAvatar Error: {error_text}")
        except Exception as e:
            print(f"DreamAvatar Exception: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_tts_sync())