from groq import Groq
import os
from typing import List, Dict

class LLMService:
    """Service for Groq LLM operations (Single Responsibility)"""
    
    def __init__(self):
        self.client = Groq(
            api_key=os.environ.get('GROQ_API_KEY')
        )
        self.model = "llama-3.1-70b-versatile"
    
    def generate_personality_prompt(self, user_data: dict) -> str:
        """Generate system prompt based on user personality"""
        personality = user_data.get('personality', {})
        name = user_data.get('name', 'User')
        
        prompt = f"""You are {name}, responding as yourself. Your personality traits:
- Communication style: {'Formal' if personality.get('formality', 5) > 7 else 'Casual' if personality.get('formality', 5) < 4 else 'Balanced'}
- Enthusiasm: {'Very enthusiastic' if personality.get('enthusiasm', 5) > 7 else 'Reserved' if personality.get('enthusiasm', 5) < 4 else 'Moderate'}
- Response length: {'Detailed' if personality.get('verbosity', 5) > 7 else 'Concise' if personality.get('verbosity', 5) < 4 else 'Balanced'}
- Humor: {'Very humorous' if personality.get('humor', 5) > 7 else 'Serious' if personality.get('humor', 5) < 4 else 'Occasional humor'}

Respond naturally as {name} would, maintaining consistency with your personality traits."""
        
        return prompt
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        personality_prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> str:
        """Generate response from Groq LLM"""
        try:
            system_message = {"role": "system", "content": personality_prompt}
            full_messages = [system_message] + messages
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"LLM generation error: {str(e)}")
    
    async def generate_streaming_response(
        self,
        messages: List[Dict[str, str]],
        personality_prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7
    ):
        """Generate streaming response from Groq LLM"""
        try:
            system_message = {"role": "system", "content": personality_prompt}
            full_messages = [system_message] + messages
            
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise Exception(f"LLM streaming error: {str(e)}")

llm_service = LLMService()