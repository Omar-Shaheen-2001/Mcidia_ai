from flask import Blueprint, render_template, session, current_app
from utils.decorators import login_required

finance_bp = Blueprint('finance', __name__)

@finance_bp.route('/')
@login_required
def index():
    lang = session.get('language', 'ar')
    return render_template('finance/index.html', lang=lang)
