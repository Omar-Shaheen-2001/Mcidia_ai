from flask import Blueprint, render_template, session, jsonify, request, current_app, send_file
from flask_jwt_extended import get_jwt_identity
from utils.decorators import login_required, role_required
from models import User, ChatSession, AILog
from sqlalchemy import func
from datetime import datetime
import json
from io import BytesIO
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    HTML, CSS = None, None

consultations_bp = Blueprint('consultations_admin', __name__, url_prefix='/consultations')

def get_db():
    return current_app.extensions['sqlalchemy']

def get_lang():
    return session.get('language', 'ar')

@consultations_bp.route('/')
@login_required
@role_required('system_admin')
def index():
    """Admin Consultations - View all user consultations"""
    db = get_db()
    lang = get_lang()
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Query consultations with user info and costs - only users with consultations
    query = db.session.query(
        User.id,
        User.username,
        User.email,
        func.count(ChatSession.id).label('consultation_count'),
        func.sum(AILog.estimated_cost).label('total_cost')
    ).join(
        ChatSession, User.id == ChatSession.user_id
    ).outerjoin(
        AILog, (AILog.user_id == User.id) & (AILog.module == 'consultation')
    ).group_by(
        User.id, User.username, User.email
    ).order_by(
        func.count(ChatSession.id).desc()
    ).paginate(page=page, per_page=per_page)
    
    # Get overall statistics
    total_consultations = db.session.query(ChatSession).count()
    total_consultation_cost = db.session.query(func.sum(AILog.estimated_cost)).filter_by(module='consultation').scalar() or 0
    total_active_users = db.session.query(User).join(ChatSession).group_by(User.id).count()
    
    return render_template(
        'admin/consultations/index.html',
        lang=lang,
        users=query.items,
        pagination=query,
        total_consultations=total_consultations,
        total_consultation_cost=total_consultation_cost,
        total_active_users=total_active_users
    )

@consultations_bp.route('/user/<int:user_id>')
@login_required
@role_required('system_admin')
def user_consultations(user_id):
    """View consultations for a specific user"""
    db = get_db()
    lang = get_lang()
    
    user = db.session.query(User).get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get consultations for this user
    consultations = db.session.query(ChatSession).filter_by(
        user_id=user_id
    ).order_by(ChatSession.created_at.desc()).paginate(page=page, per_page=per_page)
    
    # Get user statistics
    total_consultations = db.session.query(ChatSession).filter_by(user_id=user_id).count()
    total_cost = db.session.query(func.sum(AILog.estimated_cost)).filter_by(user_id=user_id, module='consultation').scalar() or 0
    
    # Distribute total cost equally among consultations
    if total_consultations > 0:
        avg_cost_per_consultation = total_cost / total_consultations
    else:
        avg_cost_per_consultation = 0
    
    # Create cost map - all sessions get equal share of AI costs
    cost_map = {consultation.id: avg_cost_per_consultation for consultation in consultations.items}
    
    return render_template(
        'admin/consultations/user_consultations.html',
        lang=lang,
        user=user,
        consultations=consultations.items,
        pagination=consultations,
        cost_map=cost_map,
        total_consultations=total_consultations,
        total_cost=total_cost
    )

@consultations_bp.route('/session/<int:session_id>')
@login_required
@role_required('system_admin')
def view_session(session_id):
    """View details of a specific consultation session"""
    db = get_db()
    lang = get_lang()
    
    session_obj = db.session.query(ChatSession).get(session_id)
    if not session_obj:
        return jsonify({'error': 'Session not found'}), 404
    
    user = db.session.query(User).get(session_obj.user_id)
    
    # Get total AI usage cost for this user's consultations
    user_consultation_cost = db.session.query(
        func.sum(AILog.estimated_cost)
    ).filter_by(user_id=session_obj.user_id, module='consultation').scalar() or 0
    
    # Get total consultations count
    total_consultations = db.session.query(ChatSession).filter_by(user_id=session_obj.user_id).count()
    
    # Distribute cost equally among this user's consultations
    if total_consultations > 0:
        session_cost = user_consultation_cost / total_consultations
    else:
        session_cost = 0
    
    # Get AI logs for this user's consultations
    ai_logs = db.session.query(AILog).filter_by(
        user_id=session_obj.user_id, 
        module='consultation'
    ).order_by(AILog.created_at.desc()).limit(10).all()
    
    return render_template(
        'admin/consultations/session_detail.html',
        lang=lang,
        session=session_obj,
        user=user,
        session_cost=session_cost,
        ai_logs=ai_logs
    )

@consultations_bp.route('/session/<int:session_id>/export-pdf')
@login_required
@role_required('system_admin')
def export_session_pdf(session_id):
    """Export consultation session to PDF"""
    db = get_db()
    lang = get_lang()
    
    session_obj = db.session.query(ChatSession).get(session_id)
    if not session_obj:
        return jsonify({'error': 'Session not found'}), 404
    
    user = db.session.query(User).get(session_obj.user_id)
    
    # Get total AI usage cost
    user_consultation_cost = db.session.query(
        func.sum(AILog.estimated_cost)
    ).filter_by(user_id=session_obj.user_id, module='consultation').scalar() or 0
    
    total_consultations = db.session.query(ChatSession).filter_by(user_id=session_obj.user_id).count()
    session_cost = (user_consultation_cost / total_consultations) if total_consultations > 0 else 0
    
    # Parse messages
    messages = json.loads(session_obj.messages) if session_obj.messages else []
    message_count = len(messages)
    
    # Build HTML content
    direction = 'rtl' if lang == 'ar' else 'ltr'
    text_align = 'right' if lang == 'ar' else 'left'
    border_side = 'right' if lang == 'ar' else 'left'
    
    html_content = f"""
    <!DOCTYPE html>
    <html dir="{direction}" lang="{lang}">
    <head>
        <meta charset="UTF-8">
        <style>
            * {{
                font-family: Arial, sans-serif;
            }}
            body {{
                direction: {direction};
                text-align: {text_align};
                margin: 0;
                padding: 20px;
                background: #fff;
                line-height: 1.6;
            }}
            .header {{
                background: linear-gradient(135deg, #0d6efd 0%, #0a58ca 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
                font-weight: 700;
            }}
            .section {{
                margin-bottom: 25px;
            }}
            .section-title {{
                font-size: 16px;
                font-weight: 700;
                color: #28a745;
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 2px solid #28a745;
            }}
            .info-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 15px;
            }}
            .info-table tr {{
                border-bottom: 1px solid #e0e0e0;
            }}
            .info-table td {{
                padding: 12px;
                text-align: {text_align};
            }}
            .info-table td:first-child {{
                background: #f5f5f5;
                font-weight: 600;
                width: 25%;
            }}
            .stats-table {{
                width: 100%;
                background: #e7f3ff;
                border-collapse: collapse;
                margin-bottom: 15px;
            }}
            .stats-table tr {{
                border-bottom: 1px solid #b0d4ff;
            }}
            .stats-table td {{
                padding: 12px;
                text-align: {text_align};
            }}
            .stats-table td:first-child {{
                background: #cce5ff;
                font-weight: 600;
                width: 25%;
            }}
            .message {{
                margin-bottom: 15px;
                padding: 12px;
                border-radius: 8px;
                border-{border_side}: 4px solid;
            }}
            .message-user {{
                background: #f9f9f9;
                border-color: #0d6efd;
            }}
            .message-assistant {{
                background: #e7f3ff;
                border-color: #28a745;
            }}
            .message-header {{
                font-weight: 600;
                margin-bottom: 8px;
                font-size: 12px;
            }}
            .message-user .message-header {{
                color: #0d6efd;
            }}
            .message-assistant .message-header {{
                color: #28a745;
            }}
            .message-content {{
                color: #333;
                word-wrap: break-word;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                padding-top: 15px;
                border-top: 1px solid #e0e0e0;
                color: #999;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📋 {'تقرير تفاصيل جلسة الاستشارة' if lang == 'ar' else 'Consultation Session Report'}</h1>
        </div>
        
        <div class="section">
            <h2 class="section-title">📋 {'معلومات الجلسة' if lang == 'ar' else 'Session Information'}</h2>
            <table class="info-table">
                <tr>
                    <td>{'معرّف الجلسة:' if lang == 'ar' else 'Session ID:'}</td>
                    <td>{session_obj.id}</td>
                </tr>
                <tr>
                    <td>{'المستخدم:' if lang == 'ar' else 'User:'}</td>
                    <td>{user.username}</td>
                </tr>
                <tr>
                    <td>{'البريد الإلكتروني:' if lang == 'ar' else 'Email:'}</td>
                    <td>{user.email}</td>
                </tr>
                <tr>
                    <td>{'المجال:' if lang == 'ar' else 'Domain:'}</td>
                    <td>{session_obj.domain or 'General'}</td>
                </tr>
                <tr>
                    <td>{'التاريخ:' if lang == 'ar' else 'Date:'}</td>
                    <td>{session_obj.created_at.strftime('%d/%m/%Y %H:%M:%S') if session_obj.created_at else '-'}</td>
                </tr>
            </table>
        </div>
        
        <div class="section">
            <h2 class="section-title">📊 {'الإحصائيات' if lang == 'ar' else 'Statistics'}</h2>
            <table class="stats-table">
                <tr>
                    <td>{'التكلفة المقدرة:' if lang == 'ar' else 'Estimated Cost:'}</td>
                    <td>${session_cost:.4f}</td>
                </tr>
                <tr>
                    <td>{'عدد الرسائل:' if lang == 'ar' else 'Message Count:'}</td>
                    <td>{message_count}</td>
                </tr>
            </table>
        </div>
        
        {'<div class="section"><h2 class="section-title">💬 ' + ('محادثة الجلسة' if lang == 'ar' else 'Session Conversation') + '</h2>' if messages else ''}
    """
    
    # Add messages
    for msg in messages:
        role = msg.get('role', 'user') if isinstance(msg, dict) else 'user'
        content = msg.get('content', msg) if isinstance(msg, dict) else msg
        timestamp = msg.get('timestamp', '') if isinstance(msg, dict) else ''
        
        # Escape HTML in content
        content = str(content).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
        
        sender = ('المستخدم' if lang == 'ar' else 'User') if role == 'user' else ('المستشار الذكي' if lang == 'ar' else 'AI Assistant')
        timestamp_str = f'({timestamp[:19]})' if timestamp else ''
        
        msg_class = 'message-user' if role == 'user' else 'message-assistant'
        icon = '👤' if role == 'user' else '🤖'
        
        html_content += f"""
        <div class="message {msg_class}">
            <div class="message-header">{icon} {sender} {timestamp_str}</div>
            <div class="message-content">{content}</div>
        </div>
        """
    
    if messages:
        html_content += "</div>"
    
    html_content += f"""
        <div class="footer">
            {'تم التصدير في:' if lang == 'ar' else 'Exported on:'} {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </body>
    </html>
    """
    
    # Convert HTML to PDF using WeasyPrint
    try:
        pdf_bytes = HTML(string=html_content).write_pdf()
        pdf_buffer = BytesIO(pdf_bytes)
        
        # Generate filename
        filename = f'consultation-session-{session_id}-{datetime.utcnow().strftime("%Y%m%d-%H%M%S")}.pdf'
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500
