from flask import Blueprint, render_template, session, current_app
from utils.decorators import login_required

innovation_bp = Blueprint('innovation', __name__)

@innovation_bp.route('/')
@login_required
def index():
    lang = session.get('language', 'ar')
    return render_template('innovation/index.html', lang=lang)
