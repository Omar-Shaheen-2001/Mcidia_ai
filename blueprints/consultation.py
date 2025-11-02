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
    db = current_app.extensions['sqlalchemy']
    user_id = int(get_jwt_identity())
    message = request.form.get('message')
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message}]
        )
        
        ai_response = response.choices[0].message['content']
        
        # Log AI usage
        log = AILog(
            user_id=user_id,
            module='consultation',
            prompt=message,
            response=ai_response,
            tokens_used=response.usage.total_tokens
        )
        db.session.add(log)
        db.session.commit()
        
        return {'response': ai_response}
    except Exception as e:
        return {'error': str(e)}, 500
