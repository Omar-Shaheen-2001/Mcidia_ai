from flask import Blueprint, render_template, request, flash, session, redirect, url_for, current_app, jsonify
from flask_jwt_extended import get_jwt_identity
from utils.decorators import login_required
from models import AILog, ChatSession, Service
from utils.ai_providers.ai_manager import AIManager
from datetime import datetime
from werkzeug.utils import secure_filename
import json
import time
import os

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
        
        # Get chart generation instructions
        try:
            from utils.chart_generator import get_ai_chart_instructions
            chart_instructions = get_ai_chart_instructions('ar' if any(ord(c) > 127 for c in message) else 'en')
        except:
            chart_instructions = ""
        
        system_prompt = f"""أنت مستشار خبير متخصص في مجال {topic}.
تقدّم استشارات عملية وقيّمة وقابلة للتطبيق.
كن موجزاً وفعالاً في إجابتك.
الرد بالعربية إذا كانت الأسئلة بالعربية، والإنجليزية إذا كانت بالإنجليزية.

{chart_instructions}"""
        
        augmented_message = f"{rag_context}\n\n**السؤال:** {message}" if rag_context else message
        ai_response = ai.chat(system_prompt, augmented_message)
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Extract charts from AI response
        charts = []
        cleaned_response = ai_response
        try:
            from utils.chart_generator import process_ai_response_for_charts
            cleaned_response, charts = process_ai_response_for_charts(ai_response)
        except:
            pass
        
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
            'content': cleaned_response,
            'timestamp': datetime.utcnow().isoformat(),
            'cost': estimated_cost,
            'charts': charts if charts else None
        })
        
        chat_session.messages = json.dumps(messages)
        chat_session.updated_at = datetime.utcnow()
        
        if not session_id:
            db.session.add(chat_session)
        
        db.session.commit()
        
        return jsonify({
            'response': cleaned_response,
            'charts': charts if charts else [],
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

# ==================== DOCUMENT UPLOAD FOR AI ANALYSIS ====================

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    """Extract text from PDF file using PyPDF2"""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        current_app.logger.error(f"PDF extraction error: {str(e)}")
        return None

def extract_text_from_docx(file_path):
    """Extract text from Word document using python-docx"""
    try:
        from docx import Document
        doc = Document(file_path)
        text = ""
        for para in doc.paragraphs:
            if para.text:
                text += para.text + "\n"
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text:
                        text += cell.text + " "
                text += "\n"
        return text.strip()
    except Exception as e:
        current_app.logger.error(f"DOCX extraction error: {str(e)}")
        return None

def extract_text_from_txt(file_path):
    """Extract text from plain text file"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read().strip()
    except Exception as e:
        current_app.logger.error(f"TXT extraction error: {str(e)}")
        return None

@consultation_bp.route('/api/upload-document', methods=['POST'])
@login_required
def upload_document():
    """API endpoint to upload and extract text from documents for AI analysis"""
    user_id = int(get_jwt_identity())
    
    # Check if file was uploaded
    if 'document' not in request.files:
        return jsonify({'success': False, 'error': 'لم يتم تحميل ملف / No file uploaded'}), 400
    
    file = request.files['document']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'لم يتم اختيار ملف / No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'نوع الملف غير مدعوم. يرجى استخدام PDF, Word, أو TXT / File type not supported. Please use PDF, Word, or TXT'}), 400
    
    # Check file size
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return jsonify({'success': False, 'error': 'حجم الملف كبير جداً (أقصى 10MB) / File too large (max 10MB)'}), 400
    
    try:
        # Secure filename and save
        filename = secure_filename(file.filename)
        timestamp = int(time.time())
        unique_filename = f"{user_id}_{timestamp}_{filename}"
        
        # Create upload directory if not exists
        upload_dir = os.path.join(current_app.root_path, 'uploads', 'documents', 'consultation')
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Extract text based on file type
        extension = filename.rsplit('.', 1)[1].lower()
        extracted_text = None
        
        if extension == 'pdf':
            extracted_text = extract_text_from_pdf(file_path)
        elif extension in ['doc', 'docx']:
            extracted_text = extract_text_from_docx(file_path)
        elif extension == 'txt':
            extracted_text = extract_text_from_txt(file_path)
        
        # Clean up file after extraction
        try:
            os.remove(file_path)
        except:
            pass
        
        if not extracted_text:
            return jsonify({
                'success': False,
                'error': 'فشل استخراج النص من الملف / Failed to extract text from file'
            }), 500
        
        # Truncate if too long (max 15000 characters for context)
        max_length = 15000
        if len(extracted_text) > max_length:
            extracted_text = extracted_text[:max_length] + "\n... [تم اقتطاع النص بسبب الطول / Text truncated due to length]"
        
        # Create preview (first 500 characters)
        preview = extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text
        
        return jsonify({
            'success': True,
            'filename': filename,
            'content': extracted_text,
            'preview': preview,
            'length': len(extracted_text)
        })
        
    except Exception as e:
        current_app.logger.error(f"Document upload error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'خطأ في معالجة الملف / Error processing file: {str(e)}'
        }), 500

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
