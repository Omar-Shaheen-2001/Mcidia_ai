"""
Embeddings module for creating and managing text embeddings
Uses OpenAI or SentenceTransformer based on availability
"""
import json
import os
from typing import List, Dict, Optional
from flask import current_app

def get_embedding_model():
    """Get available embedding model - OpenAI or SentenceTransformer"""
    try:
        from openai import OpenAI
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            return 'openai'
    except:
        pass
    
    try:
        from sentence_transformers import SentenceTransformer
        return 'sentence_transformer'
    except:
        pass
    
    return None

def create_embedding(text: str) -> Optional[List[float]]:
    """
    Create embedding for text using available model
    Returns embedding vector or None if failed
    """
    if not text or not isinstance(text, str):
        return None
    
    model = get_embedding_model()
    
    try:
        if model == 'openai':
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text[:8191]
            )
            return response.data[0].embedding
        
        elif model == 'sentence_transformer':
            from sentence_transformers import SentenceTransformer
            embedder = SentenceTransformer('all-MiniLM-L6-v2')
            embedding = embedder.encode(text, convert_to_tensor=False)
            return embedding.tolist()
    
    except Exception as e:
        print(f"Error creating embedding: {e}")
        return None

def create_embeddings_for_document(text: str, metadata: Dict = None) -> Dict:
    """
    Create embedding for document with metadata
    
    Args:
        text: Document text content
        metadata: Dict with org_id, project_id, user_id, type, timestamp, etc.
    
    Returns:
        Dict with embedding and metadata
    """
    embedding = create_embedding(text)
    
    if embedding is None:
        return None
    
    return {
        'text': text[:5000],
        'embedding': embedding,
        'metadata': metadata or {},
        'embedding_model': get_embedding_model()
    }

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from Word document"""
    try:
        from docx import Document
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting DOCX: {e}")
        return ""

def extract_text_from_file(file_path: str) -> str:
    """Extract text from various file types"""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext in ['.docx', '.doc']:
        return extract_text_from_docx(file_path)
    elif ext in ['.txt', '.md']:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    return ""

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks"""
    chunks = []
    sentences = text.split('\n')
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) > chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk += "\n" + sentence if current_chunk else sentence
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks
