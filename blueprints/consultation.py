from flask import Blueprint, render_template, request, flash, session, jsonify
from flask_jwt_extended import get_jwt_identity
from utils.decorators import login_required
from models import User, ChatSession, AILog
from app import db
from utils.ai_client import llm_chat
import json

consultation_bp = Blueprint('consultation', __name__)

@consultation_bp.route('/')
@login_required
def index():
    user_id = get_jwt_identity()
    sessions = ChatSession.query.filter_by(user_id=user_id).order_by(ChatSession.updated_at.desc()).all()
    lang = session.get('language', 'ar')
    return render_template('consultation/index.html', sessions=sessions, lang=lang)

@consultation_bp.route('/chat/<domain>', methods=['GET', 'POST'])
@login_required
def chat(domain):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    lang = session.get('language', 'ar')
    
    # Get or create chat session
    chat_session = ChatSession.query.filter_by(user_id=user_id, domain=domain).order_by(ChatSession.updated_at.desc()).first()
    
    if not chat_session:
        chat_session = ChatSession(
            user_id=user_id,
            domain=domain,
            messages=json.dumps([])
        )
        db.session.add(chat_session)
        db.session.commit()
    
    if request.method == 'POST':
        user_message = request.form.get('message')
        
        # Load existing messages
        messages = json.loads(chat_session.messages) if chat_session.messages else []
        
        # Determine domain-specific system prompt
        domain_prompts = {
            'strategy': 'أنت مستشار استراتيجي خبير / You are an expert strategic consultant',
            'hr': 'أنت خبير موارد بشرية / You are an HR expert',
            'finance': 'أنت مستشار مالي محترف / You are a professional financial consultant',
            'quality': 'أنت خبير في الجودة والحوكمة / You are a quality and governance expert',
            'governance': 'أنت خبير في الحوكمة المؤسسية / You are a corporate governance expert'
        }
        
        system_prompt = domain_prompts.get(domain, 'أنت مستشار محترف / You are a professional consultant')
        
        # Get AI response
        ai_response = llm_chat(system_prompt, user_message)
        
        # Append messages
        messages.append({'role': 'user', 'content': user_message})
        messages.append({'role': 'assistant', 'content': ai_response})
        
        # Update session
        chat_session.messages = json.dumps(messages)
        db.session.commit()
        
        # Log AI usage
        ai_log = AILog(
            user_id=user_id,
            module='consultation',
            prompt=user_message[:500],
            response=ai_response[:500],
            tokens_used=int(len(ai_response.split()) * 1.3)
        )
        db.session.add(ai_log)
        user.ai_credits_used += int(len(ai_response.split()) * 1.3)
        db.session.commit()
        
        return jsonify({'response': ai_response})
    
    messages = json.loads(chat_session.messages) if chat_session.messages else []
    return render_template('consultation/chat.html', domain=domain, messages=messages, lang=lang)
