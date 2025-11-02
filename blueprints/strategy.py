from flask import Blueprint, render_template, session, current_app
from utils.decorators import login_required

strategy_bp = Blueprint('strategy', __name__)

@strategy_bp.route('/')
@login_required
def index():
    lang = session.get('language', 'ar')
    return render_template('strategy/index.html', lang=lang)
