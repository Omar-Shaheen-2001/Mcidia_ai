from flask import render_template, session, redirect, url_for, flash, request, jsonify
from . import member_dashboard_bp
from utils.decorators import organization_role_required
from models import db, Document
from utils.ai_client import llm_chat
from flask_jwt_extended import get_jwt_identity

@member_dashboard_bp.route('/<int:org_id>/knowledge', methods=['GET', 'POST'])
@organization_role_required('member', 'admin', 'owner', org_id_param='org_id')
def knowledge(org_id, _membership=None, _organization=None):
    """AI-powered knowledge search in organization documents"""
    lang = session.get('language', 'ar')
    
    search_results = None
    query = None
    
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        
        if query:
            # Get organization documents
            documents = db.session.query(Document).join(
                Document.user
            ).filter(
                Document.user.has(organization_id=org_id)
            ).all()
            
            if documents:
                # Prepare context from documents
                docs_context = "\n\n".join([
                    f"Document: {doc.filename}\nContent: {doc.content[:500]}..."
                    for doc in documents[:5]  # Limit to 5 most relevant docs
                ])
                
                # Build AI prompt
                system_prompt = f"""أنت مساعد ذكاء اصطناعي متخصص في البحث عن المعلومات في مستندات المؤسسة.
سأعطيك مجموعة من المستندات وسؤال من المستخدم.
قم بالبحث في المستندات وتقديم إجابة دقيقة وواضحة.

المستندات المتاحة:
{docs_context}"""
                
                user_prompt = f"السؤال: {query}"
                
                try:
                    # Get AI response
                    ai_response = llm_chat(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        max_tokens=500
                    )
                    
                    search_results = {
                        'answer': ai_response,
                        'documents_searched': len(documents)
                    }
                except Exception as e:
                    flash(f'حدث خطأ في البحث / Search error: {str(e)}', 'danger')
            else:
                flash('لا توجد مستندات في المؤسسة / No documents found in organization', 'info')
    
    return render_template(
        'member_dashboard/knowledge.html',
        lang=lang,
        organization=_organization,
        membership=_membership,
        query=query,
        search_results=search_results
    )
