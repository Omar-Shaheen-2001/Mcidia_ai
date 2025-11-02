from flask import Blueprint, render_template, request, flash, session
from flask_jwt_extended import get_jwt_identity
from utils.decorators import login_required
from models import User, Project, AILog
from app import db
from utils.ai_client import llm_chat
import json

marketing_bp = Blueprint('marketing', __name__)

@marketing_bp.route('/')
@login_required
def index():
    user_id = get_jwt_identity()
    projects = db.session.query(Project).filter_by(user_id=user_id, module='marketing').all()
    lang = session.get('language', 'ar')
    return render_template('marketing/index.html', projects=projects, lang=lang)

@marketing_bp.route('/plan', methods=['GET', 'POST'])
@login_required
def marketing_plan():
    user_id = get_jwt_identity()
    user = db.session.query(User).get(user_id)
    lang = session.get('language', 'ar')
    
    if request.method == 'POST':
        company_name = request.form.get('company_name')
        product = request.form.get('product')
        target_audience = request.form.get('target_audience')
        budget = request.form.get('budget')
        goals = request.form.get('goals')
        
        if lang == 'ar':
            system_prompt = "أنت خبير تسويق استراتيجي متخصص في إعداد الخطط التسويقية."
            user_message = f"""
            الشركة: {company_name}
            المنتج/الخدمة: {product}
            الجمهور المستهدف: {target_audience}
            الميزانية: {budget}
            الأهداف: {goals}
            
            قم بإعداد خطة تسويقية شاملة تتضمن:
            1. تحليل السوق والجمهور المستهدف
            2. تحليل المنافسين (Competitive Analysis)
            3. استراتيجية المحتوى
            4. القنوات التسويقية المقترحة (رقمية وتقليدية)
            5. جدول زمني للحملات (6 أشهر)
            6. مؤشرات الأداء الرئيسية (KPIs)
            7. توزيع الميزانية
            8. توقعات العائد على الاستثمار (ROI)
            """
        else:
            system_prompt = "You are a strategic marketing expert specialized in creating marketing plans."
            user_message = f"""
            Company: {company_name}
            Product/Service: {product}
            Target Audience: {target_audience}
            Budget: {budget}
            Goals: {goals}
            
            Create a comprehensive marketing plan including:
            1. Market and Target Audience Analysis
            2. Competitive Analysis
            3. Content Strategy
            4. Recommended Marketing Channels (digital and traditional)
            5. Campaign Timeline (6 months)
            6. Key Performance Indicators (KPIs)
            7. Budget Allocation
            8. Expected ROI
            """
        
        ai_response = llm_chat(system_prompt, user_message)
        
        project = Project(
            user_id=user_id,
            title=f"Marketing Plan - {company_name}",
            module='marketing',
            content=json.dumps({
                'company_name': company_name,
                'product': product,
                'plan': ai_response
            }),
            status='completed'
        )
        db.session.add(project)
        
        ai_log = AILog(
            user_id=user_id,
            module='marketing',
            prompt=user_message[:500],
            response=ai_response[:500],
            tokens_used=int(len(ai_response.split()) * 1.3)
        )
        db.session.add(ai_log)
        user.ai_credits_used += int(len(ai_response.split()) * 1.3)
        db.session.commit()
        
        flash('تم إنشاء الخطة التسويقية بنجاح! / Marketing Plan generated successfully!', 'success')
        return render_template('marketing/plan_result.html', plan=ai_response, project=project, lang=lang)
    
    return render_template('marketing/plan.html', lang=lang)

@marketing_bp.route('/competitor-analysis', methods=['GET', 'POST'])
@login_required
def competitor_analysis():
    user_id = get_jwt_identity()
    user = db.session.query(User).get(user_id)
    lang = session.get('language', 'ar')
    
    if request.method == 'POST':
        industry = request.form.get('industry')
        competitors = request.form.get('competitors')
        market = request.form.get('market')
        
        if lang == 'ar':
            system_prompt = "أنت محلل تسويقي متخصص في تحليل المنافسين."
            user_message = f"""
            القطاع: {industry}
            المنافسون الرئيسيون: {competitors}
            السوق: {market}
            
            قم بتحليل شامل للمنافسين يتضمن:
            1. نقاط القوة والضعف لكل منافس
            2. استراتيجيات التسعير
            3. القنوات التسويقية المستخدمة
            4. حصتهم في السوق
            5. ميزاتهم التنافسية
            6. فرص التميز
            7. التوصيات الاستراتيجية
            """
        else:
            system_prompt = "You are a marketing analyst specialized in competitor analysis."
            user_message = f"""
            Industry: {industry}
            Main Competitors: {competitors}
            Market: {market}
            
            Provide comprehensive competitor analysis including:
            1. Strengths and Weaknesses of each competitor
            2. Pricing Strategies
            3. Marketing Channels Used
            4. Market Share
            5. Competitive Advantages
            6. Differentiation Opportunities
            7. Strategic Recommendations
            """
        
        ai_response = llm_chat(system_prompt, user_message)
        
        project = Project(
            user_id=user_id,
            title=f"Competitor Analysis - {industry}",
            module='marketing',
            content=json.dumps({
                'industry': industry,
                'analysis': ai_response
            }),
            status='completed'
        )
        db.session.add(project)
        
        ai_log = AILog(
            user_id=user_id,
            module='marketing',
            prompt=user_message[:500],
            response=ai_response[:500],
            tokens_used=int(len(ai_response.split()) * 1.3)
        )
        db.session.add(ai_log)
        user.ai_credits_used += int(len(ai_response.split()) * 1.3)
        db.session.commit()
        
        flash('تم إنشاء تحليل المنافسين بنجاح! / Competitor Analysis generated successfully!', 'success')
        return render_template('marketing/competitor_result.html', analysis=ai_response, project=project, lang=lang)
    
    return render_template('marketing/competitor_analysis.html', lang=lang)
