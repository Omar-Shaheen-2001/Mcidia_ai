from flask import Blueprint, render_template, request, flash, session, redirect, url_for, current_app, jsonify
from flask_jwt_extended import get_jwt_identity
from utils.decorators import login_required
from models import AILog, ChatSession, Service
from datetime import datetime
import json
import openai
import os
import time

openai.api_key = os.getenv('OPENAI_API_KEY')

consultation_bp = Blueprint('consultation', __name__)

@consultation_bp.route('/')
def index():
    lang = session.get('language', 'ar')
    db = current_app.extensions['sqlalchemy']
    
    # Get available services for consultation topics
    services = db.session.query(Service).filter_by(is_active=True).all()
    
    return render_template('consultation/index.html', lang=lang, services=services)

@consultation_bp.route('/start')
@login_required
def start_session():
    """Start a new consultation session"""
    lang = session.get('language', 'ar')
    db = current_app.extensions['sqlalchemy']
    user_id = int(get_jwt_identity())
    
    # Get available services for topics
    services = db.session.query(Service).filter_by(is_active=True).all()
    
    return render_template('consultation/start.html', lang=lang, services=services)

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
    
    # Get available services
    services = db.session.query(Service).filter_by(is_active=True).all()
    
    return render_template(
        'consultation/session.html',
        lang=lang,
        session=chat_session,
        messages=messages,
        services=services
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
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message}]
        )
        
        ai_response = response.choices[0].message['content']
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Calculate estimated cost
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        estimated_cost = (input_tokens * 0.0015 / 1000) + (output_tokens * 0.002 / 1000)
        
        # Log AI usage
        log = AILog(
            user_id=user_id,
            module='consultation',
            service_type=topic,
            provider_type='openai',
            model_name='gpt-3.5-turbo',
            prompt=message,
            response=ai_response,
            tokens_used=response.usage.total_tokens,
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
        execution_time_ms = int((time.time() - start_time) * 1000)
        
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
            error_message=str(e),
            execution_time_ms=execution_time_ms
        )
        db.session.add(failed_log)
        db.session.commit()
        
        return jsonify({'error': str(e)}), 500

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
