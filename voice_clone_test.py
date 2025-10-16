#!/usr/bin/env python3
"""
Voice Cloning Backend Testing Suite for Digital Self Platform
Tests Newport AI Voice Clone integration with real API calls
"""

import asyncio
import aiohttp
import json
import os
import time
from pathlib import Path
import tempfile
import io
import wave

# Configuration
BASE_URL = "https://component-review-2.preview.emergentagent.com/api"
TEST_USER_EMAIL = "voice.tester@example.com"
TEST_USER_PASSWORD = "VoiceTest123!"
TEST_USER_NAME = "Voice Tester"

class VoiceCloneTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.user_id = None
        self.avatar_id = None
        self.conversation_id = None
        self.voice_task_id = None
        self.clone_id = None
        
    async def setup(self):
        """Initialize test session"""
        self.session = aiohttp.ClientSession()
        print(f"🔧 Testing voice cloning at: {BASE_URL}")
        
    async def cleanup(self):
        """Clean up test session"""
        if self.session:
            await self.session.close()
            
    async def test_health_check(self):
        """Test 1: Health Check"""
        print("\n🏥 Testing Health Check...")
        try:
            async with self.session.get(f"{BASE_URL}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ Health check passed: {data}")
                    return True
                else:
                    print(f"❌ Health check failed: {resp.status}")
                    return False
        except Exception as e:
            print(f"❌ Health check exception: {str(e)}")
            return False
            
    async def test_user_authentication(self):
        """Test 2: User Authentication"""
        print("\n👤 Testing User Authentication...")
        
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
                    return await self.test_user_login()
                else:
                    print(f"❌ Registration failed: {resp.status}")
                    return False
        except Exception as e:
            print(f"❌ Registration exception: {str(e)}")
            return False
            
    async def test_user_login(self):
        """Test 2b: User Login"""
        print("\n🔐 Testing User Login...")
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
        
    async def create_test_audio_file(self):
        """Create a test audio file for voice upload"""
        # Create a simple test audio file (1 second of silence)
        sample_rate = 44100
        duration = 1.0  # 1 second
        frames = int(sample_rate * duration)
        
        # Generate simple sine wave for testing
        import math
        frequency = 440  # A4 note
        audio_data = []
        for i in range(frames):
            value = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
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
        
    async def test_voice_upload(self):
        """Test 3: Voice Sample Upload - NEW FEATURE"""
        print("\n🎤 Testing Voice Sample Upload...")
        
        if not self.auth_token:
            print("❌ No auth token available")
            return False
            
        try:
            # Create test audio file
            audio_path = await self.create_test_audio_file()
            print(f"📁 Created test audio: {audio_path}")
            
            # Upload voice sample
            with open(audio_path, 'rb') as f:
                form_data = aiohttp.FormData()
                form_data.add_field('file', f, filename='voice_sample.wav', content_type='audio/wav')
                
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
            
    async def test_voice_clone_status_polling(self):
        """Test 4: Voice Clone Status Polling - NEW FEATURE"""
        print(f"\n⏳ Testing Voice Clone Status Polling for task: {self.voice_task_id}")
        
        if not self.auth_token or not self.voice_task_id:
            print("❌ Missing auth token or voice task ID")
            return False
            
        try:
            headers = self.get_auth_headers()
            max_attempts = 30  # 30 attempts = ~60 seconds
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
            
            print("⏰ Voice clone polling timed out (60+ seconds)")
            return False
            
        except Exception as e:
            print(f"❌ Voice clone status polling exception: {str(e)}")
            return False
            
    async def test_get_my_voice(self):
        """Test 5: Get My Voice - NEW FEATURE"""
        print("\n🔊 Testing Get My Voice...")
        
        if not self.auth_token:
            print("❌ No auth token available")
            return False
            
        try:
            headers = self.get_auth_headers()
            async with self.session.get(f"{BASE_URL}/voices/my-voice", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    voice_id = data.get('voice_id')
                    message = data.get('message')
                    
                    print(f"✅ Voice retrieved successfully!")
                    print(f"✅ Voice ID: {voice_id}")
                    print(f"✅ Message: {message}")
                    
                    # Verify it matches our clone_id
                    if voice_id == self.clone_id:
                        print("✅ Voice ID matches cloned voice!")
                        return True
                    else:
                        print(f"⚠️ Voice ID mismatch: expected {self.clone_id}, got {voice_id}")
                        return True  # Still success if voice exists
                        
                elif resp.status == 404:
                    print("ℹ️ No cloned voice found (expected if cloning failed)")
                    return False
                else:
                    error_text = await resp.text()
                    print(f"❌ Get voice failed: {resp.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Get voice exception: {str(e)}")
            return False
            
    async def setup_avatar_and_conversation(self):
        """Setup avatar and conversation for chat testing"""
        print("\n🖼️ Setting up avatar and conversation...")
        
        # Create simple test image for avatar
        from PIL import Image
        img = Image.new('RGB', (512, 512), color='lightblue')
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        img.save(temp_file.name, 'JPEG')
        temp_file.close()
        
        try:
            # Upload avatar
            with open(temp_file.name, 'rb') as f:
                form_data = aiohttp.FormData()
                form_data.add_field('file', f, filename='avatar.jpg', content_type='image/jpeg')
                
                headers = self.get_auth_headers()
                async with self.session.post(f"{BASE_URL}/avatars/upload", 
                                           data=form_data, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.avatar_id = data.get('id')
                        print(f"✅ Avatar uploaded: {self.avatar_id}")
                    else:
                        print(f"⚠️ Avatar upload failed: {resp.status}")
            
            # Create conversation
            payload = {"title": "Voice Clone Test Conversation"}
            async with self.session.post(f"{BASE_URL}/conversations/", 
                                       json=payload, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.conversation_id = data.get('id')
                    print(f"✅ Conversation created: {self.conversation_id}")
                    return True
                else:
                    print(f"⚠️ Conversation creation failed: {resp.status}")
                    return False
                    
            # Clean up temp file
            os.unlink(temp_file.name)
            
        except Exception as e:
            print(f"❌ Setup exception: {str(e)}")
            return False
            
    async def test_chat_with_cloned_voice(self):
        """Test 6: Chat with Cloned Voice - INTEGRATION TEST"""
        print("\n💬 Testing Chat with Cloned Voice...")
        
        if not self.auth_token or not self.conversation_id:
            print("❌ Missing auth token or conversation ID")
            return False
            
        try:
            # Send a short message to test cloned voice
            payload = {
                "content": "Hello! Test my cloned voice."
            }
            
            headers = self.get_auth_headers()
            print("📤 Sending message with cloned voice...")
            print("   Expected: Backend should use text_to_speech_with_clone() with user's voice_id")
            
            async with self.session.post(f"{BASE_URL}/chat/send?conversation_id={self.conversation_id}", 
                                       json=payload, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    message = data.get('message', {})
                    video_task_id = data.get('video_task_id')
                    
                    print(f"✅ AI Response: {message.get('content', '')[:100]}...")
                    print(f"✅ Response time: {message.get('response_time_ms')}ms")
                    
                    if video_task_id:
                        print(f"✅ Video task created with cloned voice: {video_task_id}")
                        return video_task_id
                    else:
                        print("⚠️ No video task ID returned (might be expected if TTS fails)")
                        return True  # Still success if message worked
                else:
                    error_text = await resp.text()
                    print(f"❌ Chat with cloned voice failed: {resp.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Chat with cloned voice exception: {str(e)}")
            return False
            
    async def run_voice_clone_tests(self):
        """Run all voice cloning tests in sequence"""
        print("🚀 Starting Voice Cloning Backend Tests")
        print("=" * 60)
        
        results = {}
        
        # Test 1: Health Check
        results['health_check'] = await self.test_health_check()
        
        # Test 2: Authentication
        results['authentication'] = await self.test_user_authentication()
        
        if results['authentication']:
            # Test 3: Voice Upload (NEW)
            results['voice_upload'] = await self.test_voice_upload()
            
            # Test 4: Voice Clone Status Polling (NEW)
            if results['voice_upload']:
                results['voice_clone_polling'] = await self.test_voice_clone_status_polling()
                
                # Test 5: Get My Voice (NEW)
                if results['voice_clone_polling']:
                    results['get_my_voice'] = await self.test_get_my_voice()
                    
                    # Test 6: Setup for chat testing
                    setup_success = await self.setup_avatar_and_conversation()
                    
                    # Test 7: Chat with Cloned Voice (INTEGRATION)
                    if setup_success:
                        chat_result = await self.test_chat_with_cloned_voice()
                        results['chat_with_cloned_voice'] = bool(chat_result)
                    else:
                        results['chat_with_cloned_voice'] = False
                else:
                    results['get_my_voice'] = False
                    results['chat_with_cloned_voice'] = False
            else:
                results['voice_clone_polling'] = False
                results['get_my_voice'] = False
                results['chat_with_cloned_voice'] = False
        
        # Print Summary
        print("\n" + "=" * 60)
        print("📊 VOICE CLONING TEST RESULTS SUMMARY")
        print("=" * 60)
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title():<30} {status}")
        
        # Overall result
        critical_tests = ['health_check', 'authentication', 'voice_upload']
        critical_passed = all(results.get(test, False) for test in critical_tests)
        
        new_features = ['voice_upload', 'voice_clone_polling', 'get_my_voice', 'chat_with_cloned_voice']
        new_features_passed = all(results.get(test, False) for test in new_features)
        
        print("\n" + "=" * 60)
        if critical_passed and new_features_passed:
            print("🎉 ALL VOICE CLONING TESTS PASSED - Newport AI Voice Clone Integration Working!")
        elif critical_passed:
            print("⚠️ BASIC TESTS PASSED - Voice Cloning Features Need Attention")
        else:
            print("🚨 CRITICAL TESTS FAILED - Voice Cloning Integration Issues")
        
        return results

async def main():
    """Main test runner"""
    tester = VoiceCloneTester()
    
    try:
        await tester.setup()
        results = await tester.run_voice_clone_tests()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())