from flask import Blueprint, render_template, session, request, redirect, url_for

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Get language from session or default to Arabic
    lang = session.get('language', 'ar')
    return render_template('index.html', lang=lang)

@main_bp.route('/set-language/<lang>')
def set_language(lang):
    if lang in ['ar', 'en']:
        session['language'] = lang
    return redirect(request.referrer or url_for('main.index'))
