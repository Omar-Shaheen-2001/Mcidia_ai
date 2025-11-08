"""
Strategic Identity Development Module
AI-powered comprehensive organizational identity building
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from flask_jwt_extended import get_jwt_identity
from utils.decorators import login_required
from models import StrategicIdentityProject, StrategicObjective, IdentityKPI, IdentityInitiative
from utils.ai_providers.ai_manager import AIManager
from werkzeug.utils import secure_filename
import json
import os
from datetime import datetime

strategic_identity_bp = Blueprint('strategic_identity', __name__)

UPLOAD_FOLDER = 'static/uploads/strategic_identity'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'xlsx', 'xls', 'txt'}

def get_db():
    """Get database instance"""
    return current_app.extensions['sqlalchemy']

def get_lang():
    """Get current language from session"""
    return session.get('language', 'ar')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==================== DASHBOARD ====================

@strategic_identity_bp.route('/')
@login_required
def index():
    """Strategic Identity dashboard - list all projects"""
    db = get_db()
    lang = get_lang()
    user_id = int(get_jwt_identity())
    
    # Get all projects for current user
    projects = db.session.query(StrategicIdentityProject).filter_by(user_id=user_id).order_by(StrategicIdentityProject.updated_at.desc()).all()
    
    return render_template('strategic_identity/index.html', 
                         projects=projects, 
                         lang=lang)

# ==================== CREATE NEW PROJECT ====================

@strategic_identity_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_project():
    """Create new strategic identity project"""
    db = get_db()
    lang = get_lang()
    user_id = int(get_jwt_identity())
    
    if request.method == 'GET':
        return render_template('strategic_identity/create.html', lang=lang)
    
    try:
        # Extract form data
        organization_name = request.form.get('organization_name')
        sector = request.form.get('sector')
        employee_count = int(request.form.get('employee_count', 0))
        location = request.form.get('location')
        description = request.form.get('description')
        current_objectives = request.form.get('current_objectives')
        ongoing_initiatives = request.form.get('ongoing_initiatives')
        
        # Handle file uploads
        uploaded_files = []
        if 'files' in request.files:
            files = request.files.getlist('files')
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
            for file in files:
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(filepath)
                    uploaded_files.append(filepath)
        
        # Create project record
        project = StrategicIdentityProject(
            user_id=user_id,
            organization_name=organization_name,
            sector=sector,
            employee_count=employee_count,
            location=location,
            description=description,
            current_objectives=current_objectives,
            ongoing_initiatives=ongoing_initiatives,
            uploaded_files=json.dumps(uploaded_files) if uploaded_files else None,
            status='draft'
        )
        
        db.session.add(project)
        db.session.commit()
        
        flash(f'تم إنشاء المشروع "{organization_name}" بنجاح / Project created successfully' if lang == 'ar' else f'Project "{organization_name}" created successfully', 'success')
        
        # Redirect to analysis generation
        return redirect(url_for('strategic_identity.generate_analysis', project_id=project.id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating project: {str(e)}")
        flash(f'خطأ في إنشاء المشروع: {str(e)} / Error creating project: {str(e)}' if lang == 'ar' else f'Error creating project: {str(e)}', 'danger')
        return redirect(url_for('strategic_identity.create_project'))

# ==================== AI ANALYSIS GENERATION ====================

@strategic_identity_bp.route('/project/<int:project_id>/generate-analysis', methods=['GET', 'POST'])
@login_required
def generate_analysis(project_id):
    """Generate AI-powered strategic analysis"""
    db = get_db()
    lang = get_lang()
    user_id = int(get_jwt_identity())
    
    # Authorization check
    project = db.session.query(StrategicIdentityProject).filter_by(id=project_id).first_or_404()
    if project.user_id != user_id:
        flash('غير مصرح لك بالوصول لهذا المشروع / Unauthorized access', 'danger')
        return redirect(url_for('strategic_identity.index'))
    
    if request.method == 'GET':
        return render_template('strategic_identity/generate_analysis.html', 
                             project=project,
                             lang=lang)
    
    try:
        ai_manager = AIManager()
        
        # Build context for AI
        context = f"""
منظمة: {project.organization_name}
القطاع: {project.sector}
عدد الموظفين: {project.employee_count}
الموقع: {project.location}
الوصف: {project.description}
الأهداف الحالية: {project.current_objectives}
المبادرات الجارية: {project.ongoing_initiatives}
"""
        
        # Generate SWOT Analysis
        swot_prompt = f"""أنت خبير استراتيجي. قم بتحليل SWOT شامل للمنظمة التالية:

{context}

قدم تحليل SWOT بصيغة JSON كالتالي:
{{
    "strengths": ["نقطة قوة 1", "نقطة قوة 2", ...],
    "weaknesses": ["نقطة ضعف 1", "نقطة ضعف 2", ...],
    "opportunities": ["فرصة 1", "فرصة 2", ...],
    "threats": ["تهديد 1", "تهديد 2", ...]
}}

قدم على الأقل 5 نقاط لكل عنصر."""

        swot_response = ai_manager.generate(
            prompt=swot_prompt,
            use_case='strategic_analysis',
            max_tokens=2000
        )
        
        # Generate Vision & Mission
        identity_prompt = f"""أنت خبير في بناء الهوية الاستراتيجية. بناءً على المعلومات التالية:

{context}

أنشئ:
1. رؤية ملهمة (Vision) - جملة واحدة طموحة
2. رسالة واضحة (Mission) - فقرة مختصرة تصف الهدف الأساسي
3. 5 قيم جوهرية (Core Values) مع وصف مختصر لكل قيمة
4. 4 مجالات استراتيجية رئيسية (Strategic Themes)

قدم النتيجة بصيغة JSON:
{{
    "vision": "الرؤية هنا...",
    "mission": "الرسالة هنا...",
    "core_values": [
        {{"value": "النزاهة", "description": "وصف مختصر"}},
        ...
    ],
    "strategic_themes": ["مجال 1", "مجال 2", ...]
}}"""

        identity_response = ai_manager.generate(
            prompt=identity_prompt,
            use_case='strategic_analysis',
            max_tokens=2000
        )
        
        # Parse responses
        try:
            swot_data = json.loads(swot_response)
            identity_data = json.loads(identity_response)
        except json.JSONDecodeError:
            # Fallback: try to extract JSON from response
            import re
            swot_match = re.search(r'\{.*\}', swot_response, re.DOTALL)
            identity_match = re.search(r'\{.*\}', identity_response, re.DOTALL)
            
            swot_data = json.loads(swot_match.group(0)) if swot_match else {}
            identity_data = json.loads(identity_match.group(0)) if identity_match else {}
        
        # Update project with AI-generated data
        project.swot_analysis = json.dumps(swot_data, ensure_ascii=False)
        project.vision_statement = identity_data.get('vision', '')
        project.mission_statement = identity_data.get('mission', '')
        project.core_values = json.dumps(identity_data.get('core_values', []), ensure_ascii=False)
        project.strategic_themes = json.dumps(identity_data.get('strategic_themes', []), ensure_ascii=False)
        project.status = 'analysis_complete'
        project.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('تم إنشاء التحليل الاستراتيجي بنجاح / Strategic analysis generated successfully', 'success')
        return redirect(url_for('strategic_identity.project_dashboard', project_id=project.id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error generating analysis: {str(e)}")
        flash(f'خطأ في إنشاء التحليل: {str(e)} / Error generating analysis: {str(e)}', 'danger')
        return redirect(url_for('strategic_identity.generate_analysis', project_id=project_id))

# ==================== PROJECT DASHBOARD ====================

@strategic_identity_bp.route('/project/<int:project_id>')
@login_required
def project_dashboard(project_id):
    """View strategic identity project dashboard"""
    db = get_db()
    lang = get_lang()
    user_id = int(get_jwt_identity())
    
    # Authorization check
    project = db.session.query(StrategicIdentityProject).filter_by(id=project_id).first_or_404()
    if project.user_id != user_id:
        flash('غير مصرح لك بالوصول لهذا المشروع / Unauthorized access', 'danger')
        return redirect(url_for('strategic_identity.index'))
    
    # Parse JSON data
    swot = json.loads(project.swot_analysis) if project.swot_analysis else {}
    pestel = json.loads(project.pestel_analysis) if project.pestel_analysis else {}
    values = json.loads(project.core_values) if project.core_values else []
    themes = json.loads(project.strategic_themes) if project.strategic_themes else []
    
    # Get related data
    objectives = db.session.query(StrategicObjective).filter_by(project_id=project_id).all()
    kpis = db.session.query(IdentityKPI).filter_by(project_id=project_id).all()
    initiatives = db.session.query(IdentityInitiative).filter_by(project_id=project_id).all()
    
    return render_template('strategic_identity/dashboard.html',
                         project=project,
                         swot=swot,
                         pestel=pestel,
                         values=values,
                         themes=themes,
                         objectives=objectives,
                         kpis=kpis,
                         initiatives=initiatives,
                         lang=lang)
