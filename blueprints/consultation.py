from flask import Blueprint, render_template, request, flash, session, redirect, url_for, current_app, jsonify
from flask_jwt_extended import get_jwt_identity
from utils.decorators import login_required
from models import AILog, ChatSession, Service
from utils.ai_providers.ai_manager import AIManager
from datetime import datetime
import json
import time

consultation_bp = Blueprint('consultation', __name__)

@consultation_bp.route('/')
def index():
    lang = session.get('language', 'ar')
    db = current_app.extensions['sqlalchemy']
    
    # Get available services for consultation topics and convert to dict
    services = db.session.query(Service).filter_by(is_active=True).all()
    services_list = [{'id': s.id, 'title_ar': s.title_ar, 'title_en': s.title_en, 'slug': s.slug} for s in services]
    
    # Get recent sessions for current user if logged in
    recent_sessions = []
    try:
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        verify_jwt_in_request(optional=True, locations=['cookies'])
        user_id = get_jwt_identity()
        if user_id:
            recent_sessions = db.session.query(ChatSession).filter_by(
                user_id=int(user_id)
            ).order_by(ChatSession.updated_at.desc()).limit(5).all()
    except:
        pass
    
    return render_template('consultation/index.html', lang=lang, services=services_list, recent_sessions=recent_sessions)

@consultation_bp.route('/api/sessions', methods=['GET'])
@login_required
def get_sessions_api():
    """API endpoint to get user's consultation sessions"""
    db = current_app.extensions['sqlalchemy']
    user_id = int(get_jwt_identity())
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Get paginated sessions
    sessions = db.session.query(ChatSession).filter_by(
        user_id=user_id
    ).order_by(ChatSession.updated_at.desc()).paginate(page=page, per_page=per_page)
    
    sessions_list = []
    for s in sessions.items:
        try:
            messages = json.loads(s.messages) if s.messages else []
            message_count = len(messages)
            total_cost = sum(m.get('cost', 0) for m in messages if m.get('role') == 'assistant')
        except:
            message_count = 0
            total_cost = 0
        
        sessions_list.append({
            'id': s.id,
            'domain': s.domain,
            'message_count': message_count,
            'total_cost': round(total_cost, 4),
            'created_at': s.created_at.isoformat(),
            'updated_at': s.updated_at.isoformat()
        })
    
    return jsonify({
        'sessions': sessions_list,
        'total': sessions.total,
        'pages': sessions.pages,
        'current_page': page
    })

@consultation_bp.route('/sessions')
@login_required
def all_sessions():
    """View all consultation sessions"""
    lang = session.get('language', 'ar')
    return render_template('consultation/all_sessions.html', lang=lang)

@consultation_bp.route('/start')
@login_required
def start_session():
    """Start a new consultation session"""
    lang = session.get('language', 'ar')
    db = current_app.extensions['sqlalchemy']
    user_id = int(get_jwt_identity())
    
    # Get available services for topics and convert to dict
    services = db.session.query(Service).filter_by(is_active=True).all()
    services_list = [{'id': s.id, 'title_ar': s.title_ar, 'title_en': s.title_en, 'slug': s.slug} for s in services]
    
    return render_template('consultation/start.html', lang=lang, services=services_list)

@consultation_bp.route('/session/<int:session_id>')
@login_required
def view_session(session_id):
    """View an existing consultation session"""
    lang = session.get('language', 'ar')
    db = current_app.extensions['sqlalchemy']
    user_id = int(get_jwt_identity())
    
    # Get the session
    chat_session = db.session.query(ChatSession).filter_by(
        id=session_id,
        user_id=user_id
    ).first()
    
    if not chat_session:
        flash('جلسة غير موجودة' if lang == 'ar' else 'Session not found', 'danger')
        return redirect(url_for('consultation.index'))
    
    # Parse messages
    try:
        messages = json.loads(chat_session.messages) if chat_session.messages else []
    except:
        messages = []
    
    # Get available services and convert to dict
    services = db.session.query(Service).filter_by(is_active=True).all()
    services_list = [{'id': s.id, 'title_ar': s.title_ar, 'title_en': s.title_en, 'slug': s.slug} for s in services]
    
    return render_template(
        'consultation/session.html',
        lang=lang,
        session=chat_session,
        messages=messages,
        services=services_list
    )

@consultation_bp.route('/api/send-message', methods=['POST'])
@login_required
def send_message():
    """API endpoint to send a message in consultation"""
    start_time = time.time()
    
    db = current_app.extensions['sqlalchemy']
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    message = data.get('message')
    session_id = data.get('session_id')
    topic = data.get('topic', 'General Consultation')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    try:
        # RAG integration: Get relevant context from vector store
        rag_context = ""
        try:
            from utils.knowledge.embeddings import create_embedding
            from utils.knowledge.vector_store import get_vector_store
            from models import User
            
            user = db.session.query(User).filter_by(id=user_id).first()
            if user and user.organization_id:
                query_embedding = create_embedding(message)
                if query_embedding:
                    vector_store = get_vector_store()
                    context_docs = vector_store.search(query_embedding, user.organization_id, top_k=3)
                    
                    if context_docs:
                        rag_context = "\n**السياق من قاعدة المعرفة:**\n"
                        for doc in context_docs:
                            rag_context += f"- {doc['text'][:200]}...\n"
        except:
            pass
        
        # Call AI using AIManager (same as other consulting modules)
        ai = AIManager.for_use_case('consultation')
        
        system_prompt = f"""أنت مستشار خبير متخصص في مجال {topic}.
تقدّم استشارات عملية وقيّمة وقابلة للتطبيق.
كن موجزاً وفعالاً في إجابتك.
الرد بالعربية إذا كانت الأسئلة بالعربية، والإنجليزية إذا كانت بالإنجليزية."""
        
        augmented_message = f"{rag_context}\n\n**السؤال:** {message}" if rag_context else message
        ai_response = ai.chat(system_prompt, augmented_message)
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Estimate tokens and cost (rough estimation)
        estimated_tokens = len(message.split()) + len(ai_response.split())
        # OpenAI pricing: $0.0015 per 1K input, $0.002 per 1K output
        estimated_cost = (estimated_tokens * 0.00175 / 1000) if estimated_tokens > 0 else 0.001
        
        # Get provider info
        available_providers = AIManager.get_available_providers()
        provider_name = available_providers[0] if available_providers else 'huggingface'
        provider_config = AIManager.get_provider_info(provider_name)
        model_name = provider_config.get('default_model', 'llama3')
        
        # Log AI usage
        log = AILog(
            user_id=user_id,
            module='consultation',
            service_type=topic,
            provider_type=provider_name,
            model_name=model_name,
            prompt=message,
            response=ai_response,
            tokens_used=estimated_tokens,
            estimated_cost=estimated_cost,
            execution_time_ms=execution_time_ms,
            status='success'
        )
        db.session.add(log)
        
        # Update or create chat session
        if session_id:
            chat_session = db.session.query(ChatSession).filter_by(
                id=session_id,
                user_id=user_id
            ).first()
        else:
            chat_session = ChatSession(user_id=user_id, domain=topic)
        
        # Parse existing messages
        try:
            messages = json.loads(chat_session.messages) if chat_session.messages else []
        except:
            messages = []
        
        # Add new messages
        messages.append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.utcnow().isoformat()
        })
        messages.append({
            'role': 'assistant',
            'content': ai_response,
            'timestamp': datetime.utcnow().isoformat(),
            'cost': estimated_cost
        })
        
        chat_session.messages = json.dumps(messages)
        chat_session.updated_at = datetime.utcnow()
        
        if not session_id:
            db.session.add(chat_session)
        
        db.session.commit()
        
        return jsonify({
            'response': ai_response,
            'session_id': chat_session.id,
            'cost': estimated_cost,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        from openai import APIError, APIConnectionError, RateLimitError, AuthenticationError
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        error_str = str(e)
        
        # Handle specific OpenAI API errors
        error_message = error_str
        http_status = 500
        
        if isinstance(e, AuthenticationError):
            error_message = 'خطأ في المصادقة - تحقق من API Key / Authentication error - check your API Key'
            http_status = 401
        elif isinstance(e, RateLimitError):
            error_message = 'تم تجاوز حد الاستخدام - يرجى المحاولة لاحقاً / Rate limit exceeded - please try again later'
            http_status = 429
        elif 'insufficient_quota' in error_str.lower():
            error_message = 'حد الاستخدام قد تم تجاوزه - يرجى التحقق من حسابك في OpenAI وإضافة رصيد / Insufficient quota - please check your OpenAI account and add credits'
            http_status = 402
        elif isinstance(e, APIConnectionError):
            error_message = 'خطأ في الاتصال - تحقق من الإنترنت / Connection error - check your internet'
            http_status = 503
        elif isinstance(e, APIError):
            error_message = f'خطأ في API: {error_str} / API Error: {error_str}'
            http_status = 500
        
        # Log failed attempt
        failed_log = AILog(
            user_id=user_id,
            module='consultation',
            service_type=topic,
            provider_type='openai',
            model_name='gpt-3.5-turbo',
            prompt=message,
            response='',
            status='failed',
            error_message=error_str,
            execution_time_ms=execution_time_ms
        )
        db.session.add(failed_log)
        db.session.commit()
        
        return jsonify({'error': error_message}), http_status

@consultation_bp.route('/api/create-session', methods=['POST'])
@login_required
def create_session():
    """API endpoint to create a new consultation session"""
    db = current_app.extensions['sqlalchemy']
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    topic = data.get('topic', 'General Consultation')
    
    # Create new session
    chat_session = ChatSession(
        user_id=user_id,
        domain=topic,
        messages=json.dumps([])
    )
    db.session.add(chat_session)
    db.session.commit()
    
    return jsonify({
        'session_id': chat_session.id,
        'domain': chat_session.domain,
        'created_at': chat_session.created_at.isoformat()
    })

# ==================== STRATEGIC PLANNING SUBMODULE ====================

@consultation_bp.route('/strategic-planning')
@login_required
def strategic_planning_module():
    """Strategic Planning consulting submodule - entry point"""
    lang = session.get('language', 'ar')
    return redirect(url_for('strategic_planning_ai.index'))

@consultation_bp.route('/strategic-planning/create', methods=['GET', 'POST'])
@login_required
def strategic_planning_create():
    """Create new strategic plan through consultation"""
    return redirect(url_for('strategic_planning_ai.create_plan'))
