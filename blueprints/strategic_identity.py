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
        # Create AI provider for strategic analysis
        ai = AIManager.for_use_case('strategic_analysis')
        
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

        swot_response = ai.chat(
            prompt=swot_prompt,
            temperature=0.7,
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

        identity_response = ai.chat(
            prompt=identity_prompt,
            temperature=0.7,
            max_tokens=2000
        )
        
        # Generate Strategic Objectives
        objectives_prompt = f"""أنت خبير في التخطيط الاستراتيجي. بناءً على المعلومات التالية:

{context}

أنشئ 5 أهداف استراتيجية SMART (محددة، قابلة للقياس، قابلة للتحقيق، ذات صلة، محددة بزمن):

قدم النتيجة بصيغة JSON:
{{
    "objectives": [
        {{
            "name": "اسم الهدف",
            "description": "وصف تفصيلي للهدف",
            "timeframe": "الإطار الزمني (مثال: 2024-2025)"
        }},
        ...
    ]
}}"""

        objectives_response = ai.chat(
            prompt=objectives_prompt,
            temperature=0.7,
            max_tokens=1500
        )
        
        # Generate Strategic Initiatives
        initiatives_prompt = f"""أنت خبير في إدارة المشاريع الاستراتيجية. بناءً على المعلومات التالية:

{context}

أنشئ 5 مبادرات تنفيذية استراتيجية، كل مبادرة يجب أن تحتوي على:
- اسم المبادرة
- الهدف المرتبط بها
- المخرجات المتوقعة
- فترة التنفيذ
- الجهة المسؤولة (قسم أو فريق)

قدم النتيجة بصيغة JSON:
{{
    "initiatives": [
        {{
            "name": "اسم المبادرة",
            "objective": "الهدف المرتبط",
            "expected_outputs": "المخرجات المتوقعة",
            "implementation_period": "فترة التنفيذ (مثال: 6 أشهر)",
            "responsible_party": "الجهة المسؤولة",
            "budget": 50000,
            "description": "وصف مختصر للمبادرة"
        }},
        ...
    ]
}}"""

        initiatives_response = ai.chat(
            prompt=initiatives_prompt,
            temperature=0.7,
            max_tokens=2000
        )
        
        # Helper function to clean and parse JSON
        def clean_and_parse_json(response_text):
            import re
            # Remove markdown code blocks
            cleaned = re.sub(r'```json\s*', '', response_text)
            cleaned = re.sub(r'```\s*', '', cleaned)
            # Remove control characters
            cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', cleaned)
            # Try to extract JSON object
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            return {}
        
        # Parse responses
        swot_data = clean_and_parse_json(swot_response)
        identity_data = clean_and_parse_json(identity_response)
        objectives_data = clean_and_parse_json(objectives_response)
        initiatives_data = clean_and_parse_json(initiatives_response)
        
        # Update project with AI-generated data
        project.swot_analysis = json.dumps(swot_data, ensure_ascii=False)
        project.vision_statement = identity_data.get('vision', '')
        project.mission_statement = identity_data.get('mission', '')
        project.core_values = json.dumps(identity_data.get('core_values', []), ensure_ascii=False)
        project.strategic_themes = json.dumps(identity_data.get('strategic_themes', []), ensure_ascii=False)
        project.status = 'analysis_complete'
        project.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Save Strategic Objectives
        for obj_data in objectives_data.get('objectives', []):
            objective = StrategicObjective(
                project_id=project.id,
                title=obj_data.get('name', ''),
                description=obj_data.get('description', ''),
                timeframe=obj_data.get('timeframe', ''),
                priority='high'
            )
            db.session.add(objective)
        
        # Save Strategic Initiatives
        for init_data in initiatives_data.get('initiatives', []):
            initiative = IdentityInitiative(
                project_id=project.id,
                name=init_data.get('name', ''),
                expected_outputs=init_data.get('expected_outputs', '') + "\n\nالهدف المرتبط: " + init_data.get('objective', ''),
                implementation_period=init_data.get('implementation_period', ''),
                responsible_party=init_data.get('responsible_party', ''),
                budget_estimate=init_data.get('budget', 0)
            )
            db.session.add(initiative)
        
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

# ==================== EXPORT FUNCTIONS ====================

@strategic_identity_bp.route('/project/<int:project_id>/export/pdf')
@login_required
def export_pdf(project_id):
    """Export strategic identity to PDF using WeasyPrint"""
    from flask import make_response
    from .pdf_export_weasy import generate_pdf_weasy
    
    db = get_db()
    user_id = int(get_jwt_identity())
    
    # Authorization check
    project = db.session.query(StrategicIdentityProject).filter_by(id=project_id).first_or_404()
    if project.user_id != user_id:
        flash('غير مصرح / Unauthorized', 'danger')
        return redirect(url_for('strategic_identity.index'))
    
    # Parse JSON data
    swot = json.loads(project.swot_analysis) if project.swot_analysis else {}
    values = json.loads(project.core_values) if project.core_values else []
    themes = json.loads(project.strategic_themes) if project.strategic_themes else []
    
    # Get related data
    objectives = db.session.query(StrategicObjective).filter_by(project_id=project_id).all()
    initiatives = db.session.query(IdentityInitiative).filter_by(project_id=project_id).all()
    
    # Generate PDF using WeasyPrint
    pdf = generate_pdf_weasy(project, objectives, initiatives, swot, values, themes)
    
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=strategic_identity_{project_id}.pdf'
    
    return response

@strategic_identity_bp.route('/project/<int:project_id>/export/excel')
@login_required
def export_excel(project_id):
    """Export strategic identity to Excel"""
    from flask import make_response
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill
    from io import BytesIO
    
    db = get_db()
    user_id = int(get_jwt_identity())
    
    # Authorization check
    project = db.session.query(StrategicIdentityProject).filter_by(id=project_id).first_or_404()
    if project.user_id != user_id:
        flash('غير مصرح / Unauthorized', 'danger')
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
    
    # Create workbook
    wb = Workbook()
    
    # Overview Sheet
    ws_overview = wb.active
    ws_overview.title = "Overview"
    ws_overview.sheet_view.rightToLeft = True
    
    header_fill = PatternFill(start_color="0066CC", end_color="0066CC", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=14)
    subheader_font = Font(bold=True, size=12)
    
    ws_overview['A1'] = "الهوية الاستراتيجية"
    ws_overview['A1'].font = header_font
    ws_overview['A1'].fill = header_fill
    ws_overview.merge_cells('A1:B1')
    
    row = 3
    ws_overview[f'A{row}'] = "اسم المؤسسة"
    ws_overview[f'B{row}'] = project.organization_name
    row += 1
    ws_overview[f'A{row}'] = "القطاع"
    ws_overview[f'B{row}'] = project.sector
    row += 1
    ws_overview[f'A{row}'] = "عدد الموظفين"
    ws_overview[f'B{row}'] = project.employee_count
    row += 2
    
    if project.vision_statement:
        ws_overview[f'A{row}'] = "الرؤية"
        ws_overview[f'A{row}'].font = Font(bold=True)
        row += 1
        ws_overview[f'A{row}'] = project.vision_statement
        ws_overview.merge_cells(f'A{row}:B{row}')
        row += 2
    
    if project.mission_statement:
        ws_overview[f'A{row}'] = "الرسالة"
        ws_overview[f'A{row}'].font = Font(bold=True)
        row += 1
        ws_overview[f'A{row}'] = project.mission_statement
        ws_overview.merge_cells(f'A{row}:B{row}')
        row += 2
    
    ws_overview.column_dimensions['A'].width = 20
    ws_overview.column_dimensions['B'].width = 50
    
    # SWOT Sheet
    if swot:
        ws_swot = wb.create_sheet("SWOT Analysis")
        ws_swot.sheet_view.rightToLeft = True
        
        ws_swot['A1'] = "تحليل SWOT"
        ws_swot['A1'].font = header_font
        ws_swot['A1'].fill = header_fill
        ws_swot.merge_cells('A1:D1')
        
        ws_swot['A3'] = "نقاط القوة"
        ws_swot['B3'] = "نقاط الضعف"
        ws_swot['C3'] = "الفرص"
        ws_swot['D3'] = "التهديدات"
        
        for cell in ['A3', 'B3', 'C3', 'D3']:
            ws_swot[cell].font = Font(bold=True)
            ws_swot[cell].fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        
        row = 4
        max_items = max(
            len(swot.get('strengths', [])),
            len(swot.get('weaknesses', [])),
            len(swot.get('opportunities', [])),
            len(swot.get('threats', []))
        )
        
        for i in range(max_items):
            strengths = swot.get('strengths', [])
            weaknesses = swot.get('weaknesses', [])
            opportunities = swot.get('opportunities', [])
            threats = swot.get('threats', [])
            
            ws_swot[f'A{row}'] = strengths[i] if i < len(strengths) else ""
            ws_swot[f'B{row}'] = weaknesses[i] if i < len(weaknesses) else ""
            ws_swot[f'C{row}'] = opportunities[i] if i < len(opportunities) else ""
            ws_swot[f'D{row}'] = threats[i] if i < len(threats) else ""
            row += 1
        
        for col in ['A', 'B', 'C', 'D']:
            ws_swot.column_dimensions[col].width = 30
    
    # Core Values Sheet
    if values:
        ws_values = wb.create_sheet("Core Values")
        ws_values.sheet_view.rightToLeft = True
        
        ws_values['A1'] = "القيم المؤسسية"
        ws_values['A1'].font = header_font
        ws_values['A1'].fill = header_fill
        ws_values.merge_cells('A1:B1')
        
        ws_values['A3'] = "القيمة"
        ws_values['B3'] = "الوصف"
        ws_values['A3'].font = Font(bold=True)
        ws_values['B3'].font = Font(bold=True)
        
        row = 4
        for value in values:
            # Handle both dict and string formats
            if isinstance(value, dict):
                ws_values[f'A{row}'] = value.get('value', '')
                ws_values[f'B{row}'] = value.get('description', '')
            else:
                ws_values[f'A{row}'] = str(value)
                ws_values[f'B{row}'] = ''
            row += 1
        
        ws_values.column_dimensions['A'].width = 20
        ws_values.column_dimensions['B'].width = 50
    
    # Strategic Themes Sheet
    if themes:
        ws_themes = wb.create_sheet("Strategic Themes")
        ws_themes.sheet_view.rightToLeft = True
        
        ws_themes['A1'] = "المجالات الاستراتيجية"
        ws_themes['A1'].font = header_font
        ws_themes['A1'].fill = header_fill
        ws_themes.merge_cells('A1:B1')
        
        ws_themes['A3'] = "المجال"
        ws_themes['B3'] = "الوصف"
        ws_themes['A3'].font = Font(bold=True)
        ws_themes['B3'].font = Font(bold=True)
        
        row = 4
        for theme in themes:
            # Handle both dict and string formats
            if isinstance(theme, dict):
                ws_themes[f'A{row}'] = theme.get('theme', '')
                ws_themes[f'B{row}'] = theme.get('description', '')
            else:
                ws_themes[f'A{row}'] = str(theme)
                ws_themes[f'B{row}'] = ''
            row += 1
        
        ws_themes.column_dimensions['A'].width = 25
        ws_themes.column_dimensions['B'].width = 50
    
    # PESTEL Analysis Sheet
    if pestel:
        ws_pestel = wb.create_sheet("PESTEL Analysis")
        ws_pestel.sheet_view.rightToLeft = True
        
        ws_pestel['A1'] = "تحليل PESTEL"
        ws_pestel['A1'].font = header_font
        ws_pestel['A1'].fill = header_fill
        ws_pestel.merge_cells('A1:B1')
        
        row = 3
        pestel_categories = [
            ('political', 'العوامل السياسية'),
            ('economic', 'العوامل الاقتصادية'),
            ('social', 'العوامل الاجتماعية'),
            ('technological', 'العوامل التقنية'),
            ('environmental', 'العوامل البيئية'),
            ('legal', 'العوامل القانونية')
        ]
        
        for key, label in pestel_categories:
            if key in pestel and pestel[key]:
                ws_pestel[f'A{row}'] = label
                ws_pestel[f'A{row}'].font = subheader_font
                row += 1
                for item in pestel[key]:
                    ws_pestel[f'A{row}'] = item
                    row += 1
                row += 1
        
        ws_pestel.column_dimensions['A'].width = 60
    
    # Strategic Objectives Sheet
    if objectives:
        ws_obj = wb.create_sheet("Strategic Objectives")
        ws_obj.sheet_view.rightToLeft = True
        
        ws_obj['A1'] = "الأهداف الاستراتيجية"
        ws_obj['A1'].font = header_font
        ws_obj['A1'].fill = header_fill
        ws_obj.merge_cells('A1:C1')
        
        ws_obj['A3'] = "الهدف"
        ws_obj['B3'] = "الوصف"
        ws_obj['C3'] = "الإطار الزمني"
        for cell in ['A3', 'B3', 'C3']:
            ws_obj[cell].font = Font(bold=True)
            ws_obj[cell].fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        
        row = 4
        for obj in objectives:
            ws_obj[f'A{row}'] = obj.title
            ws_obj[f'B{row}'] = obj.description or ''
            ws_obj[f'C{row}'] = obj.timeframe or ''
            row += 1
        
        ws_obj.column_dimensions['A'].width = 25
        ws_obj.column_dimensions['B'].width = 40
        ws_obj.column_dimensions['C'].width = 20
    
    # KPIs Sheet
    if kpis:
        ws_kpi = wb.create_sheet("KPIs")
        ws_kpi.sheet_view.rightToLeft = True
        
        ws_kpi['A1'] = "مؤشرات الأداء الرئيسية"
        ws_kpi['A1'].font = header_font
        ws_kpi['A1'].fill = header_fill
        ws_kpi.merge_cells('A1:D1')
        
        ws_kpi['A3'] = "المؤشر"
        ws_kpi['B3'] = "القيمة المستهدفة"
        ws_kpi['C3'] = "الوحدة"
        ws_kpi['D3'] = "التكرار"
        for cell in ['A3', 'B3', 'C3', 'D3']:
            ws_kpi[cell].font = Font(bold=True)
            ws_kpi[cell].fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        
        row = 4
        for kpi in kpis:
            ws_kpi[f'A{row}'] = kpi.kpi_name
            ws_kpi[f'B{row}'] = kpi.target_value
            ws_kpi[f'C{row}'] = kpi.measurement_unit or ''
            ws_kpi[f'D{row}'] = kpi.frequency or ''
            row += 1
        
        ws_kpi.column_dimensions['A'].width = 30
        ws_kpi.column_dimensions['B'].width = 15
        ws_kpi.column_dimensions['C'].width = 15
        ws_kpi.column_dimensions['D'].width = 15
    
    # Initiatives Sheet
    if initiatives:
        ws_init = wb.create_sheet("Initiatives")
        ws_init.sheet_view.rightToLeft = True
        
        ws_init['A1'] = "المبادرات التنفيذية الاستراتيجية"
        ws_init['A1'].font = header_font
        ws_init['A1'].fill = header_fill
        ws_init.merge_cells('A1:E1')
        
        ws_init['A3'] = "المبادرة"
        ws_init['B3'] = "المخرجات المتوقعة"
        ws_init['C3'] = "فترة التنفيذ"
        ws_init['D3'] = "الجهة المسؤولة"
        ws_init['E3'] = "الميزانية التقديرية"
        for cell in ['A3', 'B3', 'C3', 'D3', 'E3']:
            ws_init[cell].font = Font(bold=True)
            ws_init[cell].fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        
        row = 4
        for init in initiatives:
            ws_init[f'A{row}'] = init.name
            ws_init[f'B{row}'] = init.expected_outputs or ''
            ws_init[f'C{row}'] = init.implementation_period or ''
            ws_init[f'D{row}'] = init.responsible_party or ''
            ws_init[f'E{row}'] = f"{init.budget_estimate or 0} ر.س" if init.budget_estimate else ""
            row += 1
        
        ws_init.column_dimensions['A'].width = 25
        ws_init.column_dimensions['B'].width = 40
        ws_init.column_dimensions['C'].width = 15
        ws_init.column_dimensions['D'].width = 20
        ws_init.column_dimensions['E'].width = 15
    
    # Save to buffer
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = f'attachment; filename=strategic_identity_{project_id}.xlsx'
    
    return response
