"""
Vector Store implementation using JSON-based storage
Supports: add_document, search, delete, persist, list_documents
Multi-tenant with org_id isolation
"""
import json
import os
from typing import List, Dict, Optional
import numpy as np
from datetime import datetime

class JSONVectorStore:
    """Simple JSON-based vector store with semantic search"""
    
    def __init__(self, store_path: str = None):
        if store_path is None:
            store_path = os.path.join(os.path.dirname(__file__), '../../data/vector_store.json')
        
        self.store_path = store_path
        self.data = self._load_store()
        os.makedirs(os.path.dirname(store_path), exist_ok=True)
    
    def _load_store(self) -> Dict:
        """Load vector store from JSON file"""
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {'documents': {}}
        return {'documents': {}}
    
    def _persist(self) -> bool:
        """Save vector store to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
            with open(self.store_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error persisting vector store: {e}")
            return False
    
    def add_document(self, doc_id: str, text: str, embedding: List[float], 
                     org_id: int, metadata: Dict = None) -> bool:
        """
        Add document to vector store
        Args:
            doc_id: Unique document ID
            text: Document text
            embedding: Text embedding vector
            org_id: Organization ID (for multi-tenancy)
            metadata: Additional metadata
        """
        if not embedding or not doc_id or not text:
            return False
        
        if not isinstance(embedding, list):
            embedding = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
        
        try:
            doc_key = f"org_{org_id}_{doc_id}"
            
            self.data['documents'][doc_key] = {
                'id': doc_id,
                'org_id': org_id,
                'text': text[:5000],
                'embedding': embedding,
                'metadata': metadata or {},
                'added_at': datetime.utcnow().isoformat()
            }
            
            return self._persist()
        except Exception as e:
            print(f"Error adding document: {e}")
            return False
    
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            a = np.array(v1)
            b = np.array(v2)
            
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            return float(dot_product / (norm_a * norm_b))
        except:
            return 0.0
    
    def search(self, query_embedding: List[float], org_id: int, top_k: int = 5) -> List[Dict]:
        """
        Semantic search using cosine similarity
        Args:
            query_embedding: Query embedding vector
            org_id: Organization ID (filters by org)
            top_k: Number of top results to return
        
        Returns:
            List of similar documents with scores
        """
        if not query_embedding:
            return []
        
        results = []
        
        for doc_key, doc in self.data.get('documents', {}).items():
            # Multi-tenant filter: only search within same org_id
            if doc.get('org_id') != org_id:
                continue
            
            if 'embedding' not in doc:
                continue
            
            similarity = self._cosine_similarity(query_embedding, doc['embedding'])
            
            results.append({
                'id': doc['id'],
                'text': doc['text'],
                'score': similarity,
                'metadata': doc.get('metadata', {}),
                'added_at': doc.get('added_at')
            })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete document from vector store"""
        try:
            keys_to_delete = [k for k in self.data['documents'].keys() if doc_id in k]
            
            for key in keys_to_delete:
                del self.data['documents'][key]
            
            if keys_to_delete:
                return self._persist()
            return True
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False
    
    def list_documents(self, org_id: int, limit: int = 100) -> List[Dict]:
        """List documents for an organization"""
        try:
            docs = []
            for doc_key, doc in self.data.get('documents', {}).items():
                if doc.get('org_id') == org_id:
                    docs.append({
                        'id': doc['id'],
                        'text': doc['text'][:200],
                        'metadata': doc.get('metadata', {}),
                        'added_at': doc.get('added_at')
                    })
            
            return docs[:limit]
        except Exception as e:
            print(f"Error listing documents: {e}")
            return []
    
    def clear_org_documents(self, org_id: int) -> bool:
        """Delete all documents for an organization"""
        try:
            keys_to_delete = [k for k, doc in self.data['documents'].items() 
                            if doc.get('org_id') == org_id]
            
            for key in keys_to_delete:
                del self.data['documents'][key]
            
            if keys_to_delete:
                return self._persist()
            return True
        except Exception as e:
            print(f"Error clearing org documents: {e}")
            return False

# Global vector store instance
_vector_store = None

def get_vector_store() -> JSONVectorStore:
    """Get or create global vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = JSONVectorStore()
    return _vector_store

def reset_vector_store():
    """Reset global vector store instance"""
    global _vector_store
    _vector_store = None
