from flask import Blueprint, render_template, session, current_app
from utils.decorators import login_required

marketing_bp = Blueprint('marketing', __name__)

@marketing_bp.route('/')
@login_required
def index():
    lang = session.get('language', 'ar')
    return render_template('marketing/index.html', lang=lang)
