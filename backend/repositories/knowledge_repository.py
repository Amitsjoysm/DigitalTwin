from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, List
from models.knowledge import KnowledgeEntry
from datetime import datetime, timezone

class KnowledgeRepository:
    """Repository for Knowledge data operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.knowledge
    
    async def create(self, knowledge: KnowledgeEntry) -> KnowledgeEntry:
        """Create a new knowledge entry"""
        know_dict = knowledge.model_dump()
        know_dict['created_at'] = know_dict['created_at'].isoformat()
        know_dict['updated_at'] = know_dict['updated_at'].isoformat()
        
        await self.collection.insert_one(know_dict)
        return knowledge
    
    async def find_by_id(self, knowledge_id: str) -> Optional[KnowledgeEntry]:
        """Find knowledge by ID"""
        know_dict = await self.collection.find_one({"id": knowledge_id}, {"_id": 0})
        if know_dict:
            know_dict['created_at'] = datetime.fromisoformat(know_dict['created_at'])
            know_dict['updated_at'] = datetime.fromisoformat(know_dict['updated_at'])
            return KnowledgeEntry(**know_dict)
        return None
    
    async def find_by_user(self, user_id: str, limit: int = 100) -> List[KnowledgeEntry]:
        """Find knowledge entries by user ID"""
        cursor = self.collection.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).limit(limit)
        entries = await cursor.to_list(length=limit)
        
        result = []
        for know_dict in entries:
            know_dict['created_at'] = datetime.fromisoformat(know_dict['created_at'])
            know_dict['updated_at'] = datetime.fromisoformat(know_dict['updated_at'])
            result.append(KnowledgeEntry(**know_dict))
        
        return result
    
    async def update(self, knowledge_id: str, update_data: dict) -> bool:
        """Update knowledge entry"""
        update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
        result = await self.collection.update_one(
            {"id": knowledge_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def delete(self, knowledge_id: str) -> bool:
        """Delete knowledge entry"""
        result = await self.collection.delete_one({"id": knowledge_id})
        return result.deleted_count > 0