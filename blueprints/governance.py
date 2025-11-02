from flask import Blueprint, render_template, session, current_app
from utils.decorators import login_required

governance_bp = Blueprint('governance', __name__)

@governance_bp.route('/')
@login_required
def index():
    lang = session.get('language', 'ar')
    return render_template('governance/index.html', lang=lang)
