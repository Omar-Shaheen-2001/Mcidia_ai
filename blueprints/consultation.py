from flask import Blueprint, render_template, request, flash, session, redirect, url_for, current_app
from flask_jwt_extended import get_jwt_identity
from utils.decorators import login_required
from models import AILog
import openai
import os

openai.api_key = os.getenv('OPENAI_API_KEY')

consultation_bp = Blueprint('consultation', __name__)

@consultation_bp.route('/')
@login_required
def index():
    lang = session.get('language', 'ar')
    return render_template('consultation/index.html', lang=lang)

@consultation_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    import time
    start_time = time.time()
    
    db = current_app.extensions['sqlalchemy']
    user_id = int(get_jwt_identity())
    message = request.form.get('message')
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message}]
        )
        
        ai_response = response.choices[0].message['content']
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Calculate estimated cost (gpt-3.5-turbo: $0.0015 per 1K input, $0.002 per 1K output)
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        estimated_cost = (input_tokens * 0.0015 / 1000) + (output_tokens * 0.002 / 1000)
        
        # Log AI usage with comprehensive details
        log = AILog(
            user_id=user_id,
            module='consultation',
            service_type='General Consultation',
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
        db.session.commit()
        
        return {'response': ai_response}
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Log failed attempt
        failed_log = AILog(
            user_id=user_id,
            module='consultation',
            service_type='General Consultation',
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
        
        return {'error': str(e)}, 500
