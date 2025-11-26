"""
Document Processing Pipeline
Handles file upload, extraction, chunking, and embedding
"""
import os
from typing import Dict, Optional
from utils.knowledge.embeddings import extract_text_from_file, chunk_text, create_embedding
from utils.knowledge.vector_store import get_vector_store

def process_document_file(file_path: str, doc_id: int, filename: str, 
                         category: str = 'General', tags: list = None) -> Dict:
    """
    Process a document file end-to-end
    
    Args:
        file_path: Path to the document file
        doc_id: Database document ID
        filename: Original filename
        category: Document category
        tags: Document tags
    
    Returns:
        Dict with processing results
    """
    if not os.path.exists(file_path):
        return {'success': False, 'error': 'File not found'}
    
    try:
        tags = tags or []
        
        # 1. Extract text
        text = extract_text_from_file(file_path)
        if not text:
            return {'success': False, 'error': 'Could not extract text from file'}
        
        # 2. Clean and normalize text
        text = normalize_text(text)
        
        # 3. Calculate quality score
        quality_score = calculate_quality_score(text)
        
        # 4. Chunk text
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        
        # 5. Create embeddings and add to vector store
        vector_store = get_vector_store()
        processed_chunks = 0
        
        for idx, chunk in enumerate(chunks):
            embedding = create_embedding(chunk)
            if embedding:
                vector_store.add_document(
                    doc_id=f"doc_{doc_id}_chunk_{idx}",
                    text=chunk,
                    embedding=embedding,
                    org_id=1,  # System org
                    metadata={
                        'document_id': doc_id,
                        'category': category,
                        'tags': tags,
                        'chunk_index': idx,
                        'filename': filename,
                        'chunk_count': len(chunks)
                    }
                )
                processed_chunks += 1
        
        return {
            'success': True,
            'text_length': len(text),
            'chunks_created': len(chunks),
            'chunks_embedded': processed_chunks,
            'quality_score': quality_score
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def normalize_text(text: str) -> str:
    """
    Clean and normalize text
    """
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove special characters but keep Arabic/English
    import re
    text = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\w\s\.\,\:\;\(\)\-]', '', text)
    
    return text.strip()

def calculate_quality_score(text: str) -> int:
    """
    Calculate document quality score (0-100)
    Based on text length, structure, etc.
    """
    lines = len(text.split('\n'))
    words = len(text.split())
    sentences = len(text.split('.'))
    
    score = 0
    
    # Length scoring (0-40 points)
    if words > 1000:
        score += 40
    elif words > 500:
        score += 30
    elif words > 100:
        score += 20
    else:
        score += 10
    
    # Structure scoring (0-30 points)
    if lines > 50:
        score += 30
    elif lines > 20:
        score += 20
    elif lines > 5:
        score += 10
    
    # Content scoring (0-30 points)
    if sentences > 30:
        score += 30
    elif sentences > 10:
        score += 20
    else:
        score += 10
    
    return min(100, score)
