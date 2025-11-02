from flask import Blueprint, render_template, session, current_app
from utils.decorators import login_required

knowledge_bp = Blueprint('knowledge', __name__)

@knowledge_bp.route('/')
@login_required
def index():
    lang = session.get('language', 'ar')
    return render_template('knowledge/index.html', lang=lang)
