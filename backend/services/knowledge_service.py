from sentence_transformers import SentenceTransformer
from chromadb import Client
from chromadb.config import Settings
import os
from typing import List, Dict
import uuid

class KnowledgeService:
    """Service for knowledge base and RAG operations (Single Responsibility)"""
    
    def __init__(self):
        # Initialize sentence transformer for embeddings
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB
        self.chroma_client = Client(Settings(
            persist_directory="/app/backend/chroma_db",
            anonymized_telemetry=False
        ))
    
    def get_or_create_collection(self, user_id: str):
        """Get or create user's knowledge collection"""
        collection_name = f"user_{user_id}_knowledge"
        return self.chroma_client.get_or_create_collection(name=collection_name)
    
    async def add_knowledge(self, user_id: str, document: str, metadata: dict) -> str:
        """Add document to user's knowledge base"""
        collection = self.get_or_create_collection(user_id)
        
        # Generate embedding
        embedding = self.embedder.encode(document).tolist()
        
        # Generate unique ID
        doc_id = str(uuid.uuid4())
        
        # Add to ChromaDB
        collection.add(
            embeddings=[embedding],
            documents=[document],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        return doc_id
    
    async def search_knowledge(
        self, 
        user_id: str, 
        query: str, 
        top_k: int = 3
    ) -> List[Dict]:
        """Search user's knowledge base"""
        collection = self.get_or_create_collection(user_id)
        
        # Generate query embedding
        query_embedding = self.embedder.encode(query).tolist()
        
        # Search in ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Format results
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    "content": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else 0
                })
        
        return formatted_results
    
    async def delete_knowledge(self, user_id: str, doc_id: str) -> bool:
        """Delete document from knowledge base"""
        try:
            collection = self.get_or_create_collection(user_id)
            collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            print(f"Delete knowledge error: {e}")
            return False

knowledge_service = KnowledgeService()