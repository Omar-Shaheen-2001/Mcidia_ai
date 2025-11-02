from flask import Blueprint, render_template, request, flash, session
from flask_jwt_extended import get_jwt_identity
from utils.decorators import login_required
from models import User, Project, AILog
from app import db
from utils.ai_client import llm_chat
import json

finance_bp = Blueprint('finance', __name__)

@finance_bp.route('/')
@login_required
def index():
    user_id = get_jwt_identity()
    projects = db.session.query(Project).filter_by(user_id=user_id, module='finance').all()
    lang = session.get('language', 'ar')
    return render_template('finance/index.html', projects=projects, lang=lang)

@finance_bp.route('/feasibility', methods=['GET', 'POST'])
@login_required
def feasibility():
    user_id = get_jwt_identity()
    user = db.session.query(User).get(user_id)
    lang = session.get('language', 'ar')
    
    if request.method == 'POST':
        project_name = request.form.get('project_name')
        investment = request.form.get('investment')
        revenue_model = request.form.get('revenue_model')
        costs = request.form.get('costs')
        
        if lang == 'ar':
            system_prompt = "أنت مستشار مالي متخصص في دراسات الجدوى الاقتصادية."
            user_message = f"""
            اسم المشروع: {project_name}
            الاستثمار المطلوب: {investment}
            نموذج الإيرادات: {revenue_model}
            التكاليف المتوقعة: {costs}
            
            قم بإعداد دراسة جدوى شاملة تتضمن:
            1. تحليل السوق والطلب
            2. التكاليف التأسيسية والتشغيلية
            3. توقعات الإيرادات (3 سنوات)
            4. تحليل الربحية والعائد على الاستثمار (ROI)
            5. نقطة التعادل (Break-even Point)
            6. التوصيات والمخاطر
            """
        else:
            system_prompt = "You are a financial consultant specialized in economic feasibility studies."
            user_message = f"""
            Project Name: {project_name}
            Required Investment: {investment}
            Revenue Model: {revenue_model}
            Expected Costs: {costs}
            
            Prepare a comprehensive feasibility study including:
            1. Market and Demand Analysis
            2. Capital and Operating Costs
            3. Revenue Projections (3 years)
            4. Profitability and ROI Analysis
            5. Break-even Point
            6. Recommendations and Risks
            """
        
        ai_response = llm_chat(system_prompt, user_message)
        
        project = Project(
            user_id=user_id,
            title=f"Feasibility Study - {project_name}",
            module='finance',
            content=json.dumps({
                'project_name': project_name,
                'investment': investment,
                'analysis': ai_response
            }),
            status='completed'
        )
        db.session.add(project)
        
        ai_log = AILog(
            user_id=user_id,
            module='finance',
            prompt=user_message[:500],
            response=ai_response[:500],
            tokens_used=int(len(ai_response.split()) * 1.3)
        )
        db.session.add(ai_log)
        user.ai_credits_used += int(len(ai_response.split()) * 1.3)
        db.session.commit()
        
        flash('تم إنشاء دراسة الجدوى بنجاح! / Feasibility Study generated successfully!', 'success')
        return render_template('finance/feasibility_result.html', analysis=ai_response, project=project, lang=lang)
    
    return render_template('finance/feasibility.html', lang=lang)

@finance_bp.route('/pricing', methods=['GET', 'POST'])
@login_required
def pricing():
    user_id = get_jwt_identity()
    user = db.session.query(User).get(user_id)
    lang = session.get('language', 'ar')
    
    if request.method == 'POST':
        product_name = request.form.get('product_name')
        costs = request.form.get('costs')
        market = request.form.get('market')
        competitors = request.form.get('competitors')
        
        if lang == 'ar':
            system_prompt = "أنت خبير في استراتيجيات التسعير وتحليل التكاليف."
            user_message = f"""
            المنتج/الخدمة: {product_name}
            التكاليف: {costs}
            السوق المستهدف: {market}
            المنافسون: {competitors}
            
            قم بتطوير استراتيجية تسعير تتضمن:
            1. تحليل التكلفة الكاملة
            2. السعر المقترح بناءً على 3 استراتيجيات مختلفة
            3. هامش الربح المتوقع
            4. التحليل المقارن مع المنافسين
            5. توصيات التسعير النفسي
            """
        else:
            system_prompt = "You are an expert in pricing strategies and cost analysis."
            user_message = f"""
            Product/Service: {product_name}
            Costs: {costs}
            Target Market: {market}
            Competitors: {competitors}
            
            Develop a pricing strategy including:
            1. Full Cost Analysis
            2. Proposed Price based on 3 different strategies
            3. Expected Profit Margin
            4. Competitive Analysis
            5. Psychological Pricing Recommendations
            """
        
        ai_response = llm_chat(system_prompt, user_message)
        
        project = Project(
            user_id=user_id,
            title=f"Pricing Strategy - {product_name}",
            module='finance',
            content=json.dumps({
                'product_name': product_name,
                'pricing': ai_response
            }),
            status='completed'
        )
        db.session.add(project)
        
        ai_log = AILog(
            user_id=user_id,
            module='finance',
            prompt=user_message[:500],
            response=ai_response[:500],
            tokens_used=int(len(ai_response.split()) * 1.3)
        )
        db.session.add(ai_log)
        user.ai_credits_used += int(len(ai_response.split()) * 1.3)
        db.session.commit()
        
        flash('تم إنشاء استراتيجية التسعير بنجاح! / Pricing Strategy generated successfully!', 'success')
        return render_template('finance/pricing_result.html', pricing=ai_response, project=project, lang=lang)
    
    return render_template('finance/pricing.html', lang=lang)
