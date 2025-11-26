"""
RAG (Retrieval Augmented Generation) module
Integrates embeddings, vector store, and AI to provide context-aware responses
"""
from flask import Blueprint, request, jsonify, session, current_app
from flask_jwt_extended import get_jwt_identity
from utils.decorators import login_required
from utils.knowledge.embeddings import (
    create_embedding, create_embeddings_for_document, chunk_text,
    extract_text_from_file
)
from utils.knowledge.vector_store import get_vector_store
from utils.ai_providers.ai_manager import AIManager
from models import User, Organization, AILog
from datetime import datetime
import json
import uuid
import os

knowledge_rag_bp = Blueprint('knowledge_rag', __name__)

def get_db():
    """Get database instance"""
    return current_app.extensions['sqlalchemy']

def get_user_org_id(user_id: int) -> int:
    """Get user's organization ID"""
    db = get_db()
    user = db.session.query(User).filter_by(id=user_id).first()
    return user.organization_id if user else None

@knowledge_rag_bp.route('/knowledge/add', methods=['POST'])
@login_required
def add_knowledge():
    """
    Add document/knowledge to vector store
    Supports: text, PDF, Word documents
    """
    db = get_db()
    user_id = int(get_jwt_identity())
    org_id = get_user_org_id(user_id)
    
    if not org_id:
        return jsonify({'error': 'User must belong to an organization'}), 400
    
    try:
        data = request.get_json() or {}
        text = data.get('text', '')
        file_path = data.get('file_path')
        doc_type = data.get('type', 'general')
        
        if file_path and os.path.exists(file_path):
            text = extract_text_from_file(file_path)
        
        if not text:
            return jsonify({'error': 'No text content provided'}), 400
        
        chunks = chunk_text(text)
        vector_store = get_vector_store()
        added_count = 0
        
        for chunk in chunks:
            doc_id = f"doc_{org_id}_{uuid.uuid4().hex[:8]}"
            embedding = create_embedding(chunk)
            
            if embedding:
                metadata = {
                    'org_id': org_id,
                    'user_id': user_id,
                    'type': doc_type,
                    'original_file': file_path or 'manual',
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                if vector_store.add_document(
                    doc_id, chunk, embedding, org_id, metadata
                ):
                    added_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Added {added_count} document chunks',
            'chunks_added': added_count
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@knowledge_rag_bp.route('/knowledge/search', methods=['POST'])
@login_required
def search_knowledge():
    """
    Search vector store for relevant documents
    Uses semantic search with embeddings
    """
    db = get_db()
    user_id = int(get_jwt_identity())
    org_id = get_user_org_id(user_id)
    
    if not org_id:
        return jsonify({'error': 'User must belong to an organization'}), 400
    
    try:
        data = request.get_json() or {}
        query = data.get('query', '')
        top_k = data.get('top_k', 5)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        query_embedding = create_embedding(query)
        
        if not query_embedding:
            return jsonify({'error': 'Failed to create query embedding'}), 500
        
        vector_store = get_vector_store()
        results = vector_store.search(query_embedding, org_id, top_k)
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results,
            'total': len(results)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@knowledge_rag_bp.route('/knowledge/query_ai', methods=['POST'])
@login_required
def query_with_rag():
    """
    Full RAG pipeline: search + augment + AI response
    Retrieves relevant documents and includes them in AI prompt
    """
    db = get_db()
    user_id = int(get_jwt_identity())
    org_id = get_user_org_id(user_id)
    lang = session.get('language', 'ar')
    
    if not org_id:
        return jsonify({'error': 'User must belong to an organization'}), 400
    
    try:
        start_time = datetime.utcnow()
        data = request.get_json() or {}
        query = data.get('query', '')
        context_type = data.get('context_type', 'general')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        query_embedding = create_embedding(query)
        
        if not query_embedding:
            return jsonify({'error': 'Failed to process query'}), 500
        
        vector_store = get_vector_store()
        context_docs = vector_store.search(query_embedding, org_id, top_k=5)
        
        context_text = ""
        if context_docs:
            context_text = "**السياق المسترجع من قاعدة المعرفة:**\n\n"
            for doc in context_docs:
                context_text += f"- {doc['text'][:300]}...\n"
        
        system_prompt = f"""أنت مستشار خبير متخصص في {context_type}.
قدّم إجابات دقيقة ومفيدة بناءً على السياق المتوفر.
إذا لم تجد معلومات ذات صلة، أخبر المستخدم بذلك.
الرد بالعربية إذا كانت الأسئلة بالعربية، والإنجليزية إذا كانت بالإنجليزية."""
        
        augmented_prompt = f"""{context_text}

**السؤال:** {query}"""
        
        ai = AIManager.for_use_case('consultation')
        ai_response = ai.chat(system_prompt, augmented_prompt)
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        estimated_tokens = len(query.split()) + len(ai_response.split())
        estimated_cost = (estimated_tokens * 0.00175 / 1000) if estimated_tokens > 0 else 0.001
        
        log = AILog(
            user_id=user_id,
            organization_id=org_id,
            module='rag',
            service_type='query_with_context',
            provider_type='openai',
            model_name='gpt-3.5-turbo',
            prompt=query,
            response=ai_response,
            tokens_used=estimated_tokens,
            estimated_cost=estimated_cost,
            execution_time_ms=execution_time,
            status='success'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'query': query,
            'response': ai_response,
            'context_docs_used': len(context_docs),
            'execution_time_ms': execution_time
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@knowledge_rag_bp.route('/knowledge/list', methods=['GET'])
@login_required
def list_knowledge():
    """List documents in organization's knowledge base"""
    user_id = int(get_jwt_identity())
    org_id = get_user_org_id(user_id)
    
    if not org_id:
        return jsonify({'error': 'User must belong to an organization'}), 400
    
    try:
        vector_store = get_vector_store()
        docs = vector_store.list_documents(org_id, limit=100)
        
        return jsonify({
            'success': True,
            'total': len(docs),
            'documents': docs
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@knowledge_rag_bp.route('/knowledge/delete/<doc_id>', methods=['DELETE'])
@login_required
def delete_knowledge(doc_id: str):
    """Delete document from knowledge base"""
    user_id = int(get_jwt_identity())
    org_id = get_user_org_id(user_id)
    
    try:
        vector_store = get_vector_store()
        vector_store.delete_document(doc_id)
        
        return jsonify({'success': True, 'message': 'Document deleted'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
