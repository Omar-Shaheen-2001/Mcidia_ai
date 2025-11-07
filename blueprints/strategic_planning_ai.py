"""
Strategic Planning & KPIs Development Module
AI-powered strategic planning with SWOT, PESTEL, Vision/Mission, Goals, and KPIs generation
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from utils.decorators import login_required
from models import StrategicPlan, StrategicKPI, StrategicInitiative, ServiceOffering, User
from utils.ai_client import llm_chat
import json
from datetime import datetime

strategic_planning_bp = Blueprint('strategic_planning_ai', __name__)

def get_db():
    """Get database instance"""
    return current_app.extensions['sqlalchemy']

def get_lang():
    """Get current language from session"""
    return session.get('language', 'ar')

# ==================== DASHBOARD ====================

@strategic_planning_bp.route('/')
@login_required
def index():
    """Strategic Planning dashboard - list all plans"""
    db = get_db()
    lang = get_lang()
    user_id = session.get('user_id')
    
    # Get all plans for current user
    plans = db.session.query(StrategicPlan).filter_by(user_id=user_id).order_by(StrategicPlan.updated_at.desc()).all()
    
    return render_template('strategic_planning/index.html', 
                         plans=plans, 
                         lang=lang)

# ==================== CREATE NEW PLAN ====================

@strategic_planning_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_plan():
    """Create new strategic plan - step 1: organization information"""
    db = get_db()
    lang = get_lang()
    user_id = session.get('user_id')
    
    if request.method == 'GET':
        # Get offering details for form configuration
        offering = db.session.query(ServiceOffering).filter_by(slug='strategic-planning-kpis').first()
        form_fields = json.loads(offering.form_fields) if offering and offering.form_fields else []
        
        return render_template('strategic_planning/create.html', 
                             form_fields=form_fields,
                             lang=lang)
    
    try:
        # Extract form data
        organization_name = request.form.get('organization_name')
        industry_sector = request.form.get('industry_sector')
        employee_count = int(request.form.get('employee_count', 0))
        planning_period = int(request.form.get('planning_period', 3))
        organization_description = request.form.get('organization_description')
        current_challenges = request.form.get('current_challenges')
        opportunities = request.form.get('opportunities')
        strategic_priorities = request.form.get('strategic_priorities', '')
        
        # Create plan record
        current_year = datetime.now().year
        plan = StrategicPlan(
            user_id=user_id,
            title=f"{organization_name} - {lang == 'ar' and 'الخطة الاستراتيجية' or 'Strategic Plan'} {current_year}-{current_year + planning_period}",
            planning_period=f"{current_year}-{current_year + planning_period}",
            start_year=current_year,
            end_year=current_year + planning_period,
            industry_sector=industry_sector,
            employee_count=employee_count,
            organization_description=organization_description,
            current_challenges=json.dumps([c.strip() for c in current_challenges.split('\n') if c.strip()]),
            opportunities=json.dumps([o.strip() for o in opportunities.split('\n') if o.strip()]),
            status='draft'
        )
        
        db.session.add(plan)
        db.session.commit()
        
        flash('تم إنشاء الخطة بنجاح / Plan created successfully' if lang == 'ar' else 'Plan created successfully', 'success')
        return redirect(url_for('strategic_planning_ai.analyze_swot', plan_id=plan.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ: {str(e)} / Error: {str(e)}' if lang == 'ar' else f'Error: {str(e)}', 'danger')
        return redirect(url_for('strategic_planning_ai.create_plan'))

# ==================== SWOT ANALYSIS (AI-POWERED) ====================

@strategic_planning_bp.route('/plan/<int:plan_id>/analyze-swot')
@login_required
def analyze_swot(plan_id):
    """Display SWOT analysis page"""
    db = get_db()
    lang = get_lang()
    user_id = session.get('user_id')
    
    plan = db.session.query(StrategicPlan).filter_by(id=plan_id, user_id=user_id).first_or_404()
    
    # Parse existing SWOT if available
    swot_data = json.loads(plan.swot_analysis) if plan.swot_analysis else None
    
    return render_template('strategic_planning/swot_analysis.html',
                         plan=plan,
                         swot_data=swot_data,
                         lang=lang)

@strategic_planning_bp.route('/plan/<int:plan_id>/generate-swot', methods=['POST'])
@login_required
def generate_swot(plan_id):
    """Generate SWOT analysis using AI"""
    db = get_db()
    lang = get_lang()
    user_id = session.get('user_id')
    
    plan = db.session.query(StrategicPlan).filter_by(id=plan_id, user_id=user_id).first_or_404()
    
    try:
        # Prepare context for AI
        challenges = json.loads(plan.current_challenges) if plan.current_challenges else []
        opportunities_list = json.loads(plan.opportunities) if plan.opportunities else []
        
        prompt = f"""قم بإجراء تحليل SWOT شامل للمؤسسة التالية:

**اسم المؤسسة:** {plan.title}
**القطاع:** {plan.industry_sector}
**عدد الموظفين:** {plan.employee_count}

**وصف المؤسسة:**
{plan.organization_description}

**التحديات الحالية:**
{chr(10).join(f'- {c}' for c in challenges)}

**الفرص المتاحة:**
{chr(10).join(f'- {o}' for o in opportunities_list)}

يرجى تقديم تحليل SWOT تفصيلي يشمل:
1. نقاط القوة (Strengths): 5-7 نقاط على الأقل
2. نقاط الضعف (Weaknesses): 5-7 نقاط على الأقل
3. الفرص (Opportunities): 5-7 نقاط على الأقل
4. التهديدات (Threats): 5-7 نقاط على الأقل

الرد بصيغة JSON:
{{
  "strengths": ["نقطة قوة 1", "نقطة قوة 2", ...],
  "weaknesses": ["نقطة ضعف 1", "نقطة ضعف 2", ...],
  "opportunities": ["فرصة 1", "فرصة 2", ...],
  "threats": ["تهديد 1", "تهديد 2", ...]
}}"""
        
        # Call AI
        response = llm_chat(
            prompt=prompt,
            model='gpt-4',
            response_format='json'
        )
        
        swot_data = json.loads(response['content'])
        
        # Save to database
        plan.swot_analysis = json.dumps(swot_data, ensure_ascii=False)
        plan.ai_tokens_used += response.get('tokens_used', 0)
        db.session.commit()
        
        return jsonify({'success': True, 'data': swot_data})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== PESTEL ANALYSIS (AI-POWERED) ====================

@strategic_planning_bp.route('/plan/<int:plan_id>/analyze-pestel')
@login_required
def analyze_pestel(plan_id):
    """Display PESTEL analysis page"""
    db = get_db()
    lang = get_lang()
    user_id = session.get('user_id')
    
    plan = db.session.query(StrategicPlan).filter_by(id=plan_id, user_id=user_id).first_or_404()
    
    # Parse existing PESTEL if available
    pestel_data = json.loads(plan.pestel_analysis) if plan.pestel_analysis else None
    
    return render_template('strategic_planning/pestel_analysis.html',
                         plan=plan,
                         pestel_data=pestel_data,
                         lang=lang)

@strategic_planning_bp.route('/plan/<int:plan_id>/generate-pestel', methods=['POST'])
@login_required
def generate_pestel(plan_id):
    """Generate PESTEL analysis using AI"""
    db = get_db()
    lang = get_lang()
    user_id = session.get('user_id')
    
    plan = db.session.query(StrategicPlan).filter_by(id=plan_id, user_id=user_id).first_or_404()
    
    try:
        prompt = f"""قم بإجراء تحليل PESTEL شامل للمؤسسة التالية:

**اسم المؤسسة:** {plan.title}
**القطاع:** {plan.industry_sector}
**وصف المؤسسة:** {plan.organization_description}

يرجى تحليل العوامل الخارجية المؤثرة على المؤسسة:
1. السياسية (Political): 3-5 عوامل
2. الاقتصادية (Economic): 3-5 عوامل
3. الاجتماعية (Social): 3-5 عوامل
4. التقنية (Technological): 3-5 عوامل
5. البيئية (Environmental): 3-5 عوامل
6. القانونية (Legal): 3-5 عوامل

الرد بصيغة JSON:
{{
  "political": ["عامل سياسي 1", ...],
  "economic": ["عامل اقتصادي 1", ...],
  "social": ["عامل اجتماعي 1", ...],
  "technological": ["عامل تقني 1", ...],
  "environmental": ["عامل بيئي 1", ...],
  "legal": ["عامل قانوني 1", ...]
}}"""
        
        # Call AI
        response = llm_chat(
            prompt=prompt,
            model='gpt-4',
            response_format='json'
        )
        
        pestel_data = json.loads(response['content'])
        
        # Save to database
        plan.pestel_analysis = json.dumps(pestel_data, ensure_ascii=False)
        plan.ai_tokens_used += response.get('tokens_used', 0)
        db.session.commit()
        
        return jsonify({'success': True, 'data': pestel_data})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== STRATEGIC FRAMEWORK GENERATION ====================

@strategic_planning_bp.route('/plan/<int:plan_id>/generate-framework')
@login_required
def generate_framework(plan_id):
    """Generate Vision, Mission, Values, and Goals using AI"""
    db = get_db()
    lang = get_lang()
    user_id = session.get('user_id')
    
    plan = db.session.query(StrategicPlan).filter_by(id=plan_id, user_id=user_id).first_or_404()
    
    return render_template('strategic_planning/framework.html',
                         plan=plan,
                         lang=lang)

@strategic_planning_bp.route('/plan/<int:plan_id>/ai-generate-framework', methods=['POST'])
@login_required
def ai_generate_framework(plan_id):
    """AI generates vision, mission, values, and strategic goals"""
    db = get_db()
    user_id = session.get('user_id')
    
    plan = db.session.query(StrategicPlan).filter_by(id=plan_id, user_id=user_id).first_or_404()
    
    try:
        # Get SWOT data
        swot = json.loads(plan.swot_analysis) if plan.swot_analysis else {}
        
        prompt = f"""بناءً على التحليل الاستراتيجي للمؤسسة التالية، قم بتوليد:

**اسم المؤسسة:** {plan.title}
**القطاع:** {plan.industry_sector}
**الوصف:** {plan.organization_description}

**نقاط القوة الرئيسية:**
{chr(10).join(f'- {s}' for s in swot.get('strengths', [])[:3])}

**الفرص الرئيسية:**
{chr(10).join(f'- {o}' for o in swot.get('opportunities', [])[:3])}

يرجى توليد:
1. **الرؤية (Vision)**: بيان ملهم عن مستقبل المؤسسة (جملة واحدة قوية)
2. **الرسالة (Mission)**: الهدف الأساسي للمؤسسة (فقرة قصيرة)
3. **القيم الجوهرية (Core Values)**: 5-7 قيم أساسية مع شرح موجز لكل قيمة
4. **الأهداف الاستراتيجية (Strategic Goals)**: 4-6 أهداف SMART تغطي المجالات الرئيسية

الرد بصيغة JSON:
{{
  "vision": "بيان الرؤية",
  "mission": "بيان الرسالة",
  "values": [
    {{"name": "القيمة 1", "description": "شرح القيمة"}},
    ...
  ],
  "strategic_goals": [
    {{
      "goal": "الهدف الاستراتيجي",
      "description": "وصف تفصيلي",
      "focus_area": "المجال (مثل: مالي، عملاء، عمليات، تعلم)",
      "timeframe": "الإطار الزمني"
    }},
    ...
  ]
}}"""
        
        # Call AI
        response = llm_chat(
            prompt=prompt,
            model='gpt-4',
            response_format='json'
        )
        
        framework_data = json.loads(response['content'])
        
        # Save to database
        plan.vision_statement = framework_data.get('vision')
        plan.mission_statement = framework_data.get('mission')
        plan.core_values = json.dumps(framework_data.get('values', []), ensure_ascii=False)
        plan.strategic_goals = json.dumps(framework_data.get('strategic_goals', []), ensure_ascii=False)
        plan.ai_tokens_used += response.get('tokens_used', 0)
        db.session.commit()
        
        return jsonify({'success': True, 'data': framework_data})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== KPIs GENERATION ====================

@strategic_planning_bp.route('/plan/<int:plan_id>/kpis')
@login_required
def manage_kpis(plan_id):
    """Manage KPIs for the strategic plan"""
    db = get_db()
    lang = get_lang()
    user_id = session.get('user_id')
    
    plan = db.session.query(StrategicPlan).filter_by(id=plan_id, user_id=user_id).first_or_404()
    kpis = db.session.query(StrategicKPI).filter_by(plan_id=plan_id).all()
    
    return render_template('strategic_planning/kpis.html',
                         plan=plan,
                         kpis=kpis,
                         lang=lang)

@strategic_planning_bp.route('/plan/<int:plan_id>/generate-kpis', methods=['POST'])
@login_required
def generate_kpis(plan_id):
    """AI generates SMART KPIs for each strategic goal"""
    db = get_db()
    user_id = session.get('user_id')
    
    plan = db.session.query(StrategicPlan).filter_by(id=plan_id, user_id=user_id).first_or_404()
    
    try:
        strategic_goals = json.loads(plan.strategic_goals) if plan.strategic_goals else []
        
        prompt = f"""قم بتوليد مؤشرات أداء رئيسية (KPIs) قابلة للقياس لكل هدف استراتيجي:

**المؤسسة:** {plan.title}
**القطاع:** {plan.industry_sector}

**الأهداف الاستراتيجية:**
{chr(10).join(f'{i+1}. {g.get("goal")} ({g.get("focus_area")})' for i, g in enumerate(strategic_goals))}

لكل هدف، قم بتوليد 2-3 مؤشرات أداء SMART تشمل:
- اسم المؤشر
- وصف موجز
- الفئة (مالي، عملاء، عمليات داخلية، تعلم ونمو)
- وحدة القياس (%, عدد، مبلغ مالي، الخ)
- القيمة الأساسية (الحالية)
- القيمة المستهدفة
- دورية القياس (شهري، ربع سنوي، سنوي)
- الجهة المسؤولة

الرد بصيغة JSON:
{{
  "kpis": [
    {{
      "name": "اسم المؤشر",
      "description": "الوصف",
      "category": "الفئة",
      "measurement_unit": "الوحدة",
      "baseline_value": 0,
      "target_value": 100,
      "measurement_frequency": "شهري/ربع سنوي/سنوي",
      "responsible_party": "الإدارة المسؤولة",
      "data_source": "مصدر البيانات"
    }},
    ...
  ]
}}"""
        
        # Call AI
        response = llm_chat(
            prompt=prompt,
            model='gpt-4',
            response_format='json'
        )
        
        kpis_data = json.loads(response['content'])
        
        # Create KPI records
        for kpi_data in kpis_data.get('kpis', []):
            kpi = StrategicKPI(
                plan_id=plan.id,
                name=kpi_data.get('name'),
                description=kpi_data.get('description'),
                category=kpi_data.get('category'),
                measurement_unit=kpi_data.get('measurement_unit'),
                baseline_value=kpi_data.get('baseline_value', 0),
                target_value=kpi_data.get('target_value', 0),
                current_value=kpi_data.get('baseline_value', 0),
                measurement_frequency=kpi_data.get('measurement_frequency'),
                responsible_party=kpi_data.get('responsible_party'),
                data_source=kpi_data.get('data_source', ''),
                status='active'
            )
            db.session.add(kpi)
        
        plan.ai_tokens_used += response.get('tokens_used', 0)
        db.session.commit()
        
        return jsonify({'success': True, 'kpis_count': len(kpis_data.get('kpis', []))})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== PLAN DASHBOARD ====================

@strategic_planning_bp.route('/plan/<int:plan_id>/dashboard')
@login_required
def plan_dashboard(plan_id):
    """Complete strategic plan dashboard with all components"""
    db = get_db()
    lang = get_lang()
    user_id = session.get('user_id')
    
    plan = db.session.query(StrategicPlan).filter_by(id=plan_id, user_id=user_id).first_or_404()
    kpis = db.session.query(StrategicKPI).filter_by(plan_id=plan_id).all()
    initiatives = db.session.query(StrategicInitiative).filter_by(plan_id=plan_id).all()
    
    # Parse JSON fields
    swot = json.loads(plan.swot_analysis) if plan.swot_analysis else {}
    pestel = json.loads(plan.pestel_analysis) if plan.pestel_analysis else {}
    values = json.loads(plan.core_values) if plan.core_values else []
    goals = json.loads(plan.strategic_goals) if plan.strategic_goals else []
    
    return render_template('strategic_planning/dashboard.html',
                         plan=plan,
                         swot=swot,
                         pestel=pestel,
                         values=values,
                         goals=goals,
                         kpis=kpis,
                         initiatives=initiatives,
                         lang=lang)

# ==================== EXPORT & REPORTS ====================

@strategic_planning_bp.route('/plan/<int:plan_id>/export-pdf')
@login_required
def export_pdf(plan_id):
    """Export strategic plan as PDF report"""
    # TODO: Implement PDF generation using ReportLab or WeasyPrint
    flash('قريباً: تصدير PDF / Coming soon: PDF export', 'info')
    return redirect(url_for('strategic_planning_ai.plan_dashboard', plan_id=plan_id))
