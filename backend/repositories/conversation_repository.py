from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, List
from models.conversation import Conversation, Message
from datetime import datetime, timezone

class ConversationRepository:
    """Repository for Conversation data operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.conversations
    
    async def create(self, conversation: Conversation) -> Conversation:
        """Create a new conversation"""
        conv_dict = conversation.model_dump()
        conv_dict['started_at'] = conv_dict['started_at'].isoformat()
        conv_dict['last_message_at'] = conv_dict['last_message_at'].isoformat()
        
        # Convert message timestamps
        for msg in conv_dict['messages']:
            msg['timestamp'] = msg['timestamp'].isoformat()
        
        await self.collection.insert_one(conv_dict)
        return conversation
    
    async def find_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """Find conversation by ID"""
        conv_dict = await self.collection.find_one({"id": conversation_id}, {"_id": 0})
        if conv_dict:
            conv_dict['started_at'] = datetime.fromisoformat(conv_dict['started_at'])
            conv_dict['last_message_at'] = datetime.fromisoformat(conv_dict['last_message_at'])
            
            for msg in conv_dict['messages']:
                msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
            
            return Conversation(**conv_dict)
        return None
    
    async def find_by_user(self, user_id: str, limit: int = 50) -> List[Conversation]:
        """Find conversations by user ID"""
        cursor = self.collection.find({"user_id": user_id}, {"_id": 0}).sort("last_message_at", -1).limit(limit)
        conversations = await cursor.to_list(length=limit)
        
        result = []
        for conv_dict in conversations:
            conv_dict['started_at'] = datetime.fromisoformat(conv_dict['started_at'])
            conv_dict['last_message_at'] = datetime.fromisoformat(conv_dict['last_message_at'])
            
            for msg in conv_dict['messages']:
                msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
            
            result.append(Conversation(**conv_dict))
        
        return result
    
    async def add_message(self, conversation_id: str, message: Message) -> bool:
        """Add message to conversation"""
        msg_dict = message.model_dump()
        msg_dict['timestamp'] = msg_dict['timestamp'].isoformat()
        
        result = await self.collection.update_one(
            {"id": conversation_id},
            {
                "$push": {"messages": msg_dict},
                "$set": {"last_message_at": datetime.now(timezone.utc).isoformat()},
                "$inc": {"message_count": 1}
            }
        )
        return result.modified_count > 0
    
    async def update(self, conversation_id: str, update_data: dict) -> bool:
        """Update conversation"""
        result = await self.collection.update_one(
            {"id": conversation_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def delete(self, conversation_id: str) -> bool:
        """Delete conversation"""
        result = await self.collection.delete_one({"id": conversation_id})
        return result.deleted_count > 0