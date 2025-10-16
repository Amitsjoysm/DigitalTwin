from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, List
from models.user import User
from datetime import datetime, timezone

class UserRepository:
    """Repository for User data operations (Dependency Inversion)"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.users
    
    async def create(self, user: User) -> User:
        """Create a new user"""
        user_dict = user.model_dump()
        user_dict['created_at'] = user_dict['created_at'].isoformat()
        user_dict['updated_at'] = user_dict['updated_at'].isoformat()
        
        await self.collection.insert_one(user_dict)
        return user
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        user_dict = await self.collection.find_one({"email": email}, {"_id": 0})
        if user_dict:
            user_dict['created_at'] = datetime.fromisoformat(user_dict['created_at'])
            user_dict['updated_at'] = datetime.fromisoformat(user_dict['updated_at'])
            return User(**user_dict)
        return None
    
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Find user by ID"""
        user_dict = await self.collection.find_one({"id": user_id}, {"_id": 0})
        if user_dict:
            user_dict['created_at'] = datetime.fromisoformat(user_dict['created_at'])
            user_dict['updated_at'] = datetime.fromisoformat(user_dict['updated_at'])
            return User(**user_dict)
        return None
    
    async def update(self, user_id: str, update_data: dict) -> bool:
        """Update user"""
        update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
        result = await self.collection.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def delete(self, user_id: str) -> bool:
        """Delete user"""
        result = await self.collection.delete_one({"id": user_id})
        return result.deleted_count > 0