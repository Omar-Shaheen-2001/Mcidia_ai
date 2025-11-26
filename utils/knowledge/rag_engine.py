"""
RAG Engine for intelligent answer generation
Combines retrieval with LLM reasoning
"""
import os
from typing import List, Dict, Optional
from utils.knowledge.embeddings import create_embedding
from utils.knowledge.vector_store import get_vector_store

def retrieve_relevant_chunks(query: str, category: str = None, top_k: int = 5) -> List[Dict]:
    """
    Retrieve relevant chunks using semantic search
    
    Args:
        query: Search query
        category: Optional category filter
        top_k: Number of top results
    
    Returns:
        List of relevant chunks with scores
    """
    try:
        # Create embedding for query
        query_embedding = create_embedding(query)
        if not query_embedding:
            return []
        
        # Search vector store
        vector_store = get_vector_store()
        results = vector_store.search(query_embedding, org_id=1, top_k=top_k * 2)
        
        # Filter by category if provided
        if category:
            results = [r for r in results if r.get('metadata', {}).get('category') == category]
        
        # Return top_k results
        return results[:top_k]
        
    except Exception as e:
        print(f"Retrieval error: {e}")
        return []

def generate_answer(query: str, context_chunks: List[Dict] = None, lang: str = 'ar') -> Dict:
    """
    Generate answer using LLM with retrieved context
    
    Args:
        query: User query
        context_chunks: Retrieved context chunks
        lang: Language (ar/en)
    
    Returns:
        Dict with answer, sources, and confidence
    """
    try:
        # If no context provided, retrieve it
        if not context_chunks:
            context_chunks = retrieve_relevant_chunks(query, top_k=5)
        
        # If still no context, return no data message
        if not context_chunks:
            return {
                'answer': 'لا توجد بيانات كافية في قاعدة المعرفة' if lang == 'ar' else 'Insufficient data in knowledge base',
                'sources': [],
                'confidence': 0.0,
                'has_context': False
            }
        
        # Prepare context
        context_text = "\n\n".join([
            f"[{i+1}] {chunk.get('text', '')}" 
            for i, chunk in enumerate(context_chunks[:3])
        ])
        
        # Call OpenAI API
        from openai import OpenAI
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            return {
                'answer': 'خدمة غير متاحة' if lang == 'ar' else 'Service unavailable',
                'sources': [],
                'confidence': 0.0,
                'has_context': False
            }
        
        client = OpenAI(api_key=api_key)
        
        # Build prompt
        if lang == 'ar':
            system_prompt = """أنت مساعد ذكي متخصص في الإجابة على أسئلة بناءً على المستندات المعطاة.
استخدم فقط المعلومات من السياق المقدم.
إذا لم تجد الإجابة في السياق، قل "لا توجد معلومات كافية" بوضوح.
تجنب الهلوسة والمعلومات غير المؤكدة."""
            user_message = f"""السياق:
{context_text}

السؤال: {query}

الرجاء الإجابة بناءً على السياق فقط."""
        else:
            system_prompt = """You are an intelligent assistant specialized in answering questions based on provided documents.
Use only the information from the given context.
If you don't find the answer in the context, clearly state "Insufficient information".
Avoid hallucination and unverified information."""
            user_message = f"""Context:
{context_text}

Question: {query}

Please answer based on the context only."""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content
        
        # Calculate confidence based on top result score
        confidence = context_chunks[0].get('score', 0) if context_chunks else 0
        
        # Prepare sources
        sources = [
            {
                'filename': chunk.get('metadata', {}).get('filename', 'Unknown'),
                'category': chunk.get('metadata', {}).get('category', 'General'),
                'score': chunk.get('score', 0)
            }
            for chunk in context_chunks[:3]
        ]
        
        return {
            'answer': answer,
            'sources': sources,
            'confidence': float(confidence),
            'has_context': True
        }
        
    except Exception as e:
        print(f"Answer generation error: {e}")
        return {
            'answer': 'حدث خطأ في معالجة السؤال' if lang == 'ar' else 'Error processing question',
            'sources': [],
            'confidence': 0.0,
            'has_context': False,
            'error': str(e)
        }
