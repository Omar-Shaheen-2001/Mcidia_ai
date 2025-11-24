from flask import Blueprint, render_template, session, jsonify, request, current_app, send_file
from flask_jwt_extended import get_jwt_identity
from utils.decorators import login_required, role_required
from models import User, ChatSession, AILog
from sqlalchemy import func
from datetime import datetime
import json
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.pdfgen import canvas

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
    
    # Query consultations with user info and costs
    query = db.session.query(
        User.id,
        User.username,
        User.email,
        func.count(ChatSession.id).label('consultation_count'),
        func.sum(AILog.estimated_cost).label('total_cost')
    ).outerjoin(
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
    
    # Create PDF
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0d6efd'),
        spaceAfter=12,
        alignment=1 if lang == 'ar' else 0
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#28a745'),
        spaceAfter=10,
        spaceBefore=10,
        alignment=1 if lang == 'ar' else 0
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        alignment=1 if lang == 'ar' else 0,
        textColor=colors.HexColor('#333333')
    )
    
    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#666666'),
        alignment=1 if lang == 'ar' else 0
    )
    
    # Build PDF content
    story = []
    
    # Title
    title = 'تقرير تفاصيل جلسة الاستشارة' if lang == 'ar' else 'Consultation Session Report'
    story.append(Paragraph(f'🔹 {title}', title_style))
    story.append(Spacer(1, 10*mm))
    
    # Session Information
    story.append(Paragraph('📋 معلومات الجلسة' if lang == 'ar' else '📋 Session Information', heading_style))
    
    info_data = [
        ['معرّف الجلسة:', str(session_obj.id)] if lang == 'ar' else ['Session ID:', str(session_obj.id)],
        ['المستخدم:', user.username] if lang == 'ar' else ['User:', user.username],
        ['البريد الإلكتروني:', user.email] if lang == 'ar' else ['Email:', user.email],
        ['المجال:', session_obj.domain or 'General'] if lang == 'ar' else ['Domain:', session_obj.domain or 'General'],
        ['التاريخ:', session_obj.created_at.strftime('%d/%m/%Y %H:%M:%S')] if lang == 'ar' else ['Date:', session_obj.created_at.strftime('%d/%m/%Y %H:%M:%S')],
    ]
    
    info_table = Table(info_data, colWidths=[60*mm, 110*mm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT' if lang == 'ar' else 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 8*mm))
    
    # Statistics
    story.append(Paragraph('📊 الإحصائيات' if lang == 'ar' else '📊 Statistics', heading_style))
    
    stats_data = [
        ['التكلفة المقدرة:', f'${session_cost:.4f}'] if lang == 'ar' else ['Estimated Cost:', f'${session_cost:.4f}'],
        ['عدد الرسائل:', str((json.loads(session_obj.messages) if session_obj.messages else []).__len__())] if lang == 'ar' else ['Message Count:', str((json.loads(session_obj.messages) if session_obj.messages else []).__len__())],
    ]
    
    stats_table = Table(stats_data, colWidths=[60*mm, 110*mm])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e7f3ff')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT' if lang == 'ar' else 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 12*mm))
    
    # Conversation
    if session_obj.messages:
        story.append(Paragraph('💬 محادثة الجلسة' if lang == 'ar' else '💬 Session Conversation', heading_style))
        
        messages = json.loads(session_obj.messages) if session_obj.messages else []
        for msg in messages:
            role = msg.get('role', 'user') if isinstance(msg, dict) else 'user'
            content = msg.get('content', msg) if isinstance(msg, dict) else msg
            timestamp = msg.get('timestamp', '') if isinstance(msg, dict) else ''
            
            sender = 'المستخدم' if lang == 'ar' else 'User' if role == 'user' else 'المستشار الذكي' if lang == 'ar' else 'AI Assistant'
            
            header = f'👤 {sender}'
            if timestamp:
                ts = timestamp[:19] if len(timestamp) > 19 else timestamp
                header += f' ({ts})'
            
            story.append(Paragraph(header, ParagraphStyle(
                'MsgHeader',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#0d6efd' if role == 'user' else '#28a745'),
                spaceAfter=4,
                alignment=1 if lang == 'ar' else 0
            )))
            
            story.append(Paragraph(content, normal_style))
            story.append(Spacer(1, 6*mm))
    
    # Build PDF
    doc.build(story)
    pdf_buffer.seek(0)
    
    # Generate filename
    filename = f'consultation-session-{session_id}-{datetime.utcnow().strftime("%Y%m%d-%H%M%S")}.pdf'
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )
