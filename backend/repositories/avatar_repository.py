from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, List
from models.avatar import Avatar
from datetime import datetime

class AvatarRepository:
    """Repository for Avatar data operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.avatars
    
    async def create(self, avatar: Avatar) -> Avatar:
        """Create a new avatar"""
        avatar_dict = avatar.model_dump()
        avatar_dict['created_at'] = avatar_dict['created_at'].isoformat()
        avatar_dict['updated_at'] = avatar_dict['updated_at'].isoformat()
        
        await self.collection.insert_one(avatar_dict)
        return avatar
    
    async def find_by_id(self, avatar_id: str) -> Optional[Avatar]:
        """Find avatar by ID"""
        avatar_dict = await self.collection.find_one({"id": avatar_id}, {"_id": 0})
        if avatar_dict:
            avatar_dict['created_at'] = datetime.fromisoformat(avatar_dict['created_at'])
            avatar_dict['updated_at'] = datetime.fromisoformat(avatar_dict['updated_at'])
            return Avatar(**avatar_dict)
        return None
    
    async def find_by_user(self, user_id: str) -> Optional[Avatar]:
        """Find avatar by user ID"""
        avatar_dict = await self.collection.find_one({"user_id": user_id}, {"_id": 0})
        if avatar_dict:
            avatar_dict['created_at'] = datetime.fromisoformat(avatar_dict['created_at'])
            avatar_dict['updated_at'] = datetime.fromisoformat(avatar_dict['updated_at'])
            return Avatar(**avatar_dict)
        return None
    
    async def update(self, avatar_id: str, update_data: dict) -> bool:
        """Update avatar"""
        from datetime import timezone
        update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
        result = await self.collection.update_one(
            {"id": avatar_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def delete(self, avatar_id: str) -> bool:
        """Delete avatar"""
        result = await self.collection.delete_one({"id": avatar_id})
        return result.deleted_count > 0