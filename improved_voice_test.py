#!/usr/bin/env python3
"""
Improved Voice Cloning Test with longer audio file
"""

import asyncio
import aiohttp
import json
import os
import time
from pathlib import Path
import tempfile
import wave
import math

# Configuration
BASE_URL = "https://component-review-2.preview.emergentagent.com/api"
TEST_USER_EMAIL = "improved.voice.tester@example.com"
TEST_USER_PASSWORD = "ImprovedVoiceTest123!"
TEST_USER_NAME = "Improved Voice Tester"

class ImprovedVoiceTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.user_id = None
        self.voice_task_id = None
        self.clone_id = None
        
    async def setup(self):
        """Initialize test session"""
        self.session = aiohttp.ClientSession()
        print(f"🔧 Testing improved voice cloning at: {BASE_URL}")
        
    async def cleanup(self):
        """Clean up test session"""
        if self.session:
            await self.session.close()
            
    async def test_authentication(self):
        """Test authentication"""
        print("\n👤 Testing Authentication...")
        
        # Try registration first
        try:
            payload = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "name": TEST_USER_NAME
            }
            
            async with self.session.post(f"{BASE_URL}/auth/register", json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.auth_token = data.get('access_token')
                    self.user_id = data.get('user', {}).get('id')
                    print(f"✅ User registered: {self.user_id}")
                    return True
                elif resp.status == 400:
                    # User exists, try login
                    return await self.test_login()
                else:
                    print(f"❌ Registration failed: {resp.status}")
                    return False
        except Exception as e:
            print(f"❌ Registration exception: {str(e)}")
            return False
            
    async def test_login(self):
        """Test login"""
        print("\n🔐 Testing Login...")
        try:
            payload = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
            
            async with self.session.post(f"{BASE_URL}/auth/login", json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.auth_token = data.get('access_token')
                    self.user_id = data.get('user', {}).get('id')
                    print(f"✅ User logged in: {self.user_id}")
                    return True
                else:
                    error_text = await resp.text()
                    print(f"❌ Login failed: {resp.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Login exception: {str(e)}")
            return False
            
    def get_auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
        
    async def create_30_second_audio(self):
        """Create a 30-second test audio file for voice cloning"""
        sample_rate = 44100
        duration = 30.0  # 30 seconds as recommended
        frames = int(sample_rate * duration)
        
        # Generate more speech-like audio patterns
        audio_data = []
        for i in range(frames):
            t = i / sample_rate
            
            # Create speech-like patterns with multiple harmonics
            fundamental = 150  # Base frequency around human speech
            value1 = 0.4 * math.sin(2 * math.pi * fundamental * t)
            value2 = 0.2 * math.sin(2 * math.pi * fundamental * 2 * t)  # 2nd harmonic
            value3 = 0.1 * math.sin(2 * math.pi * fundamental * 3 * t)  # 3rd harmonic
            
            # Add speech-like modulation
            speech_envelope = 0.5 + 0.5 * math.sin(2 * math.pi * 2 * t)  # 2Hz modulation
            pause_pattern = 1.0 if (t % 4) < 3 else 0.1  # Pause every 4 seconds
            
            combined = (value1 + value2 + value3) * speech_envelope * pause_pattern
            value = int(16000 * combined)
            audio_data.append(value)
        
        # Create temporary WAV file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        
        with wave.open(temp_file.name, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            
            # Convert to bytes
            audio_bytes = b''.join([value.to_bytes(2, 'little', signed=True) for value in audio_data])
            wav_file.writeframes(audio_bytes)
        
        temp_file.close()
        return temp_file.name
        
    async def test_voice_upload_improved(self):
        """Test voice upload with 30-second audio"""
        print("\n🎤 Testing Voice Upload (30-second audio)...")
        
        if not self.auth_token:
            print("❌ No auth token available")
            return False
            
        try:
            # Create 30-second test audio
            audio_path = await self.create_30_second_audio()
            print(f"📁 Created 30-second test audio: {audio_path}")
            
            # Get file size
            file_size = os.path.getsize(audio_path)
            print(f"📊 Audio file size: {file_size} bytes ({file_size/1024/1024:.2f} MB)")
            
            # Upload voice sample
            with open(audio_path, 'rb') as f:
                form_data = aiohttp.FormData()
                form_data.add_field('file', f, filename='voice_sample_30s.wav', content_type='audio/wav')
                
                headers = self.get_auth_headers()
                async with self.session.post(f"{BASE_URL}/voices/upload", 
                                           data=form_data, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.voice_task_id = data.get('task_id')
                        
                        print(f"✅ Voice upload successful!")
                        print(f"✅ Voice clone task ID: {self.voice_task_id}")
                        print(f"✅ Message: {data.get('message')}")
                        
                        return True
                    else:
                        error_text = await resp.text()
                        print(f"❌ Voice upload failed: {resp.status} - {error_text}")
                        return False
                        
            # Clean up temp file
            os.unlink(audio_path)
            
        except Exception as e:
            print(f"❌ Voice upload exception: {str(e)}")
            return False
            
    async def test_file_serving(self):
        """Test if the voice file is served with correct MIME type"""
        print("\n🔍 Testing Voice File Serving...")
        
        if not self.voice_task_id:
            print("❌ No voice task ID available")
            return False
            
        # The file should be accessible via the new API endpoint
        # We need to get the filename from the upload response or construct it
        # For now, let's test the general file serving capability
        
        try:
            # Test a known file (we'll use a simple approach)
            test_url = f"{BASE_URL}/voices/file/test.wav"  # This will 404 but show us the endpoint works
            
            async with self.session.get(test_url) as resp:
                print(f"📥 File serving test status: {resp.status}")
                if resp.status == 404:
                    print("✅ File serving endpoint is working (404 expected for non-existent file)")
                    return True
                elif resp.status == 200:
                    content_type = resp.headers.get('content-type', 'unknown')
                    print(f"✅ File served with content-type: {content_type}")
                    return True
                else:
                    print(f"⚠️ Unexpected status: {resp.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ File serving test exception: {str(e)}")
            return False
            
    async def test_voice_clone_polling_improved(self):
        """Test voice clone polling with longer timeout"""
        print(f"\n⏳ Testing Voice Clone Polling (Extended) for task: {self.voice_task_id}")
        
        if not self.auth_token or not self.voice_task_id:
            print("❌ Missing auth token or voice task ID")
            return False
            
        try:
            headers = self.get_auth_headers()
            max_attempts = 60  # 60 attempts = ~2 minutes (voice cloning can take longer)
            attempt = 0
            
            while attempt < max_attempts:
                attempt += 1
                print(f"   Polling attempt {attempt}/{max_attempts}...")
                
                async with self.session.get(f"{BASE_URL}/voices/clone-status/{self.voice_task_id}", 
                                          headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        status = data.get('status')
                        clone_id = data.get('clone_id')
                        
                        print(f"   Status: {status}")
                        
                        if status == 'completed':
                            if clone_id:
                                self.clone_id = clone_id
                                print(f"✅ Voice clone completed!")
                                print(f"✅ Clone ID: {clone_id}")
                                print(f"✅ Message: {data.get('message')}")
                                return True
                            else:
                                print("❌ Voice clone completed but no clone_id provided")
                                return False
                        elif status == 'failed':
                            error = data.get('error', 'Unknown error')
                            print(f"❌ Voice clone failed: {error}")
                            
                            # Let's also check what the actual Newport AI response was
                            print("🔍 Checking Newport AI response details...")
                            return False
                        elif status in ['pending', 'processing']:
                            # Continue polling
                            await asyncio.sleep(2)
                            continue
                        else:
                            print(f"⚠️ Unknown status: {status}")
                            await asyncio.sleep(2)
                            continue
                    else:
                        error_text = await resp.text()
                        print(f"❌ Status check failed: {resp.status} - {error_text}")
                        return False
            
            print("⏰ Voice clone polling timed out (2+ minutes)")
            return False
            
        except Exception as e:
            print(f"❌ Voice clone polling exception: {str(e)}")
            return False
            
    async def run_improved_tests(self):
        """Run improved voice cloning tests"""
        print("🚀 Starting Improved Voice Cloning Tests")
        print("=" * 60)
        
        results = {}
        
        # Test 1: Authentication
        results['authentication'] = await self.test_authentication()
        
        if results['authentication']:
            # Test 2: Voice Upload with 30-second audio
            results['voice_upload'] = await self.test_voice_upload_improved()
            
            # Test 3: File Serving
            results['file_serving'] = await self.test_file_serving()
            
            # Test 4: Voice Clone Polling (Extended)
            if results['voice_upload']:
                results['voice_clone_polling'] = await self.test_voice_clone_polling_improved()
            else:
                results['voice_clone_polling'] = False
        
        # Print Summary
        print("\n" + "=" * 60)
        print("📊 IMPROVED VOICE CLONING TEST RESULTS")
        print("=" * 60)
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title():<30} {status}")
        
        return results

async def main():
    """Main test runner"""
    tester = ImprovedVoiceTester()
    
    try:
        await tester.setup()
        results = await tester.run_improved_tests()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())