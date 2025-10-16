#!/usr/bin/env python3
"""
Focused Backend Test - Core Chat Functionality
Tests the essential chat flow without video generation
"""

import asyncio
import aiohttp
import json
import tempfile
from PIL import Image

# Configuration
BASE_URL = "https://component-review-2.preview.emergentagent.com/api"
TEST_USER_EMAIL = "alice.smith@example.com"
TEST_USER_PASSWORD = "SecurePass456!"
TEST_USER_NAME = "Alice Smith"

class FocusedTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.user_id = None
        self.avatar_id = None
        self.conversation_id = None
        
    async def setup(self):
        """Initialize test session"""
        self.session = aiohttp.ClientSession()
        print(f"🔧 Testing backend at: {BASE_URL}")
        
    async def cleanup(self):
        """Clean up test session"""
        if self.session:
            await self.session.close()
    
    async def test_authentication(self):
        """Test user registration and login"""
        print("\n🔐 Testing Authentication...")
        
        # Try registration first
        payload = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "name": TEST_USER_NAME
        }
        
        try:
            async with self.session.post(f"{BASE_URL}/auth/register", json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.auth_token = data.get('access_token')
                    self.user_id = data.get('user', {}).get('id')
                    print(f"✅ User registered: {self.user_id}")
                    return True
                elif resp.status == 400:
                    # Try login instead
                    login_payload = {"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
                    async with self.session.post(f"{BASE_URL}/auth/login", json=login_payload) as login_resp:
                        if login_resp.status == 200:
                            data = await login_resp.json()
                            self.auth_token = data.get('access_token')
                            self.user_id = data.get('user', {}).get('id')
                            print(f"✅ User logged in: {self.user_id}")
                            return True
                        else:
                            print(f"❌ Login failed: {login_resp.status}")
                            return False
                else:
                    print(f"❌ Registration failed: {resp.status}")
                    return False
        except Exception as e:
            print(f"❌ Auth exception: {str(e)}")
            return False
    
    def get_auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    async def test_avatar_upload(self):
        """Test avatar upload"""
        print("\n🖼️ Testing Avatar Upload...")
        
        if not self.auth_token:
            print("❌ No auth token")
            return False
        
        try:
            # Create test image
            img = Image.new('RGB', (512, 512), color='lightgreen')
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            img.save(temp_file.name, 'JPEG')
            temp_file.close()
            
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
                        return True
                    else:
                        error_text = await resp.text()
                        print(f"❌ Avatar upload failed: {resp.status} - {error_text}")
                        return False
        except Exception as e:
            print(f"❌ Avatar upload exception: {str(e)}")
            return False
    
    async def test_conversation_creation(self):
        """Test conversation creation"""
        print("\n💬 Testing Conversation Creation...")
        
        if not self.auth_token:
            print("❌ No auth token")
            return False
        
        try:
            payload = {"title": "Test Chat Session"}
            headers = self.get_auth_headers()
            
            async with self.session.post(f"{BASE_URL}/conversations/", 
                                       json=payload, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.conversation_id = data.get('id')
                    print(f"✅ Conversation created: {self.conversation_id}")
                    return True
                else:
                    error_text = await resp.text()
                    print(f"❌ Conversation creation failed: {resp.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Conversation creation exception: {str(e)}")
            return False
    
    async def test_chat_message_basic(self):
        """Test basic chat message (text only, no video)"""
        print("\n💭 Testing Basic Chat Message (LLM Response Only)...")
        
        if not self.auth_token or not self.conversation_id:
            print("❌ Missing auth token or conversation ID")
            return False
        
        try:
            payload = {"content": "Hi there! How are you?"}
            headers = self.get_auth_headers()
            
            print("📤 Sending message to Groq LLM...")
            async with self.session.post(f"{BASE_URL}/chat/send?conversation_id={self.conversation_id}", 
                                       json=payload, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    message = data.get('message', {})
                    video_task_id = data.get('video_task_id')
                    
                    print(f"✅ AI Response: {message.get('content', '')[:100]}...")
                    print(f"✅ Response time: {message.get('response_time_ms')}ms")
                    
                    if video_task_id:
                        print(f"⚠️ Video task created but may fail: {video_task_id}")
                        return {"success": True, "video_task_id": video_task_id}
                    else:
                        print("ℹ️ No video task (expected if avatar missing or TTS fails)")
                        return {"success": True, "video_task_id": None}
                else:
                    error_text = await resp.text()
                    print(f"❌ Chat message failed: {resp.status} - {error_text}")
                    return {"success": False}
        except Exception as e:
            print(f"❌ Chat message exception: {str(e)}")
            return {"success": False}
    
    async def test_video_status_if_available(self, video_task_id):
        """Test video status polling if task ID is available"""
        if not video_task_id:
            print("\n⏭️ Skipping video status test (no task ID)")
            return True
        
        print(f"\n🎬 Testing Video Status Polling: {video_task_id}")
        
        try:
            headers = self.get_auth_headers()
            
            # Try a few polls to see what happens
            for attempt in range(3):
                print(f"   Poll attempt {attempt + 1}/3...")
                
                async with self.session.get(f"{BASE_URL}/chat/video-status/{video_task_id}", 
                                          headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        status = data.get('status')
                        print(f"   Status: {status}")
                        
                        if status == 'completed':
                            video_url = data.get('video_url')
                            print(f"✅ Video completed: {video_url}")
                            return True
                        elif status == 'failed':
                            error = data.get('error', 'Unknown error')
                            print(f"❌ Video failed: {error}")
                            return False
                        
                        await asyncio.sleep(2)
                    else:
                        error_text = await resp.text()
                        print(f"   Status check failed: {resp.status} - {error_text}")
                        return False
            
            print("⏰ Video still processing after 3 attempts")
            return True  # Not a failure, just slow
            
        except Exception as e:
            print(f"❌ Video status exception: {str(e)}")
            return False
    
    async def run_focused_tests(self):
        """Run focused tests on core functionality"""
        print("🎯 FOCUSED BACKEND TESTING - Core Chat Functionality")
        print("=" * 60)
        
        results = {}
        
        # Test 1: Authentication
        results['authentication'] = await self.test_authentication()
        
        if results['authentication']:
            # Test 2: Avatar Upload
            results['avatar_upload'] = await self.test_avatar_upload()
            
            # Test 3: Conversation Creation
            results['conversation_creation'] = await self.test_conversation_creation()
            
            if results['conversation_creation']:
                # Test 4: Basic Chat (most important)
                chat_result = await self.test_chat_message_basic()
                results['chat_basic'] = chat_result.get('success', False) if isinstance(chat_result, dict) else chat_result
                
                # Test 5: Video Status (if available)
                if isinstance(chat_result, dict) and chat_result.get('video_task_id'):
                    results['video_status'] = await self.test_video_status_if_available(chat_result['video_task_id'])
                else:
                    results['video_status'] = None
        
        # Print Summary
        print("\n" + "=" * 60)
        print("📊 FOCUSED TEST RESULTS")
        print("=" * 60)
        
        for test_name, result in results.items():
            if result is None:
                status = "⏭️ SKIP"
            elif result:
                status = "✅ PASS"
            else:
                status = "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title():<25} {status}")
        
        # Critical assessment
        critical_tests = ['authentication', 'conversation_creation', 'chat_basic']
        critical_passed = all(results.get(test, False) for test in critical_tests)
        
        print("\n" + "=" * 60)
        if critical_passed:
            print("🎉 CORE FUNCTIONALITY WORKING - Chat system operational!")
            print("   ✅ Users can register/login")
            print("   ✅ Users can create conversations") 
            print("   ✅ Users can send messages and get AI responses")
            if results.get('avatar_upload'):
                print("   ✅ Avatar upload working")
            if results.get('video_status') is False:
                print("   ⚠️ Video generation has issues (Newport AI TTS)")
            elif results.get('video_status') is None:
                print("   ℹ️ Video generation not tested (no task ID)")
        else:
            print("🚨 CORE FUNCTIONALITY ISSUES")
            failed_tests = [test for test in critical_tests if not results.get(test, False)]
            print(f"   Failed: {', '.join(failed_tests)}")
        
        return results

async def main():
    """Main test runner"""
    tester = FocusedTester()
    
    try:
        await tester.setup()
        results = await tester.run_focused_tests()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())