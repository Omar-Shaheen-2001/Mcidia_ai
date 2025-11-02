from flask import Blueprint, render_template, session, current_app
from utils.decorators import login_required

hr_bp = Blueprint('hr', __name__)

@hr_bp.route('/')
@login_required
def index():
    lang = session.get('language', 'ar')
    return render_template('hr/index.html', lang=lang)
